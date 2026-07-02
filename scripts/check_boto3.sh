#!/bin/bash
python3 -c "import boto3; print('boto3 available')" 2>/dev/null || echo "boto3 not available"
pip3 install boto3 2>/dev/null || python3 -m pip install boto3 2>/dev/null || echo "cannot install boto3"
