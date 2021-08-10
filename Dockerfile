FROM python:3
LABEL maintainer="rbaraglia@linagora.com"

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY transcriptionservice /usr/src/app/transcriptionservice
COPY docker-entrypoint.sh ./
COPY supervisor /usr/src/app/supervisor
RUN mkdir -p /var/log/supervisor/

ENV PYTHONPATH="${PYTHONPATH}:/usr/src/app/transcriptionservice"

HEALTHCHECK CMD curl localhost:8000/healthcheck

EXPOSE 8000
EXPOSE 5555

ENTRYPOINT ["./docker-entrypoint.sh"]

