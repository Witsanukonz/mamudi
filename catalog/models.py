from decimal import Decimal
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone

SIZE_CHOICES = [(size, size) for size in ['XS', 'S', 'M', 'L', 'XL', 'XXL']]


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['id']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Product(models.Model):
    class Gender(models.TextChoices):
        MALE = 'Male', 'Male'
        FEMALE = 'Female', 'Female'
        UNISEX = 'Unisex', 'Unisex'

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    stock = models.PositiveIntegerField(default=0)
    gender = models.CharField(max_length=10, choices=Gender.choices, default=Gender.UNISEX)
    sizes = models.JSONField(default=list, blank=True)
    color = models.CharField(max_length=60)
    image = models.ImageField(upload_to='products/', blank=True, max_length=500)
    release_date = models.DateField(default=timezone.localdate)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-release_date', '-id']
        constraints = [models.CheckConstraint(condition=models.Q(price__gt=0), name='product_positive_price')]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.slug])

    @property
    def image_url(self):
        if not self.image:
            return static('images/product-placeholder.svg')
        name = str(self.image.name).replace('\\', '/')
        if name.startswith('products/mamudi-'):
            return static(f'images/{name}')
        return self.image.url

    @property
    def gallery_image_urls(self):
        urls = [self.image_url]
        for product_image in self.additional_images.all():
            if product_image.image:
                urls.append(product_image.image.url)
        return urls

    @property
    def image_count(self):
        return (1 if self.image else 0) + self.additional_images.count()

    @property
    def short_name(self):
        return self.name.removeprefix('MAMUDI ')

    @property
    def default_size(self):
        return self.sizes[0] if self.sizes else 'One size'


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='additional_images')
    image = models.ImageField(upload_to='products/', max_length=500)
    position = models.PositiveSmallIntegerField(validators=[MinValueValidator(2), MaxValueValidator(5)])

    class Meta:
        ordering = ['position']
        constraints = [
            models.UniqueConstraint(fields=['product', 'position'], name='unique_product_image_position'),
            models.CheckConstraint(condition=models.Q(position__gte=2, position__lte=5), name='product_image_position_2_to_5'),
        ]

    def __str__(self):
        return f'{self.product.name} image {self.position}'
