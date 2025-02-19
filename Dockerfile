# GitHub action Dockerfile
FROM python:3.13

ADD ./github_cite /github_cite

WORKDIR /github_cite

RUN pip install --target=/github_cite -r requirements-minimal.txt

CMD [ "python3", "action.py" ]
