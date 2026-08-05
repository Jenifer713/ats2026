#!/bin/bash
# Check for virtual environments
echo "--- Looking for venv ---"
ls /home/jeniffer/django/ats2626/ 2>&1
echo "--- Checking if venv exists ---"
ls /home/jeniffer/django/ats2626/venv 2>&1
ls /home/jeniffer/django/ats2626/env 2>&1
ls /home/jeniffer/django/ats2626/.venv 2>&1
echo "--- Already installed packages ---"
pip3 list 2>&1 | grep -iE "psycopg2|dj-database|whitenoise|gunicorn|python-dotenv"
echo "--- Done ---"
