FROM python:3.8-alpine as base
LABEL maintainer="Nicolas Hamilakis <nicolas.hamilakis@ens.fr>"
LABEL copyright="GPL3, CoML Team, ENS, INRIA, EHESS"

RUN pip install --no-cache-dir --upgrade pip


# Base to install python dependencies
FROM base as install
COPY requirements.txt /app
COPY requirements-dev.txt /app
# install dependencies
RUN pip install --no-cache-dir -r /app/requirements-dev.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# FOLDERS
RUN mkdir -p data/submissions

FROM install
# Project files
COPY zerospeech/ /app/
COPY setup.py /app/
COPY README.md /app/
COPY pyproject.toml /app/
COPY data/templates /templates

# install project
RUN pip install /app

# todo fix entrypoint & CMD
# ENTRYPOINT
# CMD [ celery something .... ]