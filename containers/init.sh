#!/bin/bash

APPDATA="/app-data"
ROOT_APPDATA="/var/app-data"

if [ ! -f "${APPDATA}/.init" ]; then
  mkdir -p "${APPDATA}/archive"
  mkdir -p "${APPDATA}/leaderboards"
  mkdir -p "${APPDATA}/_static"
  mkdir -p "${APPDATA}/submissions"
  mkdir -p "${APPDATA}/user_data"

  # copy leaderboard archives
  if [ -d "${ROOT_APPDATA}/archive" ]; then
    cp -r  "${ROOT_APPDATA}/archive" "${APPDATA}/archive"
  fi

  # copy static files
  if [ -d "${ROOT_APPDATA}/_static" ]; then
    cp -r "${ROOT_APPDATA}/_static" "${APPDATA}/_static"
  fi

  # clean file duplicates
  rm -rf "${ROOT_APPDATA}"

  # add a lockfile to prevent re-running this
  touch "${APPDATA}/.init"

fi