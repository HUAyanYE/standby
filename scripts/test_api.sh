#!/bin/bash
curl -s -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -H "X-Device-Id: test-device-123" \
  -d '{"device_fingerprint":"test-device-123"}'
