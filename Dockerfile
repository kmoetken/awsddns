FROM python:3.7-alpine

ADD requirements.txt /

WORKDIR /

RUN pip install -r requirements.txt

ADD awsddns.py /

CMD [ "python", "awsddns.py"]
