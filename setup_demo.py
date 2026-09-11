"""Prepare a complete local demo after cloning: python setup_demo.py."""
import os
from pathlib import Path
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parent


def run(*args):
    subprocess.run([str(arg) for arg in args], cwd=ROOT, check=True)


def main():
    if sys.version_info < (3, 12):
        raise SystemExit('Please install Python 3.12 or newer, then run this command again.')
    python = ROOT / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not python.exists():
        print('Creating .venv...', flush=True)
        venv.EnvBuilder(with_pip=True).create(ROOT / '.venv')
    run(python, '-m', 'pip', 'install', '-r', ROOT / 'requirements.txt')
    run(python, ROOT / 'scripts' / 'prepare_demo.py')
    run(python, 'manage.py', 'migrate', '--noinput')
    run(python, 'manage.py', 'seed_demo')
    run(python, 'manage.py', 'create_store_admin', '--noinput')
    run(python, 'manage.py', 'check')
    command = '.venv\\Scripts\\python.exe' if os.name == 'nt' else '.venv/bin/python'
    print('\nMAMUDI is ready. Login details: DEMO_ACCESS.md')
    print(f'Start the store: {command} manage.py runserver')
    print('Open http://127.0.0.1:8000/')


if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as error:
        raise SystemExit(f'Setup stopped at: {error.cmd[1:]}. Fix the error above and rerun python setup_demo.py.') from error

