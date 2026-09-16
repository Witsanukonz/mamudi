import os
from pathlib import Path
from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from accounts.models import User
from catalog.demo_images import hero_image, product_image
from catalog.models import Category, Product

PRODUCTS = [
    ('Essential Oversized Tee','T-Shirts',590,'Black','S M L XL',25,'Unisex'),
    ('Classic White Tee','T-Shirts',490,'White','S M L XL',20,'Unisex'),
    ('Heavyweight Tee','T-Shirts',690,'Charcoal','M L XL',15,'Unisex'),
    ('Boxy Fit Tee','T-Shirts',590,'Cream','S M L',12,'Unisex'),
    ('Relaxed Oxford Shirt','Shirts',990,'White','S M L XL',18,'Unisex'),
    ('Minimal Black Shirt','Shirts',1090,'Black','M L XL',10,'Male'),
    ('Linen Relaxed Shirt','Shirts',1190,'Beige','S M L',14,'Unisex'),
    ('Signature Hoodie','Hoodies',1490,'Black','S M L XL',20,'Unisex'),
    ('Essential Gray Hoodie','Hoodies',1390,'Gray','M L XL',16,'Unisex'),
    ('Everyday Zip Hoodie','Hoodies',1590,'Cream','S M L',8,'Unisex'),
    ('Utility Jacket','Jackets',1990,'Black','M L XL',10,'Male'),
    ('Minimal Coach Jacket','Jackets',1790,'Dark Gray','S M L XL',12,'Unisex'),
    ('Straight Fit Pants','Pants',1290,'Black','S M L XL',20,'Unisex'),
    ('Wide Leg Pants','Pants',1390,'Cream','S M L',14,'Female'),
    ('Relaxed Cargo Pants','Pants',1590,'Olive','M L XL',11,'Unisex'),
    ('Casual Shorts','Shorts',890,'Black','S M L XL',18,'Unisex'),
    ('Relaxed Cotton Shorts','Shorts',790,'Beige','S M L',15,'Unisex'),
    ('Minimal Midi Dress','Dresses',1490,'Black','S M L',10,'Female'),
    ('Everyday Tote Bag','Accessories',590,'Natural','',30,'Unisex'),
    ('Minimal Cap','Accessories',490,'Black','',25,'Unisex'),
]
DESCRIPTIONS={
    'T-Shirts':'เสื้อยืดทรงสบาย ดีไซน์มินิมอล เนื้อผ้านุ่ม เหมาะสำหรับ Everyday Look จับคู่กับกางเกงตัวโปรดได้ทุกวัน',
    'Shirts':'เสื้อเชิ้ตทรง Relaxed เส้นสายเรียบสะอาด ใส่ได้ทั้งวันทำงานและวันพักผ่อน แมตช์กับเสื้อยืดด้านในเป็นเลเยอร์ได้ง่าย',
    'Hoodies':'เสื้อฮู้ดทรงสบาย สัมผัสนุ่ม พร้อมกระเป๋าด้านหน้าและดีไซน์เรียบง่าย สำหรับวันสบายและอากาศเย็น',
    'Jackets':'แจ็กเก็ตเส้นสายมินิมอล ทรงคล่องตัว พร้อมกระเป๋าใช้งาน เหมาะสำหรับสวมทับเพิ่มความสมบูรณ์ให้ Everyday Look',
    'Pants':'กางเกงทรงร่วมสมัย ใส่สบาย เคลื่อนไหวสะดวก โทนสีเรียบง่าย จับคู่กับเสื้อเชิ้ตหรือเสื้อยืดได้อย่างลงตัว',
    'Shorts':'กางเกงขาสั้นทรงผ่อนคลาย เหมาะสำหรับวันพักผ่อน พร้อมกระเป๋าที่ใช้งานได้จริงและสีที่แมตช์ง่าย',
    'Dresses':'เดรสความยาว Midi ซิลูเอตเรียบหรู สวมใส่สบาย เสริมลุคด้วยเครื่องประดับชิ้นเล็กสำหรับทุกวัน',
    'Accessories':'แอ็กเซสซอรีดีไซน์เรียบง่าย ใช้งานสะดวก เติมรายละเอียดให้ลุคประจำวัน โทนสีธรรมชาติที่เข้ากับทุกชุด',
}


class Command(BaseCommand):
    help='Create 8 categories, 20 illustrated products and a demo customer without overwriting existing records.'

    @transaction.atomic
    def handle(self,*args,**options):
        categories={name:Category.objects.get_or_create(slug=slugify(name), defaults={'name':name,'description':f'MAMUDI {name}. Essentials for everyday life.'})[0] for name in DESCRIPTIONS}
        created_count=0
        for index,(name,category,price,color,sizes,stock,gender) in enumerate(PRODUCTS,1):
            slug=slugify(f'MAMUDI {name}')
            filename=f'products/{slug}.jpg'
            # Keep demo artwork in media for local Django and in static for
            # immutable/serverless deployments such as Vercel.
            for path in (Path(settings.MEDIA_ROOT)/filename, settings.BASE_DIR/'static/images'/filename):
                if not path.exists():
                    product_image(path,category,color,index)
            product,created=Product.objects.get_or_create(slug=slug,defaults={
                'name':f'MAMUDI {name}','category':categories[category],'price':price,'color':color,'sizes':sizes.split(),
                'stock':stock,'gender':gender,'description':DESCRIPTIONS[category], 'image':filename,
                'release_date':timezone.localdate()-timedelta(days=index-1),
            })
            created_count+=created
            if not product.image:
                product.image=filename
                product.save(update_fields=['image'])
        path=settings.BASE_DIR/'static/images/hero.jpg'
        if not path.exists():
            hero_image(path)
        customer,created=User.objects.get_or_create(username='customer', defaults={'email':'customer@mamudi.example','first_name':'Demo','last_name':'Customer','phone':'0812345678','address':'123 Demo Road','province':'Bangkok','postal_code':'10110'})
        if created:
            password=os.getenv('DEMO_CUSTOMER_PASSWORD')
            if password:
                customer.set_password(password)
            else:
                customer.set_unusable_password()
            customer.save()
        self.stdout.write(self.style.SUCCESS(f'Seed complete: {Category.objects.count()} categories, {Product.objects.count()} products ({created_count} added). Existing stock and accounts preserved.'))
        if created and not os.getenv('DEMO_CUSTOMER_PASSWORD'):
            self.stdout.write('Set customer password with: python manage.py changepassword customer')
