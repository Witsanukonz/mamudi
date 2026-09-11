from django import forms
from django.contrib.auth import password_validation
from django.utils.text import slugify
from accounts.forms import UniqueEmailMixin
from accounts.models import User
from catalog.models import Category, Product, SIZE_CHOICES


def unique_slug(model, name, pk=None):
    base = slugify(name, allow_unicode=False)[:160] or 'item'
    candidate, index = base, 2
    while model.objects.filter(slug=candidate).exclude(pk=pk).exists():
        candidate = f'{base}-{index}'
        index += 1
    return candidate


class ProductForm(forms.ModelForm):
    sizes = forms.MultipleChoiceField(choices=SIZE_CHOICES, widget=forms.CheckboxSelectMultiple, required=False, help_text='Leave empty for one-size accessories. Stock is shared across all sizes.')
    gender = forms.ChoiceField(choices=Product.Gender.choices, widget=forms.RadioSelect)

    class Meta:
        model = Product
        fields = ['name', 'category', 'description', 'price', 'stock', 'sizes', 'gender', 'color', 'image', 'release_date', 'is_active']
        widgets = {'description': forms.Textarea(attrs={'rows': 4}), 'release_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'), 'image': forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png,image/webp', 'data-image-input': ''}), 'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}), 'stock': forms.NumberInput(attrs={'min': 0})}

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image and hasattr(image, 'content_type'):
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError('Image must be 5 MB or smaller.')
            if getattr(image, 'image', None) and image.image.format not in ['JPEG', 'PNG', 'WEBP']:
                raise forms.ValidationError('Use a JPEG, PNG, or WebP image.')
        return image

    def save(self, commit=True):
        product = super().save(commit=False)
        if not product.slug:
            product.slug = unique_slug(Product, product.name)
        if commit:
            product.save()
        return product


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}

    def save(self, commit=True):
        category = super().save(commit=False)
        if not category.slug:
            category.slug = unique_slug(Category, category.name)
        if commit:
            category.save()
        return category


class UserForm(UniqueEmailMixin, forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False, help_text='Use at least 8 characters. Leave empty when editing to keep the current password.')
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=False)

    class Meta:
        model = User
        # Password is a declared form field, excluded from model assignment.
        # Only set_password() below may write the model's password hash.
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'confirm_password', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order_fields(['username', 'email', 'first_name', 'last_name', 'role', 'password', 'confirm_password', 'is_active'])
        if not self.instance.pk:
            self.fields['password'].required = True
            self.fields['confirm_password'].required = True

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        if password != cleaned.get('confirm_password'):
            self.add_error('confirm_password', 'Passwords do not match.')
        if password:
            candidate = User(username=cleaned.get('username', ''), email=cleaned.get('email', ''), first_name=cleaned.get('first_name', ''), last_name=cleaned.get('last_name', ''))
            password_validation.validate_password(password, candidate)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get('password'):
            user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user
