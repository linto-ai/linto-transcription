curl -X POST "http://localhost:8000/transcribe" -H "accept: application/json"\
 -H "Content-Type: multipart/form-data" \
 -F 'format=raw' \
 -F "file=@bonjour.wav;type=audio/wav"