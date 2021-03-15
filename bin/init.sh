#!/bin/bash
# source this file to work on the API
conda activate zapi
export ZR_ENV_FILE=test.env
alias run_server="uvicorn zerospeech.api:app --reload --debug"
alias zr="python -m zerospeech.admin"
