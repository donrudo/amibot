FROM python:3-slim 

MAINTAINER "carlosm"

COPY ./LICENSE ./setup.* ./requirements.txt ./README.md ./pyproject.toml /nonexistent/
COPY ./scripts /nonexistent/scripts
COPY ./amibot /nonexistent/amibot

RUN apt update && \
    apt upgrade -y && \
    mkdir /nonexistent/configs && \
    chown nobody -R /nonexistent && \
    chmod +750 /nonexistent/scripts && \
    cd /nonexistent/ && \
    ./scripts/build.sh

USER nobody
WORKDIR /nonexistent
ENTRYPOINT ["scripts/start.sh"]
