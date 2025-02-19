# GitHub action Dockerfile
FROM python:3-slim AS builder

ADD ./github_cite /github_cite

WORKDIR /github_cite

RUN pip install --target=/github_cite -r requirements-minimal.txt

FROM gcr.io/distroless/python3-debian10
COPY --from=builder /github_cite /github_cite
WORKDIR /github_cite
ENV PYTHONPATH=/github_cite

CMD [ "/github_cite/action.py" ]
