#!/bin/bash
docker exec standby-postgres psql -U standby -d standby -c "SELECT id, substring(text_content,1,30) as text FROM anchors ORDER BY created_at DESC LIMIT 10;"
docker exec standby-postgres psql -U standby -d standby -c "SELECT anchor_id FROM anchor_vectors ORDER BY created_at DESC LIMIT 10;"
