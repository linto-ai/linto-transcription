#!/bin/bash
set -e
echo "RUNNING : Transcription request service"

supervisord -c supervisor/supervisor.conf
supervisorctl -c supervisor/supervisor.conf tail -f ingress stderr
