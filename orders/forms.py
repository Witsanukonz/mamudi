from django import forms
from django.core.validators import RegexValidator


class CheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'autocomplete': 'name'}))
    phone = forms.CharField(max_length=20, validators=[RegexValidator(r'^\+?[0-9 ()-]{9,20}$', 'Enter a valid phone number.')], widget=forms.TextInput(attrs={'type': 'tel', 'autocomplete': 'tel'}))
    address = forms.CharField(max_length=1000, widget=forms.Textarea(attrs={'rows': 3, 'autocomplete': 'street-address'}))
    province = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'autocomplete': 'address-level1'}))
    postal_code = forms.RegexField(r'^[0-9]{5}$', max_length=5, error_messages={'invalid': 'Enter a 5-digit postal code.'}, widget=forms.TextInput(attrs={'inputmode': 'numeric', 'autocomplete': 'postal-code'}))
    checkout_token = forms.UUIDField(widget=forms.HiddenInput)

