#!/bin/bash
python3 --version
pip3 --version
pip --version
which python3
which pip3
echo "---venv check---"
ls /home/jeniffer/django/
echo "---django check---"
python3 -c "import django; print(django.__version__)"
