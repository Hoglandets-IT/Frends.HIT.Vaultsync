FROM python:3.9.1-slim-buster

ADD . /app

RUN pip3 install -r /app/requirements.txt

ENTRYPOINT ["python3", "/app/synk.py"]