import getpass
import os
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from accounts.models import User


class Command(BaseCommand):
    help='Create a custom Dashboard admin. Reads ADMIN_USERNAME, ADMIN_EMAIL and ADMIN_PASSWORD, or prompts.'

    def add_arguments(self,parser):
        parser.add_argument('--noinput',action='store_true')
        parser.add_argument(
            '--reset-password',
            action='store_true',
            help='Set the password of an existing admin from ADMIN_PASSWORD.',
        )

    def handle(self,*args,**options):
        username=os.getenv('ADMIN_USERNAME','')
        email=os.getenv('ADMIN_EMAIL','')
        password=os.getenv('ADMIN_PASSWORD','')
        if not options['noinput']:
            username=username or input('Admin username: ').strip()
            email=email or input('Admin email: ').strip()
            if not password:
                password=getpass.getpass('Password: ')
                if password!=getpass.getpass('Confirm password: '):
                    raise CommandError('Passwords do not match.')
        if not all([username,email,password]):
            raise CommandError('Set ADMIN_USERNAME, ADMIN_EMAIL and ADMIN_PASSWORD in .env, or run without --noinput.')
        if User.objects.filter(username=username).exists():
            existing=User.objects.get(username=username)
            if not existing.is_store_admin:
                raise CommandError('That username already exists and is not an active admin. No changes made.')
            if options['reset_password']:
                try:
                    password_validation.validate_password(password,existing)
                except ValidationError as exc:
                    raise CommandError('; '.join(exc.messages)) from exc
                existing.set_password(password)
                existing.save(update_fields=['password'])
                self.stdout.write(self.style.SUCCESS(f'Updated the password for Dashboard admin "{username}".'))
                return
            self.stdout.write('Admin already exists. Password and account unchanged.')
            return
        user=User(username=username,email=email.strip().lower(),role=User.Role.ADMIN,first_name='Store')
        try:
            password_validation.validate_password(password,user)
            user.full_clean(exclude=['password'])
        except ValidationError as exc:
            raise CommandError('; '.join(exc.messages)) from exc
        user.set_password(password)
        user.save()
        self.stdout.write(self.style.SUCCESS(f'Created Dashboard admin "{username}". Sign in at /accounts/login/ and open /dashboard/.'))
