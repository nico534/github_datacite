FROM python:3.13

WORKDIR /application

ADD . .
RUN pip install -r requirements.txt
CMD [ "python",  "rest_api.py"]