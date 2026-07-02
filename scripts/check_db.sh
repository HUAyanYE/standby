#!/bin/bash
docker exec standby-postgres psql -U standby -d standby -c "SELECT anchor_id FROM anchor_vectors ORDER BY created_at DESC LIMIT 5;"
docker exec standby-postgres psql -U standby -d standby -c "SELECT id, text_content FROM anchors ORDER BY created_at DESC LIMIT 5;"
