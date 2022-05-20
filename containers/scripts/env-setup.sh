#!/bin/bash

echo "Setting up $1"

for i in ~/.local/share/*; do
  if [ -f "$i" ]; then
    ln -s /usr/local/bin/$i $i
  fi
done

echo "Done setting up $1"