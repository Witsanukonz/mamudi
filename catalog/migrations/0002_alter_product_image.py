from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('catalog', '0001_initial')]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='image',
            field=models.ImageField(blank=True, max_length=500, upload_to='products/'),
        ),
    ]
