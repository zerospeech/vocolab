FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8 as base
LABEL maintainer="Nicolas Hamilakis <nicolas.hamilakis@ens.fr>"
LABEL copyright="GPL3, CoML Team, ENS, INRIA, EHESS"

RUN pip install --no-cache-dir --upgrade pip


# Base to install python dependencies
FROM base as install
COPY requirements.txt /src
COPY requirements-dev.txt /src
# install dependencies
RUN pip install --no-cache-dir -r /src/requirements-dev.txt
RUN pip install --no-cache-dir -r /src/requirements.txt

FROM install as vocolab
# Project files
COPY vocolab /src/vocolab
COPY setup.py /src/
COPY setup.cfg /src/
COPY MANIFEST.cfg /src/
COPY README.md /src
COPY docs /docs/

# Install vocolab
WORKDIR /src
RUN pip install .

# Setup env
COPY containers/app-data /var/app-data/
COPY containers/dockerconfig /etc/vocolab/
RUN bash /etc/vocolab/env-setup.sh "api"

# Executing
FROM vocolab
EXPOSE 8000
CMD ["gunicorn"  , "-b", "0.0.0.0:8000", "app:app"]