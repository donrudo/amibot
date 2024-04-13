FROM python:3

LABEL authors="carlosm"

COPY ./LICENSE /nonexistent/
COPY ./setup.* ./requirements.txt ./README.md ./pyproject.toml /nonexistent/
COPY amibot /nonexistent/amibot
COPY scripts /nonexistent/scripts

RUN mkdir /nonexistent/configs; chown nobody -R /nonexistent

USER nobody
WORKDIR /nonexistent

RUN python3 -m pip install build; pip install -r ./requirements.txt

ENTRYPOINT ["scripts/start.sh"]
