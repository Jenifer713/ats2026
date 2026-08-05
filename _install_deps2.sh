#!/bin/bash
set -e
echo "=== Installing production dependencies ==="

pip3 install \
  "psycopg2-binary==2.9.12" \
  "dj-database-url==2.2.0" \
  "whitenoise==6.7.0" \
  "gunicorn==22.0.0" \
  "python-dotenv==1.0.1" 2>&1

echo "=== Installation complete ==="
echo ""
echo "=== Verifying installed versions ==="
pip3 show psycopg2-binary 2>&1 | grep -E "^Name:|^Version:"
pip3 show dj-database-url 2>&1 | grep -E "^Name:|^Version:"
pip3 show whitenoise 2>&1 | grep -E "^Name:|^Version:"
pip3 show gunicorn 2>&1 | grep -E "^Name:|^Version:"
pip3 show python-dotenv 2>&1 | grep -E "^Name:|^Version:"

echo ""
echo "=== Generating requirements.txt ==="
cd /home/jeniffer/django/ats2626
pip3 freeze 2>&1 > requirements.txt
echo "requirements.txt generated successfully"

echo ""
echo "=== Verifying required packages in requirements.txt ==="
grep -iE "^psycopg2.binary==" requirements.txt && echo "OK: psycopg2-binary found" || echo "MISSING: psycopg2-binary"
grep -iE "^dj.database.url==" requirements.txt && echo "OK: dj-database-url found" || echo "MISSING: dj-database-url"
grep -iE "^whitenoise==" requirements.txt && echo "OK: whitenoise found" || echo "MISSING: whitenoise"
grep -iE "^gunicorn==" requirements.txt && echo "OK: gunicorn found" || echo "MISSING: gunicorn"
grep -iE "^python.dotenv==" requirements.txt && echo "OK: python-dotenv found" || echo "MISSING: python-dotenv"

echo ""
echo "=== Checking for duplicates ==="
sort requirements.txt | uniq -d | head -20

echo ""
echo "=== Done ==="
