#!/bin/bash


echo "Evaluating submission $1"


mkdir -p "$1/scores"

echo "{" >> "$1/scores.json"

for i in {001..015}; do
  head -c 1M </dev/urandom > "$1/scores/$i.score"
  score=$(md5sum "$1/scores/$i.score" | cut -d' ' -f1 | python -c "x = [ int(c, 16) for c in input()]; print(sum(x) / len(x))")
  echo "\"$i\": \"$score\"," >> "$1/scores.json"
done

sed -i '$ s/.$//' "$1/scores.json"
echo "}" >> "$1/scores.json"