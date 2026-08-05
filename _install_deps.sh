#!/bin/bash
set -e
echo "=== Installing production dependencies ==="

pip3 install \
  "psycopg2-binary==2.9.9" \
  "dj-database-url==2.2.0" \
  "whitenoise==6.7.0" \
  "gunicorn==22.0.0" \
  "python-dotenv==1.0.1" 2>&1

echo "=== Installation complete ==="
echo "=== Verifying installed versions ==="
pip3 show psycopg2-binary dj-database-url whitenoise gunicorn python-dotenv 2>&1

echo "=== Generating requirements.txt ==="
cd /home/jeniffer/django/ats2626
pip3 freeze > requirements.txt 2>&1
echo "=== requirements.txt generated ==="
echo "=== Checking required packages in requirements.txt ==="
grep -E "psycopg2.binary|dj.database.url|whitenoise|gunicorn|python.dotenv" requirements.txt 2>&1
echo "=== Done ==="
