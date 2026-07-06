import os
import secrets

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _load_dotenv(path):
    if not os.path.exists(path):
        return
    with open(path, encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(os.path.join(BASE_DIR, '.env'))


_PLACEHOLDER_SECRET = 'degistirin-uzun-rastgele-bir-deger'


def _get_secret_key():
    key = os.environ.get('SECRET_KEY')
    if key and key != _PLACEHOLDER_SECRET:
        return key
    if os.environ.get('FLASK_DEBUG', '0') == '1':
        # Only in debug mode: a random key per process is acceptable.
        return secrets.token_hex(32)
    raise RuntimeError(
        'SECRET_KEY is not set (or still the placeholder). Generate one with '
        '`python -c "import secrets; print(secrets.token_hex(32))"` and set it in .env.'
    )


class Config:
    SECRET_KEY = _get_secret_key()

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 'mysql+pymysql://root:root@localhost:3306/seizure_tracking'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
