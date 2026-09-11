"""Live browser acceptance test. Requires running local server and agent-browser CLI.

Uses the local demo customer/admin from .env. Creates then removes a test
category, product and user, and leaves one cancelled demo order as evidence.
"""
import argparse
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

BASE=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(BASE))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','mamudi.settings')
import django
django.setup()
from accounts.models import User
from catalog.models import Category, Product
from orders.models import Order

parser=argparse.ArgumentParser()
parser.add_argument('--browser',required=True,help='Path to agent-browser executable')
args=parser.parse_args()
ARTIFACTS=BASE/'artifacts'
ARTIFACTS.mkdir(exist_ok=True)
report={'pages':[],'flows':[],'errors':[]}


def browser(*command):
    process=subprocess.run([args.browser,'--json',*map(str,command)],capture_output=True,text=True,encoding='utf-8',timeout=40)
    try:
        data=json.loads(process.stdout)
    except ValueError:
        raise AssertionError(f'Browser command failed: {command[0]}: {process.stderr[:300]}')
    if not data.get('success'):
        raise AssertionError(f'Browser command failed: {command[0]}: {data.get("error")}')
    return data.get('data',{})


def evaluate(script):
    return browser('eval',script).get('result')


def navigate(path):
    browser('open','http://127.0.0.1:8000'+path)


def fill(selector,value):
    if selector == '#id_release_date':
        # Chromium date inputs need an ISO value; simulated text typing varies by locale.
        evaluate('''(()=>{const input=document.querySelector('#id_release_date');
          input.value='''+json.dumps(value)+''';
          input.dispatchEvent(new Event('input',{bubbles:true}));
          input.dispatchEvent(new Event('change',{bubbles:true}));
          return input.checkValidity();})()''')
    else:
        browser('fill',selector,value)


def click(selector):
    browser('click',selector)
    browser('wait','--load','networkidle')


def url_contains(value):
    path=evaluate('location.pathname')
    assert value in path, f'Expected {value}, got {path}'


def check_page(label,width):
    result=evaluate('''(async()=>{
      const imgs=[...document.images];
      imgs.forEach(i=>i.loading='eager');
      await Promise.all(imgs.map(i=>i.decode().catch(()=>null)));
      return {path:location.pathname,width:innerWidth,scrollWidth:document.documentElement.scrollWidth,
        broken:imgs.filter(i=>!i.naturalWidth).map(i=>i.src),
        textLength:document.body.innerText.trim().length,
        title:document.title};
    })()''')
    assert result['width']==result['scrollWidth'], f'Horizontal overflow: {label} at {width}: {result}'
    assert not result['broken'], f'Broken images: {label}: {result["broken"]}'
    assert result['textLength']>100, f'Blank page: {label}'
    assert 'Error at' not in result['title']
    report['pages'].append(result)


def login(username,password):
    navigate('/accounts/login/')
    fill('#id_username',username)
    fill('#id_password',password)
    click('.auth-panel button[type="submit"], .auth-panel form button')
    assert evaluate('location.pathname')=='/'


def logout():
    # Expose the real account menu and submit its CSRF-protected form.
    navigate('/')
    click('.account-menu summary')
    click('.account-menu form button')


def screenshot(name):
    browser('screenshot',str(ARTIFACTS/name))


def flow(name):
    report['flows'].append(name)
    print(f'PASS: {name}',flush=True)


try:
    browser('cookies','clear')
    product=Product.objects.get(slug='mamudi-essential-oversized-tee')
    for width in [375,390,768,1280]:
        browser('set','viewport',width,900)
        for path in ['/', '/products/', '/products/?page=2',product.get_absolute_url(),'/cart/','/accounts/login/','/accounts/register/']:
            navigate(path)
            check_page(path,width)
        print(f'PASS: public pages at {width}px',flush=True)
    browser('set','viewport',390,844)
    navigate('/')
    click('[data-menu-toggle]')
    assert evaluate('document.querySelector("#mobile-menu").hidden') is False
    click('#mobile-menu a[href="/products/"]')
    url_contains('/products/')
    flow('Mobile navigation')
    fill('input[name="q"]','Hoodie')
    browser('select','select[name="category"]','hoodies')
    browser('select','select[name="size"]','M')
    click('.filter-row button')
    assert evaluate('document.querySelectorAll(".product-card").length')==3
    check_page('Filtered shop',390)
    screenshot('shop-mobile.png')
    flow('Search, category and size filters through UI')

    marker=uuid.uuid4().hex[:8]
    member_name=f'browser_{marker}'
    member_password=f'Demo-Check-{marker}-Password!'
    navigate('/accounts/register/')
    for field,value in {'username':member_name,'email':f'{member_name}@mamudi.example','first_name':'Browser','last_name':'Check','password1':member_password,'password2':member_password}.items():
        fill('#id_'+field,value)
    click('.auth-panel form button')
    assert User.objects.filter(username=member_name,role='customer').exists()
    navigate('/accounts/profile/')
    fill('#id_first_name','Verified')
    click('.auth-panel form button')
    assert User.objects.get(username=member_name).first_name=='Verified'
    flow('Register and edit customer profile')
    logout()

    login('customer',os.environ['DEMO_CUSTOMER_PASSWORD'])
    stock_before=product.stock
    navigate(product.get_absolute_url())
    browser('check','input[name="size"][value="M"]')
    fill('input[name="quantity"]','2')
    click('.purchase-form button')
    url_contains('/cart/')
    click('.quantity-control button[value="plus"]')
    assert evaluate('document.querySelector(".quantity-control input[name=quantity]").value')=='3'
    click('.quantity-control button[value="minus"]')
    assert evaluate('document.querySelector(".quantity-control input[name=quantity]").value')=='2'
    check_page('Populated cart',390)
    screenshot('cart-mobile.png')
    click('a[href="/checkout/"]')
    for field,value in {'full_name':'Demo Customer','phone':'0812345678','address':'123 Demo Road','province':'Bangkok','postal_code':'10110'}.items():
        fill('#id_'+field,value)
    check_page('Checkout',390)
    click('[data-submit-once]')
    url_contains('/success/')
    order=Order.objects.filter(user__username='customer').first()
    assert order is not None
    assert order.items.get().quantity==2
    product.refresh_from_db()
    assert product.stock==stock_before-2
    assert evaluate('document.querySelector(".bag-count").textContent')=='0'
    check_page('Order success',390)
    screenshot('order-success-mobile.png')
    navigate('/orders/')
    assert order.number in evaluate('document.body.innerText')
    flow('Login, add to cart, change quantity, checkout, stock deduction and order history')
    logout()

    login(os.environ['ADMIN_USERNAME'],os.environ['ADMIN_PASSWORD'])
    for width in [375,390,768,1280]:
        browser('set','viewport',width,900)
        for path in ['/dashboard/','/dashboard/products/','/dashboard/products/add/','/dashboard/categories/','/dashboard/users/','/dashboard/users/add/','/dashboard/orders/',f'/dashboard/orders/{order.pk}/']:
            navigate(path)
            check_page(path,width)
        print(f'PASS: Dashboard pages at {width}px',flush=True)
    navigate('/dashboard/')
    screenshot('dashboard-desktop.png')

    navigate('/dashboard/categories/add/')
    fill('#id_name','Browser Check Category '+marker)
    fill('#id_description','Temporary browser acceptance check')
    click('.form-panel form button')
    category=Category.objects.get(name='Browser Check Category '+marker)
    navigate(f'/dashboard/categories/{category.pk}/edit/')
    fill('#id_description','Updated through the browser')
    click('.form-panel form button')
    category.refresh_from_db()
    assert category.description=='Updated through the browser'
    flow('Category create and edit')

    navigate('/dashboard/products/add/')
    for field,value in {'name':'MAMUDI Browser Check '+marker,'description':'Created by live browser verification','price':'795.50','stock':'7','color':'Black','release_date':'2026-09-11'}.items():
        fill('#id_'+field,value)
    browser('select','#id_category',category.pk)
    browser('check','#id_sizes_1')
    browser('check','input[name="gender"][value="Unisex"]')
    browser('upload','#id_image',str(product.image.path))
    assert evaluate('document.querySelector("[data-image-preview]").src.startsWith("blob:")')
    screenshot('product-form-desktop.png')
    click('.form-panel form button')
    created_product=Product.objects.get(name='MAMUDI Browser Check '+marker)
    assert Path(created_product.image.path).exists()
    navigate(f'/dashboard/products/{created_product.pk}/edit/')
    fill('#id_stock','9')
    click('.form-panel form button')
    created_product.refresh_from_db()
    assert created_product.stock==9
    navigate(f'/dashboard/products/{created_product.pk}/delete/')
    click('.button-danger')
    assert not Product.objects.filter(pk=created_product.pk).exists()
    navigate(f'/dashboard/categories/{category.pk}/delete/')
    click('.button-danger')
    assert not Category.objects.filter(pk=category.pk).exists()
    flow('Product create, image preview/upload, edit, delete; category delete')

    member=User.objects.get(username=member_name)
    navigate(f'/dashboard/users/{member.pk}/edit/')
    fill('#id_last_name','Verified Admin Edit')
    click('.form-panel form button')
    member.refresh_from_db()
    assert member.last_name=='Verified Admin Edit'
    assert member.check_password(member_password)
    navigate('/dashboard/users/?q='+member_name)
    click('.table-actions form button')
    member.refresh_from_db()
    assert not member.is_active
    navigate('/dashboard/users/?q='+member_name)
    click('.table-actions form button')
    member.refresh_from_db()
    assert member.is_active
    navigate(f'/dashboard/users/{member.pk}/delete/')
    click('.button-danger')
    assert not User.objects.filter(pk=member.pk).exists()
    flow('User edit preserving password, disable, enable and delete')

    navigate(f'/dashboard/orders/{order.pk}/')
    browser('select','select[name="status"]','Confirmed')
    click('.status-form button')
    order.refresh_from_db()
    assert order.status=='Confirmed'
    browser('select','select[name="status"]','Cancelled')
    click('.status-form button')
    order.refresh_from_db()
    product.refresh_from_db()
    assert order.status=='Cancelled' and product.stock==stock_before
    flow('Admin confirms and cancels order; stock restored')
    report['demo_order']=order.number

    errors=browser('errors').get('errors',[])
    logs=browser('console').get('messages',[])
    assert not errors, errors
    report['errors']=errors
    report['console']=logs
    browser('set','viewport',1280,900)
    navigate('/dashboard/')
    screenshot('dashboard-desktop.png')
    logout()
    navigate('/')
    screenshot('home-desktop.png')
    browser('set','viewport',390,844)
    screenshot('home-mobile.png')
    report['result']='PASS'
finally:
    (ARTIFACTS/'browser-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Browser acceptance passed: {len(report["pages"])} page/viewport checks, {len(report["flows"])} flows.',flush=True)
