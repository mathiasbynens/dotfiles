#!/bin/bash

if [ $# -lt 2 ]; then
  >&2 echo "Usage: $0 [timestamp] [message]"
  >&2 echo "Example: $0 1496929321 \"Release v1.56\""
  exit 1
fi

timestamp=$1
message="$2"

curl "https://api.speedcurve.com/v1/notes" -u 8z2p8yr45wmt9qk7oqzg1ln1nouf5q:x --request POST --data timestamp=$timestamp --data site_id=23524 --data note="$message" \
  && curl "https://api.speedcurve.com/v1/notes" -u 8z2p8yr45wmt9qk7oqzg1ln1nouf5q:x --request POST --data timestamp=$timestamp --data site_id=23523 --data note="$message" \
  && curl "https://api.speedcurve.com/v1/notes" -u 8z2p8yr45wmt9qk7oqzg1ln1nouf5q:x --request POST --data timestamp=$timestamp --data site_id=23525 --data note="$message" \
  && curl "https://api.speedcurve.com/v1/notes" -u 8z2p8yr45wmt9qk7oqzg1ln1nouf5q:x --request POST --data timestamp=$timestamp --data site_id=23527 --data note="$message" \
  && curl "https://api.speedcurve.com/v1/notes" -u 8z2p8yr45wmt9qk7oqzg1ln1nouf5q:x --request POST --data timestamp=$timestamp --data site_id=23535 --data note="$message" \
  && curl "https://api.speedcurve.com/v1/notes" -u 8z2p8yr45wmt9qk7oqzg1ln1nouf5q:x --request POST --data timestamp=$timestamp --data site_id=23478 --data note="$message" \
  && curl "https://api.speedcurve.com/v1/notes" -u 8z2p8yr45wmt9qk7oqzg1ln1nouf5q:x --request POST --data timestamp=$timestamp --data site_id=23304 --data note="$message"
