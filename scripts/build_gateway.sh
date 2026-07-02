#!/bin/bash
cd /mnt/d/LocalRepository/standby
echo "Building api-gateway..."
docker compose build api-gateway 2>&1
echo "BUILD_EXIT: $?"
