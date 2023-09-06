FROM python:3.10-alpine3.18

RUN pip install requests
WORKDIR /app
COPY notifier.py template.html /app/

# TODO Dev purporse
COPY conf.ini /app/conf.ini

ENTRYPOINT ["python3", "/app/notifier.py"]
