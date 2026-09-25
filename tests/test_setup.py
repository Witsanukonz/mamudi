from pathlib import Path
import tempfile
from unittest import TestCase
from unittest.mock import patch
from contextlib import redirect_stdout
from io import StringIO
from dotenv import dotenv_values
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase as DjangoTestCase
from scripts.prepare_demo import prepare

User = get_user_model()


class DemoSetupTests(TestCase):
    def test_fresh_settings_and_rerun_preserve_credentials(self):
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(StringIO()):
            root = Path(temp)
            (root / '.env.example').write_text('DEBUG=True\nSECRET_KEY=replace-this-for-deployment\n', encoding='utf-8')
            (root / 'db.sqlite3').write_bytes(b'tracked demo database')
            prepare(root)
            first = (root / '.env').read_bytes()
            credentials = (root / 'DEMO_ACCESS.md').read_bytes()
            values = dotenv_values(root / '.env')
            self.assertNotEqual(values['SECRET_KEY'], 'replace-this-for-deployment')
            self.assertGreaterEqual(len(values['ADMIN_PASSWORD']), 20)
            self.assertNotEqual(values['ADMIN_PASSWORD'], values['DEMO_CUSTOMER_PASSWORD'])
            self.assertEqual((root / 'local.sqlite3').read_bytes(), b'tracked demo database')
            self.assertEqual(values['DATABASE_URL'], f'sqlite:///{(root / "local.sqlite3").as_posix()}')
            prepare(root)
            self.assertEqual(first, (root / '.env').read_bytes())
            self.assertEqual(credentials, (root / 'DEMO_ACCESS.md').read_bytes())

    def test_existing_custom_settings_are_preserved(self):
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(StringIO()):
            root = Path(temp)
            (root / '.env').write_text('ADMIN_USERNAME=teacher\nADMIN_PASSWORD=existing-strong-password\nDATABASE_URL=sqlite:///custom.db\n', encoding='utf-8')
            prepare(root)
            values = dotenv_values(root / '.env')
            self.assertEqual(values['ADMIN_USERNAME'], 'teacher')
            self.assertEqual(values['ADMIN_PASSWORD'], 'existing-strong-password')
            self.assertEqual(values['DATABASE_URL'], 'sqlite:///custom.db')


class DemoCredentialCommandTests(DjangoTestCase):
    def test_setup_flags_update_existing_demo_passwords_and_normal_runs_preserve_them(self):
        admin = User.objects.create_user(
            username='admin',
            email='admin@mamudi.example',
            password='Old-Admin-Password-123!',
            role=User.Role.ADMIN,
        )
        customer = User.objects.create_user(
            username='customer',
            email='customer@mamudi.example',
            password='Old-Customer-Password-123!',
        )
        first_env = {
            'ADMIN_USERNAME': 'admin',
            'ADMIN_EMAIL': 'admin@mamudi.example',
            'ADMIN_PASSWORD': 'Generated-Admin-Password-928!',
            'DEMO_CUSTOMER_PASSWORD': 'Generated-Customer-Password-739!',
        }
        with patch.dict('os.environ', first_env, clear=False), redirect_stdout(StringIO()):
            call_command('seed_demo', reset_customer_password=True)
            call_command('create_store_admin', noinput=True, reset_password=True)

        admin.refresh_from_db()
        customer.refresh_from_db()
        self.assertTrue(admin.check_password(first_env['ADMIN_PASSWORD']))
        self.assertTrue(customer.check_password(first_env['DEMO_CUSTOMER_PASSWORD']))
        admin_hash = admin.password
        customer_hash = customer.password

        later_env = {
            **first_env,
            'ADMIN_PASSWORD': 'Different-Admin-Password-928!',
            'DEMO_CUSTOMER_PASSWORD': 'Different-Customer-Password-739!',
        }
        with patch.dict('os.environ', later_env, clear=False), redirect_stdout(StringIO()):
            call_command('seed_demo')
            call_command('create_store_admin', noinput=True)

        admin.refresh_from_db()
        customer.refresh_from_db()
        self.assertEqual(admin.password, admin_hash)
        self.assertEqual(customer.password, customer_hash)
