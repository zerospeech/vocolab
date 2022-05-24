#!/bin/bash
set -o errexit

APPDATA=${VC_DATA_FOLDER:-"/app-data"}
ROOT_APPDATA="/var/app-data"

echo "Initializing Environment..."

if [ ! -f "${APPDATA}/.init" ]; then
  echo "APPDATA FOLDER NOT INITIALIZED..."
  echo "Setting up..."
  mkdir -p "${APPDATA}/leaderboards"
  mkdir -p "${APPDATA}/submissions"
  mkdir -p "${APPDATA}/user_data"

  # copy leaderboard archives
  if [ -d "${ROOT_APPDATA}/archive" ]; then
    cp -r  "${ROOT_APPDATA}/archive" "${APPDATA}/archive"
  else
      # or create the empty dir
      mkdir -p "${APPDATA}/archive"
  fi

  # copy static files
  if [ -d "${ROOT_APPDATA}/_static" ]; then
    cp -r "${ROOT_APPDATA}/_static" "${APPDATA}/_static"
  else
      # or create the empty dir
      mkdir -p "${APPDATA}/_static"
  fi

  # copy evaluators files
  if [ -d "${ROOT_APPDATA}/evaluators" ]; then
    cp -r "${ROOT_APPDATA}/evaluators" "${APPDATA}/evaluators"
  else
      # or create the empty dir
      mkdir -p "${APPDATA}/evaluators"
  fi

  # clean file duplicates
  rm -rf "${ROOT_APPDATA}"

  # add a lockfile to prevent re-running this
  touch "${APPDATA}/.init"
fi

if [ $# -eq 0 ]; then
  echo "no command given; sleeping"
  while true; do sleep 10000; done
else
  echo ">>> $@"
  exec "$@"
fi
