#!/bin/bash -x

python manage.py migrate --noinput || exit 1
python manage.py ensure_adminuser --no-input || exit 1
exec "$@"