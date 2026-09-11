from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        CUSTOMER = 'customer', 'Customer'

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.CUSTOMER)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    province = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=5, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(Lower('email'), name='unique_user_email_ci')]

    @property
    def is_store_admin(self):
        return self.is_active and (self.is_superuser or self.role == self.Role.ADMIN)

