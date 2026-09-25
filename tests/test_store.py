import io
import tempfile
import uuid
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from catalog.models import Category, Product, ProductImage
from orders.models import Order
from orders.services import place_order, transition_order

User=get_user_model()


def upload(name='sample.png'):
    data=io.BytesIO()
    Image.new('RGB',(40,50),'beige').save(data,'PNG')
    return SimpleUploadedFile(name,data.getvalue(),content_type='image/png')


@override_settings(ALLOWED_HOSTS=['testserver','localhost'])
class StoreTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin=User.objects.create_user(username='manager',email='manager@example.com',password='Strong-Password-123!',role='admin')
        cls.customer=User.objects.create_user(username='alice',email='alice@example.com',password='Strong-Password-123!')
        cls.other=User.objects.create_user(username='bob',email='bob@example.com',password='Strong-Password-123!')
        cls.category=Category.objects.create(name='T-Shirts',slug='t-shirts')
        cls.product=Product.objects.create(category=cls.category,name='MAMUDI Everyday Tee',slug='everyday-tee',description='Soft cotton tee',price='590',stock=5,color='Black',sizes=['S','M'],gender='Unisex')
        cls.hidden=Product.objects.create(category=cls.category,name='Hidden Tee',slug='hidden-tee',description='Hidden',price='200',stock=3,color='Cream',is_active=False)
        cls.sold=Product.objects.create(category=cls.category,name='Sold Tee',slug='sold-tee',description='Sold out',price='800',stock=0,color='Gray',sizes=['L'])

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.media=override_settings(MEDIA_ROOT=self.temp.name)
        self.media.enable()
        self.addCleanup(self.media.disable)

    def login_admin(self):
        self.client.force_login(self.admin)

    def cart(self, quantity=2, size='S', product=None):
        product=product or self.product
        return {f'{product.pk}:{size}':{'product_id':product.pk,'size':size,'quantity':quantity}}

    def shipping(self):
        return {'full_name':'Alice Test','phone':'0812345678','address':'123 Test Road','province':'Bangkok','postal_code':'10110'}

    def product_data(self,**kwargs):
        return {'name':'MAMUDI New Tee','category':self.category.pk,'description':'A new essential','price':'999.50','stock':12,'sizes':['S','L'],'gender':'Unisex','color':'Beige','image_count':1,'release_date':'2026-09-11','is_active':'on',**kwargs}

    def user_data(self,**kwargs):
        return {'username':'newuser','email':'new@example.com','first_name':'New','last_name':'Member','role':'customer','is_active':'on','password':'New-Strong-Password-928!','confirm_password':'New-Strong-Password-928!',**kwargs}

    def test_public_pages_and_templates(self):
        for url in ['/', '/products/', self.product.get_absolute_url(),'/cart/','/accounts/login/','/accounts/register/','/accounts/password-reset/']:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code,200)

    def test_hidden_product_not_public(self):
        self.assertEqual(self.client.get(self.hidden.get_absolute_url()).status_code,404)
        ids=[p.pk for p in self.client.get('/products/').context['page_obj']]
        self.assertNotIn(self.hidden.pk,ids)

    def test_all_shop_filters(self):
        response=self.client.get('/products/',{'q':'Everyday','category':'t-shirts','gender':'Unisex','size':'M','min_price':'500','max_price':'600','availability':'in_stock','sort':'price_asc'})
        self.assertEqual([p.pk for p in response.context['page_obj']],[self.product.pk])
        self.assertEqual([p.pk for p in self.client.get('/products/',{'availability':'out_of_stock'}).context['page_obj']],[self.sold.pk])

    def test_bad_filter_values_are_safe(self):
        for value in ['abc','NaN','Infinity','-5','1e1000000']:
            with self.subTest(value=value):
                response=self.client.get('/products/',{'min_price':value,'max_price':value,'sort':'bad','page':'not-a-page'})
                self.assertEqual(response.status_code,200)

    def test_sort_prices(self):
        self.assertEqual([p.pk for p in self.client.get('/products/',{'sort':'price_desc'}).context['page_obj']],[self.sold.pk,self.product.pk])

    def test_registration_ignores_role_escalation_and_hashes_password(self):
        response=self.client.post('/accounts/register/',{'username':'newcustomer','email':'NEWCUSTOMER@example.com','password1':'Good-Customer-928!','password2':'Good-Customer-928!','role':'admin','is_superuser':'on'})
        self.assertRedirects(response,'/')
        user=User.objects.get(username='newcustomer')
        self.assertEqual(user.role,'customer')
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password('Good-Customer-928!'))
        self.assertEqual(user.email,'newcustomer@example.com')

    def test_duplicate_email_case_insensitive(self):
        response=self.client.post('/accounts/register/',{'username':'duplicate','email':'ALICE@EXAMPLE.COM','password1':'Good-Customer-928!','password2':'Good-Customer-928!'})
        self.assertContains(response,'already in use')
        self.assertFalse(User.objects.filter(username='duplicate').exists())

    def test_login_logout_and_disabled_user(self):
        self.assertRedirects(self.client.post('/accounts/login/',{'username':'alice','password':'Strong-Password-123!'}),'/')
        self.assertEqual(self.client.get('/accounts/logout/').status_code,405)
        self.assertRedirects(self.client.post('/accounts/logout/'),'/')
        self.customer.is_active=False
        self.customer.save()
        self.assertContains(self.client.post('/accounts/login/',{'username':'alice','password':'Strong-Password-123!'}),'Please enter a correct')

    def test_profile_changes_cannot_escalate_role(self):
        self.client.force_login(self.customer)
        response=self.client.post('/accounts/profile/',{'first_name':'Alice Updated','last_name':'Test','email':'alice@example.com','role':'admin'})
        self.assertRedirects(response,'/accounts/profile/')
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.first_name,'Alice Updated')
        self.assertEqual(self.customer.role,'customer')

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_password_reset_email_and_token_flow(self):
        response=self.client.post('/accounts/password-reset/',{'email':self.customer.email})
        self.assertRedirects(response,'/accounts/password-reset/sent/')
        self.assertEqual(len(mail.outbox),1)
        url=next(line for line in mail.outbox[0].body.splitlines() if line.startswith('http'))
        response=self.client.get(url,follow=True)
        self.assertContains(response,'Choose a new password')
        response=self.client.post(response.request['PATH_INFO'],{'new_password1':'Reset-Secret-937!','new_password2':'Reset-Secret-937!'})
        self.assertRedirects(response,'/accounts/reset/complete/')
        self.customer.refresh_from_db()
        self.assertTrue(self.customer.check_password('Reset-Secret-937!'))

    def test_guest_dashboard_redirect(self):
        self.assertEqual(self.client.get('/dashboard/').status_code,302)

    def test_customer_cannot_access_any_dashboard_action(self):
        self.client.force_login(self.customer)
        for url in ['/dashboard/','/dashboard/products/','/dashboard/users/','/dashboard/categories/','/dashboard/orders/','/dashboard/products/add/',f'/dashboard/products/{self.product.pk}/edit/',f'/dashboard/users/{self.admin.pk}/toggle/',f'/dashboard/users/{self.admin.pk}/delete/']:
            for method in ['get','post']:
                with self.subTest(url=url,method=method):
                    self.assertEqual(getattr(self.client,method)(url).status_code,403)

    def test_dashboard_pages_render(self):
        self.login_admin()
        for url in ['/dashboard/','/dashboard/products/','/dashboard/users/','/dashboard/categories/','/dashboard/orders/','/dashboard/products/add/','/dashboard/categories/add/','/dashboard/users/add/',f'/dashboard/users/{self.customer.pk}/',f'/dashboard/products/{self.hidden.pk}/']:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code,200)

    def test_product_add_all_components_and_image_upload(self):
        self.login_admin()
        response=self.client.get('/dashboard/products/add/')
        for component in ['type="text"','type="radio"','<textarea','type="checkbox"','<select','type="date"','type="file"','data-image-preview']:
            self.assertContains(response,component)
        response=self.client.post('/dashboard/products/add/',self.product_data(image_1=upload()))
        self.assertRedirects(response,'/dashboard/products/')
        product=Product.objects.get(name='MAMUDI New Tee')
        self.assertEqual(product.sizes,['S','L'])
        self.assertEqual(product.price,Decimal('999.50'))
        self.assertTrue(Path(product.image.path).exists())

    def test_product_edit_stock_and_delete_post_only(self):
        self.login_admin()
        self.assertRedirects(self.client.post(f'/dashboard/products/{self.product.pk}/edit/',self.product_data(stock=7,image_1=upload())),'/dashboard/products/')
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock,7)
        self.assertEqual(self.product.slug,'everyday-tee')
        self.assertEqual(self.client.get(f'/dashboard/products/{self.product.pk}/delete/').status_code,200)
        self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())
        self.client.post(f'/dashboard/products/{self.product.pk}/delete/')
        self.assertFalse(Product.objects.filter(pk=self.product.pk).exists())

    def test_product_validation(self):
        self.login_admin()
        for data in [self.product_data(stock=-1,image_1=upload()),self.product_data(price=0,image_1=upload()),self.product_data(sizes=['BAD'],image_1=upload()),self.product_data(image_1=SimpleUploadedFile('fake.png',b'not an image',content_type='image/png'))]:
            response=self.client.post('/dashboard/products/add/',data)
            self.assertTrue(response.context['form'].errors)
        self.assertFalse(Product.objects.filter(name='MAMUDI New Tee').exists())

    def test_product_gallery_saves_three_images_and_can_reduce_count(self):
        self.login_admin()
        response=self.client.post('/dashboard/products/add/',self.product_data(
            image_count=3,
            image_1=upload('front.png'),
            image_2=upload('back.png'),
            image_3=upload('detail.png'),
        ))
        self.assertRedirects(response,'/dashboard/products/')
        product=Product.objects.get(name='MAMUDI New Tee')
        self.assertEqual(list(product.additional_images.values_list('position',flat=True)),[2,3])
        self.assertEqual(product.image_count,3)
        detail=self.client.get(product.get_absolute_url())
        self.assertEqual(detail.status_code,200)
        self.assertContains(detail,'data-gallery-thumbnail',count=3)

        response=self.client.post(f'/dashboard/products/{product.pk}/edit/',self.product_data(image_count=1))
        self.assertRedirects(response,'/dashboard/products/')
        product.refresh_from_db()
        self.assertTrue(product.image)
        self.assertEqual(product.image_count,1)
        self.assertFalse(ProductImage.objects.filter(product=product).exists())

    def test_product_gallery_requires_every_selected_image_on_create(self):
        self.login_admin()
        response=self.client.post('/dashboard/products/add/',self.product_data(image_count=2,image_1=upload('front.png')))
        self.assertEqual(response.status_code,200)
        self.assertIn('image_2',response.context['form'].errors)
        self.assertFalse(Product.objects.filter(name='MAMUDI New Tee').exists())

    def test_product_gallery_uses_absolute_blob_urls_on_local_storage(self):
        blob_url='https://example.public.blob.vercel-storage.com/product-front.jpg'
        detail_url='https://example.public.blob.vercel-storage.com/product-detail.jpg'
        self.product.image=blob_url
        self.product.save(update_fields=['image'])
        ProductImage.objects.create(product=self.product,position=2,image=detail_url)
        self.assertEqual(self.product.image_url,blob_url)
        self.assertEqual(self.product.gallery_image_urls,[blob_url,detail_url])

    def test_category_crud_and_protected_delete(self):
        self.login_admin()
        self.assertRedirects(self.client.post('/dashboard/categories/add/',{'name':'New category','description':'New'}),'/dashboard/categories/')
        category=Category.objects.get(name='New category')
        self.client.post(f'/dashboard/categories/{category.pk}/edit/',{'name':'Renamed','description':'Updated'})
        category.refresh_from_db()
        self.assertEqual(category.name,'Renamed')
        self.client.post(f'/dashboard/categories/{category.pk}/delete/')
        self.assertFalse(Category.objects.filter(pk=category.pk).exists())
        self.client.post(f'/dashboard/categories/{self.category.pk}/delete/')
        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())

    def test_user_create_edit_enable_disable_delete(self):
        self.login_admin()
        self.assertRedirects(self.client.post('/dashboard/users/add/',self.user_data()),'/dashboard/users/')
        user=User.objects.get(username='newuser')
        self.assertTrue(user.check_password('New-Strong-Password-928!'))
        hashed=user.password
        self.client.post(f'/dashboard/users/{user.pk}/edit/',self.user_data(first_name='Edited',password='',confirm_password=''))
        user.refresh_from_db()
        self.assertEqual(user.first_name,'Edited')
        self.assertEqual(user.password,hashed)
        for active in [False,True]:
            self.client.post(f'/dashboard/users/{user.pk}/toggle/')
            user.refresh_from_db()
            self.assertEqual(user.is_active,active)
        self.client.post(f'/dashboard/users/{user.pk}/delete/')
        self.assertFalse(User.objects.filter(pk=user.pk).exists())

    def test_admin_cannot_delete_disable_or_demote_self(self):
        self.login_admin()
        self.client.post(f'/dashboard/users/{self.admin.pk}/toggle/')
        self.client.post(f'/dashboard/users/{self.admin.pk}/delete/')
        self.client.post(f'/dashboard/users/{self.admin.pk}/edit/',self.user_data(username='manager',email='manager@example.com',role='customer',password='',confirm_password=''))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
        self.assertEqual(self.admin.role,'admin')

    def test_store_admin_cannot_manage_superuser_or_django_admin(self):
        superuser=User.objects.create_superuser(username='root',email='root@example.com',password='Root-Strong-928!')
        self.login_admin()
        for suffix in ['edit/','delete/','toggle/']:
            self.assertEqual(self.client.post(f'/dashboard/users/{superuser.pk}/{suffix}').status_code,403)
        self.assertEqual(self.client.get('/admin/').status_code,302)

    def test_cart_guest_add_update_remove(self):
        self.assertRedirects(self.client.post(reverse('cart_add',args=[self.product.pk]),{'size':'S','quantity':2}),'/cart/')
        key=f'{self.product.pk}:S'
        self.assertEqual(self.client.session['cart'][key]['quantity'],2)
        self.client.post('/cart/update/',{'key':key,'action':'plus'})
        self.assertEqual(self.client.session['cart'][key]['quantity'],3)
        self.client.post('/cart/update/',{'key':key,'action':'minus'})
        self.assertEqual(self.client.session['cart'][key]['quantity'],2)
        self.client.post('/cart/update/',{'key':key,'quantity':4,'action':'update'})
        self.assertEqual(self.client.session['cart'][key]['quantity'],4)
        self.client.post('/cart/update/',{'key':key,'action':'remove'})
        self.assertEqual(self.client.session['cart'],{})

    def test_cart_rejects_invalid_size_quantity_and_aggregate_stock(self):
        for data in [{'size':'BAD','quantity':1},{'size':'S','quantity':-1},{'size':'S','quantity':'abc'},{'size':'S','quantity':6}]:
            self.client.post(reverse('cart_add',args=[self.product.pk]),data)
            self.assertFalse(self.client.session.get('cart',{}))
        self.client.post(reverse('cart_add',args=[self.product.pk]),{'size':'S','quantity':4})
        self.client.post(reverse('cart_add',args=[self.product.pk]),{'size':'M','quantity':2})
        self.assertEqual(sum(x['quantity'] for x in self.client.session['cart'].values()),4)

    def test_hidden_sold_out_products_cannot_be_added(self):
        for product,size in [(self.hidden,'One size'),(self.sold,'L')]:
            self.client.post(reverse('cart_add',args=[product.pk]),{'size':size,'quantity':1})
            self.assertFalse(self.client.session.get('cart',{}))

    def test_deleted_cart_product_is_removed_so_remaining_items_can_checkout(self):
        self.client.post(reverse('cart_add',args=[self.product.pk]),{'size':'S','quantity':1})
        self.product.delete()
        response=self.client.get('/cart/')
        self.assertEqual(response.status_code,200)
        self.assertEqual(self.client.session['cart'],{})

    def test_cart_post_only_and_csrf(self):
        self.assertEqual(self.client.get(reverse('cart_add',args=[self.product.pk])).status_code,405)
        client=Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(reverse('cart_add',args=[self.product.pk]),{'size':'S','quantity':1}).status_code,403)

    def test_checkout_requires_login_preserves_guest_cart(self):
        self.client.post(reverse('cart_add',args=[self.product.pk]),{'size':'S','quantity':1})
        self.assertEqual(self.client.get('/checkout/').status_code,302)
        self.client.post('/accounts/login/',{'username':'alice','password':'Strong-Password-123!'})
        self.assertEqual(len(self.client.session['cart']),1)

    def test_checkout_end_to_end_double_submit_and_clear_cart(self):
        self.client.force_login(self.customer)
        self.client.post(reverse('cart_add',args=[self.product.pk]),{'size':'S','quantity':2})
        self.assertEqual(self.client.get('/checkout/').status_code,200)
        data={**self.shipping(),'checkout_token':self.client.session['checkout_token'],'total':'1','price':'1'}
        response=self.client.post('/checkout/',data)
        order=Order.objects.get(user=self.customer)
        self.assertRedirects(response,reverse('order_success',args=[order.reference]))
        self.assertEqual(order.total,Decimal('1180'))
        self.assertEqual(order.items.get().quantity,2)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock,3)
        self.assertEqual(self.client.session['cart'],{})
        self.assertRedirects(self.client.post('/checkout/',data),reverse('order_success',args=[order.reference]))
        self.assertEqual(Order.objects.count(),1)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock,3)

    def test_stale_checkout_does_not_partially_deduct_stock(self):
        self.client.force_login(self.customer)
        self.client.post(reverse('cart_add',args=[self.product.pk]),{'size':'S','quantity':4})
        self.client.get('/checkout/')
        Product.objects.filter(pk=self.product.pk).update(stock=1)
        response=self.client.post('/checkout/',{**self.shipping(),'checkout_token':self.client.session['checkout_token']})
        self.assertContains(response,'Not enough stock')
        self.assertEqual(Order.objects.count(),0)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock,1)
        self.assertTrue(self.client.session['cart'])

    def test_atomic_rollback_when_second_product_fails(self):
        cart={**self.cart(),**self.cart(quantity=1,size='L',product=self.sold)}
        with self.assertRaises(ValueError):
            place_order(self.customer,cart,self.shipping())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock,5)
        self.assertEqual(Order.objects.count(),0)

    def test_deleted_inactive_or_invalid_item_rejected_at_checkout(self):
        for cart in [self.cart(product=self.hidden,size='One size'),self.cart(size='BAD'),self.cart(quantity=-1),{'missing':{'product_id':999999,'size':'S','quantity':1}}]:
            with self.assertRaises(ValueError):
                place_order(self.customer,cart,self.shipping())
        self.assertEqual(Order.objects.count(),0)

    def test_order_ownership(self):
        order=place_order(self.customer,self.cart(),self.shipping())
        self.client.force_login(self.other)
        for name in ['order_detail','order_success']:
            self.assertEqual(self.client.get(reverse(name,args=[order.reference])).status_code,404)
        self.assertNotContains(self.client.get('/orders/'),order.number)

    def test_cancel_restores_stock_once(self):
        order=place_order(self.customer,self.cart(),self.shipping())
        transition_order(order.pk,'Cancelled')
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock,5)
        with self.assertRaises(ValueError):
            transition_order(order.pk,'Cancelled')
        with self.assertRaises(ValueError):
            transition_order(order.pk,'Pending')
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock,5)

    def test_admin_order_transitions(self):
        order=place_order(self.customer,self.cart(),self.shipping())
        self.login_admin()
        url=reverse('dashboard_order_detail',args=[order.pk])
        self.assertEqual(self.client.get(url).status_code,200)
        for status in ['Confirmed','Shipped','Completed']:
            self.assertRedirects(self.client.post(url,{'status':status}),url)
            order.refresh_from_db()
            self.assertEqual(order.status,status)
        self.client.post(url,{'status':'Cancelled'})
        order.refresh_from_db()
        self.assertEqual(order.status,'Completed')

    def test_order_snapshot_survives_product_user_delete(self):
        order=place_order(self.customer,self.cart(),self.shipping())
        self.product.delete()
        self.customer.delete()
        order.refresh_from_db()
        item=order.items.get()
        self.assertIsNone(order.user)
        self.assertIsNone(item.product)
        self.assertEqual(item.price,Decimal('590'))
        self.assertEqual(item.name,'MAMUDI Everyday Tee')

    def test_database_price_constraint(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Product.objects.filter(pk=self.product.pk).update(price=-1)

    @patch('catalog.management.commands.seed_demo.product_image')
    @patch('catalog.management.commands.seed_demo.hero_image')
    def test_seed_idempotent_preserves_stock_and_account(self,*mocks):
        out=io.StringIO()
        call_command('seed_demo',stdout=out)
        demo=Product.objects.get(slug='mamudi-essential-oversized-tee')
        demo.stock=9
        demo.save()
        customer=User.objects.get(username='customer')
        password=customer.password
        count=Product.objects.count()
        call_command('seed_demo',stdout=out)
        demo.refresh_from_db()
        customer.refresh_from_db()
        self.assertEqual(Product.objects.count(),count)
        self.assertEqual(Category.objects.count(),8)
        self.assertEqual(demo.stock,9)
        self.assertEqual(customer.password,password)
        self.assertEqual(Product.objects.filter(slug__startswith='mamudi-').count(),20)
