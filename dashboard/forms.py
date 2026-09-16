from django import forms
from django.contrib.auth import password_validation
from django.utils.text import slugify
from accounts.forms import UniqueEmailMixin
from accounts.models import User
from catalog.models import Category, Product, ProductImage, SIZE_CHOICES


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
    image_count = forms.TypedChoiceField(
        label='Number of product images',
        choices=[(number, f'{number} image{"s" if number > 1 else ""}') for number in range(1, 6)],
        coerce=int,
        initial=1,
        help_text='Choose 1–5 images. Reducing this number removes the extra image slots when you save.',
        widget=forms.Select(attrs={'data-image-count': ''}),
    )
    image_1 = forms.ImageField(label='Image 1 · Main image', required=False)
    image_2 = forms.ImageField(label='Image 2', required=False)
    image_3 = forms.ImageField(label='Image 3', required=False)
    image_4 = forms.ImageField(label='Image 4', required=False)
    image_5 = forms.ImageField(label='Image 5', required=False)

    class Meta:
        model = Product
        fields = ['name', 'category', 'description', 'price', 'stock', 'sizes', 'gender', 'color', 'release_date', 'is_active']
        widgets = {'description': forms.Textarea(attrs={'rows': 4}), 'release_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'), 'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}), 'stock': forms.NumberInput(attrs={'min': 0})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order_fields(['name', 'category', 'description', 'price', 'stock', 'sizes', 'gender', 'color', 'image_count', 'image_1', 'image_2', 'image_3', 'image_4', 'image_5', 'release_date', 'is_active'])
        existing = {}
        if self.instance.pk:
            if self.instance.image:
                existing[1] = self.instance.image_url
            existing.update({item.position: item.image.url for item in self.instance.additional_images.all() if item.image})
            self.fields['image_count'].initial = max(existing, default=1)
        for position in range(1, 6):
            field = self.fields[f'image_{position}']
            field.widget.attrs.update({
                'accept': 'image/jpeg,image/png,image/webp',
                'data-product-image-input': '',
                'data-image-slot': position,
                'data-existing-url': existing.get(position, ''),
            })

    @property
    def image_slots(self):
        return [
            {
                'field': self[f'image_{position}'],
                'position': position,
                'url': self.fields[f'image_{position}'].widget.attrs.get('data-existing-url', ''),
            }
            for position in range(1, 6)
        ]

    def clean(self):
        cleaned = super().clean()
        count = cleaned.get('image_count')
        if not count:
            return cleaned
        existing_positions = set()
        if self.instance.pk:
            if self.instance.image:
                existing_positions.add(1)
            existing_positions.update(self.instance.additional_images.values_list('position', flat=True))
        for position in range(1, count + 1):
            field_name = f'image_{position}'
            image = cleaned.get(field_name)
            if image and image.size > 5 * 1024 * 1024:
                self.add_error(field_name, 'Image must be 5 MB or smaller.')
            if image and getattr(image, 'image', None) and image.image.format not in ['JPEG', 'PNG', 'WEBP']:
                self.add_error(field_name, 'Use a JPEG, PNG, or WebP image.')
            if not image and position not in existing_positions:
                self.add_error(field_name, f'Upload and crop image {position}.')
        return cleaned

    def save(self, commit=True):
        product = super().save(commit=False)
        if not product.slug:
            product.slug = unique_slug(Product, product.name)
        if commit:
            if self.cleaned_data.get('image_1'):
                product.image = self.cleaned_data['image_1']
            product.save()
            count = self.cleaned_data['image_count']
            existing = {item.position: item for item in product.additional_images.all()}
            for position in range(2, count + 1):
                image = self.cleaned_data.get(f'image_{position}')
                if image:
                    item = existing.get(position) or ProductImage(product=product, position=position)
                    item.image = image
                    item.save()
            product.additional_images.filter(position__gt=count).delete()
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
