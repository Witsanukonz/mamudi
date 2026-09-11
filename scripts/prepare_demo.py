"""Create machine-local demo settings without replacing existing values."""
from pathlib import Path
import secrets

from dotenv import dotenv_values, set_key

ROOT = Path(__file__).resolve().parent.parent


def prepare(root=ROOT):
    env_path = root / '.env'
    if not env_path.exists():
        env_path.write_text((root / '.env.example').read_text(encoding='utf-8'), encoding='utf-8')
    values = dotenv_values(env_path)
    defaults = {
        'DEBUG': 'True',
        'SECRET_KEY': secrets.token_urlsafe(48),
        'ALLOWED_HOSTS': 'localhost,127.0.0.1',
        'ADMIN_USERNAME': 'admin',
        'ADMIN_EMAIL': 'admin@mamudi.example',
        'ADMIN_PASSWORD': secrets.token_urlsafe(18),
        'DEMO_CUSTOMER_PASSWORD': secrets.token_urlsafe(18),
    }
    for name, value in defaults.items():
        if not values.get(name) or (name == 'SECRET_KEY' and values[name] == 'replace-this-for-deployment'):
            set_key(str(env_path), name, value)
            values[name] = value
    access = root / 'DEMO_ACCESS.md'
    if not access.exists():
        access.write_text(
            '# Local MAMUDI demo accounts\n\n'
            'These credentials belong to this machine. Do not publish this file.\n\n'
            'Login: http://127.0.0.1:8000/accounts/login/\n\n'
            f'Admin username: `{values["ADMIN_USERNAME"]}`\n\n'
            f'Admin password: `{values["ADMIN_PASSWORD"]}`\n\n'
            'Dashboard: http://127.0.0.1:8000/dashboard/\n\n'
            'Customer username: `customer`\n\n'
            f'Customer password: `{values["DEMO_CUSTOMER_PASSWORD"]}`\n\n'
            'If an account already existed in the database, setup preserves its password.\n'
            'Use `python manage.py changepassword USERNAME` to change an existing account.\n',
            encoding='utf-8',
        )
    print('Local settings ready. Existing settings and access files preserved.')


if __name__ == '__main__':
    prepare()

