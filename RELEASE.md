# 1.2.0
 - Added timestamp interpolation for non-consecutive diarization segments.
 - Added Makefile for styling
 - Refactored code to PEP8 (black)
 - Reorganized repository folder structure.
 - Added service discovery for subtasks
 - Added service resolve and service resolve policy
 - Added task logs and log query route
 
# 1.1.2h1
 - Fixed convertnumber converting spk id 1
 - Fixed usersub not applied to subtitles
 - Fixed text cleaning and substitutions not applied to chunks of subtitle.

# 1.1.2
 - Added raw_return and convert_number to VTT and SRT format
 - Removed accept header check on /job/ route
 - Cleanup

# 1.1.1
 - Added: Text normalisation.
 - Added: Text to Number. 
 - Added: Result presentation options as query string.
 - Added: MongoDB error handler. 
 - Changed: Steps progression.
 - Updated: README
 - Updated: API specs.
 - Updated: transcription_request test script.

# 1.1.0
 - Added: A new route has been added /results/{result_id} allows to fetch transcription result and to specify the result format.
 - Changed: MongoDB server availibility timeout check greatly reduced to prevent hanging when mongo is unavailable.
 - Changed: The /job/{job_id} route now returns a ressource_id to be fetch on the /results/{result_id} when the task is completed.
 - Changed: Diarization is ignored when number of speaker is 1
 - Changed: GUNICORN_WORKER replaced with CONCURRENCY.
 - Fixed: Transcription worker concurrency is now set using CONCURRENCY env variable.
 - Updated: README.
 - Updated: Swagger's document.
 - Removed: no_cache request option has been removed.

# 1.0.3
 - Added: Subtitling return format for VTT and SRT 
 - Added: Accept headers for subtitle formats
 - Added: jobid in result database
 - Changed: segment in TranscriptionResult will be equals to raw_segment in absence of postprocessing
 - Added: fetch result in db using jobid
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