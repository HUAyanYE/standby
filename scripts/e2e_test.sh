#!/bin/bash
set -e

GATEWAY="http://localhost:8080"
PASS=0
FAIL=0

check() {
  local name="$1"
  local expected="$2"
  local actual="$3"
  if echo "$actual" | grep -q "$expected"; then
    echo "  PASS: $name"
    PASS=$((PASS+1))
  else
    echo "  FAIL: $name"
    echo "    expected pattern: $expected"
    echo "    got: $(echo "$actual" | head -c 300)"
    FAIL=$((FAIL+1))
  fi
}

sign_request() {
  local method="$1"
  local path="$2"
  local device_hash="$3"
  local timestamp="$4"
  local device_id="$5"
  local message="${method}${path}${timestamp}${device_id}"
  echo -n "$message" | openssl dgst -sha256 -hmac "$device_hash" -binary | base64
}

echo "=== Standby E2E API Test ==="
echo ""

# 1. Health check
echo "[1] Health Check"
HEALTH=$(curl -s "$GATEWAY/health")
check "health status" '"status":"ok"' "$HEALTH"
check "all engines up" '"anchor":true' "$HEALTH"

# 2. Register
echo "[2] Register"
TS=$(date +%s)
DEV_FP="e2e-fp-$TS"
DEV_ID="e2e-$TS"
REG=$(curl -s -X POST "$GATEWAY/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -H "X-Device-Id: $DEV_ID" \
  -d "{\"device_fingerprint\": \"$DEV_FP\"}")
check "register success" '"token"' "$REG"
TOKEN=$(echo "$REG" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('token',''))" 2>/dev/null || echo "")
check "token not empty" "." "$TOKEN"

# Extract device_hash from JWT claims
DEVICE_HASH=$(echo "$TOKEN" | python3 -c "
import sys,base64,json
token=sys.stdin.read().strip()
parts=token.split('.')
payload=parts[1]+'='*(4-len(parts[1])%4)
claims=json.loads(base64.b64decode(payload))
print(claims.get('device_id',''))
" 2>/dev/null || echo "")
echo "    device_hash: ${DEVICE_HASH:0:16}..."

# 3. Login
echo "[3] Login"
LOGIN=$(curl -s -X POST "$GATEWAY/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -H "X-Device-Id: $DEV_ID" \
  -d "{\"device_fingerprint\": \"$DEV_FP\"}")
check "login success" '"token"' "$LOGIN"

authed_curl() {
  local method="$1"
  local path="$2"
  shift 2
  local ts=$(date +%s)
  local sig=$(sign_request "$method" "$path" "$DEVICE_HASH" "$ts" "$DEV_ID")
  curl -s -X "$method" "$GATEWAY$path" \
    -H "Authorization: Bearer $TOKEN" \
    -H "X-Device-Id: $DEV_ID" \
    -H "X-Device-Signature: $sig" \
    -H "X-Request-Timestamp: $ts" \
    -H "Content-Type: application/json" \
    "$@"
}

# 4. List anchors
echo "[4] List Anchors"
ANCHORS=$(authed_curl GET "/api/v1/anchors")
check "list anchors ok" '"data"\|"items"\|"anchors"\|\[\]' "$ANCHORS"

# 5. Create anchor
echo "[5] Create Anchor"
CREATE=$(authed_curl POST "/api/v1/anchors" \
  -d '{"source_texts": ["今天天气真好，心情很舒畅"], "source": "user", "modality": "text"}')
check "create anchor ok" '"id"\|"anchor_id"\|"success"\|"text"' "$CREATE"
ANCHOR_ID=$(echo "$CREATE" | python3 -c "
import sys,json
d=json.load(sys.stdin)
data=d.get('data',d)
if isinstance(data,dict):
  print(data.get('anchor_id', data.get('id','')))
else:
  print('')
" 2>/dev/null || echo "")
echo "    anchor_id: $ANCHOR_ID"

if [ -n "$ANCHOR_ID" ]; then
  # 6. Get anchor detail
  echo "[6] Get Anchor Detail"
  DETAIL=$(authed_curl GET "/api/v1/anchors/$ANCHOR_ID")
  check "anchor detail ok" '"text"\|"content"\|"topics"\|"id"' "$DETAIL"

  # 7. Submit reaction
  echo "[7] Submit Reaction"
  REACT=$(authed_curl POST "/api/v1/reactions" \
    -d "{\"anchor_id\": \"$ANCHOR_ID\", \"reaction_type\": 1, \"opinion_text\": \"我也喜欢好天气\"}")
  check "reaction ok" '"success"\|"id"\|"resonance"\|"reaction"\|"value"' "$REACT"

  # 8. Get reaction distribution
  echo "[8] Reaction Distribution"
  DIST=$(authed_curl GET "/api/v1/reactions/distribution/$ANCHOR_ID")
  check "distribution ok" '"distribution"\|"total"\|"data"\|"count"' "$DIST"

  # 9. Feeling chain
  echo "[9] Feeling Chain"
  CHAIN=$(authed_curl GET "/api/v1/anchors/$ANCHOR_ID/chain?max_depth=3")
  check "chain ok" '"chain"\|"data"\|"depth"\|"reactions"\|\[\]' "$CHAIN"

  # 10. Group memory
  echo "[10] Group Memory"
  MEMORY=$(authed_curl GET "/api/v1/anchors/$ANCHOR_ID/memory")
  check "memory ok" '"memory"\|"data"\|"opinions"\|"summary"' "$MEMORY"
fi

# 11. Submit context
echo "[11] Submit Context"
CTX=$(authed_curl POST "/api/v1/context" \
  -d '{"scene_type": "commute", "mood_hint": "calm", "attention_level": "low"}')
check "context ok" '"success"\|"ok"\|"status"\|"message"' "$CTX"

# 12. Contextual weights
echo "[12] Contextual Weights"
WEIGHTS=$(authed_curl GET "/api/v1/context/weights?topics=%E5%A4%A9%E6%B0%94,%E5%BF%83%E6%83%85,%E6%88%B7%E5%A4%96")
check "weights ok" '"weights"\|"data"\|"topic"\|"value"' "$WEIGHTS"

# 13. Encode text
echo "[13] Encode Text"
ENCODE=$(authed_curl POST "/api/v1/encode" \
  -d '{"texts": ["测试文本编码"]}')
check "encode ok" '"vectors"\|"embeddings"\|"data"\|"encoded"\|"dim"' "$ENCODE"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
