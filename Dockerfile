FROM python:3.10-slim

ADD requirements.txt /
RUN pip install -r /requirements.txt

ADD . /src/
WORKDIR /src/
ENTRYPOINT ["python", "train.py"]
