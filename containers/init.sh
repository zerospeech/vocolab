#!/bin/bash

APPDATA=${VC_DATA_FOLDER:-"/app-data"}
ROOT_APPDATA="/var/app-data"

echo "INITIALIZE API"

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

  # clean file duplicates
  rm -rf "${ROOT_APPDATA}"

  # add a lockfile to prevent re-running this
  touch "${APPDATA}/.init"
fi


exec "$@"