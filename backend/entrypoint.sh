#!/bin/sh
set -e

echo "Aguardando o PostgreSQL em ${DB_HOST:-db}:${DB_PORT:-5432}..."
until python -c "import socket,os,sys; s=socket.socket(); s.settimeout(2);
try:
    s.connect((os.environ.get('DB_HOST','db'), int(os.environ.get('DB_PORT','5432')))); s.close()
except Exception:
    sys.exit(1)" 2>/dev/null; do
  echo "  ...banco indisponível, aguardando."
  sleep 2
done
echo "PostgreSQL disponível."

python manage.py migrate --noinput
python manage.py seed_sources

echo "Iniciando servidor Django em 0.0.0.0:8000"
exec python manage.py runserver 0.0.0.0:8000
