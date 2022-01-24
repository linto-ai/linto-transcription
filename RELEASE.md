# 1.0.3
 - Added: Subtitling return format for VTT and SRT 
 - Added: Accept headers for subtitle formats
 - Added: jobid in result database
 - Added: fetch result in db using jobid
 - Changed: segment in TranscriptionResult will be equals to raw_segment in absence of postprocessing
 - Moved: transcription related file to workers/utils
 - Updated: README
 - Removed: no longer used formating.py file
 - Removed: SubtitleConfig in TranscriptionConfig

# 1.0.2
 - Added force_sync param for forced synchronous call
 - Added vad processing to split large files into subfiles
 - Added password variable for the service broker
 - Changed API to the TranscriptionConfig format.
 - Changed results return format
 - Updated test_transcription.py
 - Fixed wavefile not being converted when samplerate was wrong
 - Removed flower
 - Updated swagger to OpenAPI 3.0 and added new specifications.git

# 1.0.1
 - Added wait-for-it for service dependencies
 - Added LICENSE
 - Added README
 - Added swagger
 - Fixed post-processing failing with speaker diarization
 - Fixed transcription task initial state not returning proper format
 - Removed unecessary ENV variables
 - Moved test/ to repository root
 
# 1.0.0
 - Initial version
 - Allow client to perform asynchronous transcription request
 - Results are stored in a database