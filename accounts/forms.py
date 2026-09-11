from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class UniqueEmailMixin:
    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        query = User.objects.filter(email__iexact=email)
        if self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
        if query.exists():
            raise forms.ValidationError('This email address is already in use.')
        return email


class RegisterForm(UniqueEmailMixin, UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']


class ProfileForm(UniqueEmailMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'province', 'postal_code']
        widgets = {'address': forms.Textarea(attrs={'rows': 3})}

