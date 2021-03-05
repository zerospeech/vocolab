#!/bin/bash
# list of aliases to debug zerospeech server


alias run_server="uvicorn zerospeech.api:app --reload --debug"
alias zr="python -m zerospeech.admin"

# todo: add ZR_ENV_FILE here?
