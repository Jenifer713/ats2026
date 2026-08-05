#!/bin/bash
echo "=== Python version ==="
python3 --version 2>&1
echo "=== Checking available psycopg2-binary versions ==="
pip3 index versions psycopg2-binary 2>&1 | head -10
echo "=== Trying latest psycopg2-binary ==="
pip3 install "psycopg2-binary" --dry-run 2>&1 | head -20
echo "=== Checking pg_config ==="
which pg_config 2>&1
pg_config --version 2>&1
echo "=== Done ==="
