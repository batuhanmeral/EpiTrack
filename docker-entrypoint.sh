#!/bin/sh
set -e

# MySQL hazır olana kadar bekle, sonra şema migration'larını uygula
echo "Veritabanı bekleniyor..."
python - <<'PY'
import os, time, sys
from urllib.parse import urlparse
import socket

url = urlparse(os.environ.get("DATABASE_URL", ""))
host, port = url.hostname or "db", url.port or 3306
for _ in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f"{host}:{port} hazir.")
            sys.exit(0)
    except OSError:
        time.sleep(1)
print("Veritabanina baglanilamadi.", file=sys.stderr)
sys.exit(1)
PY

echo "Migration'lar uygulaniyor..."
flask db upgrade

exec "$@"
