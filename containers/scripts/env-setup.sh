#!/bin/bash

echo "Setting up $1"

for i in /usr/local/share/vocolab/*; do
  if [ -f "$i" ]; then
    ln -s /usr/local/bin/$i $i
  fi
done


if [ ! -d "/docs" ]; then
  git clone https://github.com/zerospeech/vocolab.wiki.git /docs
fi

echo "Done setting up $1"