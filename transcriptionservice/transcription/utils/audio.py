import os
import subprocess
from typing import List, Tuple

import numpy as np
import wavio
import webrtcvad

__all__ = ["transcoding", "splitFile"]


def transcoding(
    input_file_path: str,
    output_sr: int = 16000,
    output_channels: int = 1,
    cleanup: bool = True,
) -> str:
    """Transcode the input file into 16b PCM Mono Wave file at given sample rate"""
    # Check File
    if not os.path.isfile(input_file_path):
        raise FileNotFoundError("Ressource not found: {input_file_path}")

    # Output name
    folder = os.path.dirname(input_file_path)
    basename = os.path.basename(input_file_path).split(".")[0]
    if input_file_path.endswith(".wav"):
        basename = f"_{basename}.wav"
    else:
        basename = f"{basename}.wav"
    output_file_path = os.path.join(folder, basename)

    # Subprocess
    command = f"ffmpeg -i {input_file_path} -y -acodec pcm_s16le"
    if output_channels is not None:
        command += f" -ac {output_channels}"
    command += f" -ar {output_sr} {output_file_path}"

    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()

    if not os.path.isfile(output_file_path):
        raise Exception("Failed transcoding")

    # Cleanup
    if cleanup:
        os.remove(input_file_path)

    return output_file_path


def vadCutIndexes(
    audio,
    sample_rate,
    chunk_length: float = 0.03,
    mode: int = 1,
    min_silence_frame: int = 10,
):
    """Apply VAD on the signal and returns cut indexes located between speech segments"""
    vad = webrtcvad.Vad()
    vad.set_mode(mode)
    chunk_size = int(sample_rate * chunk_length)
    vad_res = []

    # Split in chunk size and process VAD
    for start in range(0, len(audio) - chunk_size, chunk_size):
        buffer = (audio[start : start + chunk_size]).astype(np.int16).tobytes()
        vad_res.append(vad.is_speech(buffer, sample_rate))

    # Determines cut indexes in the middle of silence windows
    # Ignore silence windows which length are < min_silence_frame
    is_speech = vad_res[0]
    sil_start_i = 0
    cut_indexes = []
    for i, v in enumerate(vad_res):
        if v:
            if not is_speech:
                sil_stop_i = i
                if sil_stop_i - sil_start_i > min_silence_frame:
                    cut_indexes.append(int(np.mean([sil_start_i, sil_stop_i])))
                is_speech = True
        else:
            if is_speech:
                is_speech = False
                sil_start_i = i

    # Returns cut_indexes as list
    return (np.array(cut_indexes) * chunk_size).astype(np.int).tolist()


def splitFile(file_path, min_length: int = 10) -> Tuple[List[Tuple[str, float, float]], float]:
    """Split a file into multiple subfiles using vad"""
    content = wavio.read(file_path)
    sr = content.rate
    audio = np.squeeze(content.data)

    # Do not split file under min_length
    if len(audio) / sr < min_length:
        return [(file_path, 0.0, len(audio))], len(audio)

    # Get cut indexex based on vad
    cut_indexes = vadCutIndexes(audio, sr)

    # If no cut detected
    if len(cut_indexes) == 0:
        return [(file_path, 0.0, len(audio))], len(audio)
    basename = ".".join(file_path.split(".")[:-1])

    # Create subfiles
    subfiles = []
    i = 0
    for start, stop in zip([0] + cut_indexes, cut_indexes + [len(audio)]):
        subfile_path = f"{basename}_{i}.wav"
        offset = start / sr
        wavio.write(subfile_path, audio[start:stop], sr)
        subfiles.append((subfile_path, offset, stop - start))
        i += 1
    return subfiles, len(audio)
