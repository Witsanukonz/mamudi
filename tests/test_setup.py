from pathlib import Path
import tempfile
from unittest import TestCase
from unittest.mock import patch
from contextlib import redirect_stdout
from io import StringIO
from dotenv import dotenv_values
from scripts.prepare_demo import prepare


class DemoSetupTests(TestCase):
    def test_fresh_settings_and_rerun_preserve_credentials(self):
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(StringIO()):
            root = Path(temp)
            (root / '.env.example').write_text('DEBUG=True\nSECRET_KEY=replace-this-for-deployment\n', encoding='utf-8')
            prepare(root)
            first = (root / '.env').read_bytes()
            credentials = (root / 'DEMO_ACCESS.md').read_bytes()
            values = dotenv_values(root / '.env')
            self.assertNotEqual(values['SECRET_KEY'], 'replace-this-for-deployment')
            self.assertGreaterEqual(len(values['ADMIN_PASSWORD']), 20)
            self.assertNotEqual(values['ADMIN_PASSWORD'], values['DEMO_CUSTOMER_PASSWORD'])
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

