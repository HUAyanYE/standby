#!/bin/bash
TS=$(date +%s)
DEV_ID="test-$TS"
REG=$(curl -s -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -H "X-Device-Id: $DEV_ID" \
  -d "{\"device_fingerprint\": \"test-fp-$TS\"}")
TOKEN=$(echo "$REG" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('token',''))")

echo "=== Chain API ==="
curl -s http://localhost:8080/api/v1/anchors/a_4966b937/chain \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Device-Id: $DEV_ID" | python3 -m json.tool
