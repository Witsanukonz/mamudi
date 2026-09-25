# MAMUDI

เว็บ Demo E-commerce ร้านเสื้อผ้าสำหรับโปรเจกต์รายวิชา ใช้ **Django + Django Templates + Tailwind CSS + Vanilla JavaScript** พร้อมหน้าร้านและ Custom Admin Dashboard

## เริ่มจากโคลน: วิธีง่ายที่สุด

ติดตั้ง [Python 3.12 ขึ้นไป](https://www.python.org/downloads/) และ [Git](https://git-scm.com/downloads) ก่อน บน Windows ให้เลือก **Add Python to PATH** ตอนติดตั้ง Python ตรวจด้วย `python --version` และ `git --version`

เปิด PowerShell หรือ Terminal แล้วรัน:

```powershell
git clone https://github.com/Witsanukonz/mamudi.git
cd mamudi
python setup_demo.py
```

รอให้ขึ้น `MAMUDI is ready` คำสั่งเดียวนี้จะสร้าง `.venv`, ติดตั้ง dependencies, สร้าง `.env`, คัดลอกฐานข้อมูลตัวอย่างเป็น `local.sqlite3`, เตรียมสินค้า/รูปภาพ และตั้งรหัสบัญชี Admin/Customer ให้พร้อมใช้ ต้องใช้อินเทอร์เน็ตตอนดาวน์โหลด dependencies ครั้งแรก

รันเว็บบน Windows โดยไม่ต้อง activate virtual environment:

```powershell
.venv\Scripts\python.exe manage.py runserver
```

บน macOS / Linux ใช้ `python3 setup_demo.py` แล้วรัน:

```bash
.venv/bin/python manage.py runserver
```

- หน้าร้าน: <http://127.0.0.1:8000/>
- เข้าสู่ระบบ: <http://127.0.0.1:8000/accounts/login/>
- Dashboard: <http://127.0.0.1:8000/dashboard/>
- เปิดไฟล์ **DEMO_ACCESS.md** ที่สร้างในโฟลเดอร์โปรเจกต์เพื่อดู Username/Password

แต่ละเครื่องได้รหัสผ่านใหม่ของตัวเอง ไม่มีรหัสผ่าน Admin กลางที่เผยแพร่บน GitHub บัญชี Admin เริ่มต้นชื่อ `admin` ส่วน Customer ชื่อ `customer` ในการติดตั้งครั้งแรก ระบบจะตั้งรหัสของทั้งสองบัญชีในฐานข้อมูลให้ตรงกับ `DEMO_ACCESS.md` โดยอัตโนมัติ

กด `Ctrl+C` ใน terminal เพื่อหยุดเว็บ ครั้งต่อไปใช้คำสั่ง `runserver` ได้เลย ไม่ต้องติดตั้งซ้ำ การรัน `python setup_demo.py` ซ้ำเก็บข้อมูล สต็อก และรหัสผ่านเดิมไว้

> GitHub เก็บซอร์สโค้ดของโปรเจกต์ หลัง clone ต้องรัน Django ตามด้านบนจึงจะเปิดเว็บได้

## เว็บออนไลน์บน Vercel

- หน้าร้าน Production: <https://mamudi.vercel.app/>
- Admin Dashboard: <https://mamudi.vercel.app/dashboard/>
- Source code: <https://github.com/Witsanukonz/mamudi>

Production ใช้ Django บน Vercel, Neon PostgreSQL สำหรับบัญชี/สินค้า/ออเดอร์ และ Vercel Blob สำหรับรูปที่อัปโหลดผ่าน Dashboard ข้อมูลจึงไม่ผูกกับไฟล์ SQLite หรือ filesystem ชั่วคราวของ serverless ส่วน local หลัง clone ยังใช้ SQLite และ `media/` ตามขั้นตอนปกติ

รหัส Production อยู่ใน `VERCEL_ACCESS.md` เฉพาะเครื่องที่ deploy และไฟล์นี้ถูก `.gitignore` ไว้ ไม่ถูกส่งขึ้น GitHub เมื่อต้องการอัปเดตเว็บหลังแก้โค้ดและทดสอบแล้ว ให้ push GitHub และรันจากโฟลเดอร์โปรเจกต์ที่ link กับ Vercel:

```powershell
npx vercel@59.19.0 --prod
```

## ติดตั้งเองทีละขั้นตอน (ทางเลือก)

หลัง clone และ `cd mamudi` แล้ว ถ้าต้องการกำหนดบัญชีหรือค่า `.env` เอง:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
```

เปิด `.env` เปลี่ยน `SECRET_KEY` และเอา `#` หน้าบรรทัด `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `DEMO_CUSTOMER_PASSWORD` ออก แล้วใส่ค่าที่ต้องการ รหัสผ่านควรมีอย่างน้อย 8 ตัวอักษรและไม่เหมือน Username จากนั้น:

```powershell
python manage.py migrate
python manage.py seed_demo
python manage.py create_store_admin --noinput
python manage.py runserver
```

สร้าง Admin แบบกรอกข้อมูลใน terminal ได้ด้วย `python manage.py create_store_admin` ระบบเก็บรหัสผ่านด้วย Django password hashing และไม่ให้คำสั่งนี้เปลี่ยนบัญชีเดิมโดยอัตโนมัติ

มี migration files อยู่ใน repository แล้ว ตอนติดตั้งให้ใช้ `migrate` ได้เลย ใช้ `makemigrations` เฉพาะเมื่อแก้โครงสร้าง models

ถ้าเลือกติดตั้งเอง ไฟล์ `DEMO_ACCESS.md` จะไม่ได้ถูกสร้างโดยอัตโนมัติ ให้ใช้รหัสผ่านที่กำหนดใน `.env` หรือที่กรอกใน terminal

ถ้าไม่ได้ตั้ง `DEMO_CUSTOMER_PASSWORD` จะสร้าง `customer` ที่ยังล็อกอินด้วยรหัสผ่านไม่ได้ ตั้งรหัสผ่านด้วย:

```powershell
python manage.py changepassword customer
```

## เปิดครั้งต่อไปและแก้ปัญหาที่พบบ่อย

| อาการ | วิธีแก้ |
| --- | --- |
| `python` ไม่พบคำสั่ง | ติดตั้ง Python พร้อม Add to PATH แล้วเปิด terminal ใหม่ หรือใช้ `py` บน Windows / `python3` บน macOS/Linux |
| PowerShell ไม่อนุญาตให้ activate | ใช้ `.venv\Scripts\python.exe manage.py runserver` โดยตรง |
| `No module named django` | เรียก Python ใน `.venv` ตามคำสั่งด้านบน หรือรัน `python setup_demo.py` อีกครั้ง |
| Linux สร้าง venv ไม่ได้ | บน Ubuntu/Debian ติดตั้ง `sudo apt install python3-venv` แล้วรัน setup ใหม่ |
| พอร์ต 8000 ถูกใช้งาน | รัน `.venv\Scripts\python.exe manage.py runserver 8001` แล้วเปิด <http://127.0.0.1:8001/> |
| ลืมรหัส Admin | รัน `.venv\Scripts\python.exe manage.py changepassword admin` |
| ไม่มีสินค้า/รูปหลังติดตั้งเอง | รัน `.venv\Scripts\python.exe manage.py seed_demo` |

คำสั่ง `changepassword` เปลี่ยนรหัสในฐานข้อมูล ให้ใช้รหัสที่ตั้งล่าสุด แม้ไฟล์ `DEMO_ACCESS.md` ยังแสดงรหัสที่สร้างครั้งแรกอยู่

## ไฟล์ที่ GitHub ไม่เก็บ

`.env`, `DEMO_ACCESS.md`, `local.sqlite3`, `media/`, `.venv/`, `node_modules/` และ logs เป็นข้อมูลเฉพาะเครื่อง จึงถูกยกเว้นใน `.gitignore` ส่วน `db.sqlite3` เป็นฐานข้อมูลตัวอย่างต้นฉบับที่เก็บไว้ใน repository เพื่อให้ข้อมูลโปรเจกต์ติดไปกับการ clone โดย `setup_demo.py` จะคัดลอกเป็นฐานข้อมูลเฉพาะเครื่องก่อนอัปเดตโครงสร้างและตั้งรหัส Demo ให้พร้อมใช้

## ฟีเจอร์

### หน้าร้าน

- Home: Hero, New Arrivals, 8 Categories, Best Sellers
- Shop: ค้นหาชื่อ/คำอธิบาย/สี กรอง Category, Gender, Price, Size, Availability และเรียงลำดับ พร้อมแบ่งหน้า
- รายละเอียดสินค้า: รูป สี เพศ ไซซ์ สต็อก จำนวน และ Add to Bag
- Cart แบบ Django session ใช้ได้ก่อน Login และยังอยู่หลัง Login
- Checkout ต้อง Login มีชื่อ เบอร์โทร ที่อยู่ จังหวัด รหัสไปรษณีย์ ไม่มีการชำระเงินจริง
- สร้าง Order/OrderItem ลดสต็อก ล้างตะกร้า และแสดง Order Success
- Register, Login, Logout แบบ POST, Reset Password, แก้ Profile และ My Orders

### Dashboard

- สถิติ Products, Users, Orders, Pending Orders และ Low Stock (สต็อกไม่เกิน 5)
- Products: ดู เพิ่ม แก้ไข ลบ อัปโหลดรูป จัดการสต็อก และเปิด/ปิดการแสดงสินค้า
- Categories: เพิ่ม แก้ไข ลบ โดยห้ามลบหมวดที่ยังมีสินค้า
- Users: ดู เพิ่ม แก้ไข Role/ข้อมูล/รหัสผ่าน เปิด/ปิด และลบ
- Orders: ดูรายละเอียด ที่อยู่ รายการสินค้า และเปลี่ยนสถานะ
- หน้า Add Product มี TextField, RadioButton, TextArea, CheckBox, DropdownList, DatePicker, FileBrowse ครบ พร้อม Image Preview

Admin ใช้ `/dashboard/` ได้ทั้งหมด บัญชีที่ `role=admin` **ไม่จำเป็นต้องเป็น Django staff** ส่วน `/admin/` จำกัดให้ Superuser เท่านั้น สร้างได้ด้วย `python manage.py createsuperuser` สำหรับ Debug

## ข้อมูลและรูปตัวอย่าง

`python manage.py seed_demo` สร้าง 8 หมวดหมู่และสินค้า MAMUDI ทั้ง 20 รายการตามโจทย์ ราคา สี ไซซ์ และสต็อกตรงกับรายการที่ให้มา

- รัน `seed_demo` ซ้ำไม่เพิ่มข้อมูลซ้ำ และไม่รีเซ็ตสต็อก ชื่อสินค้า ราคา หรือรหัสผ่านเดิม (`setup_demo.py` จะตั้งรหัส Demo จากไฟล์เฉพาะเครื่องในรอบแรกเท่านั้น)
- รูปสินค้าเป็น **ภาพประกอบ placeholder ที่สร้างเองด้วย Pillow** ไม่ใช่ภาพถ่ายสินค้า ไม่มีภาพหรือโลโก้แบรนด์อื่น
- รูปอยู่ใน `media/products/` และ hero อยู่ที่ `static/images/hero.jpg`
- สินค้าที่สร้างโดยไม่อัปโหลดรูปใช้ `static/images/product-placeholder.svg` เพื่อไม่ให้มีรูปหาย
- อัปโหลดได้เฉพาะ JPEG, PNG, WebP ขนาดไม่เกิน 5 MB ตรวจชนิดภาพจริงฝั่งเซิร์ฟเวอร์
- เปลี่ยนเป็นภาพถ่ายผ่าน Dashboard ได้ทันที

## กติกาการซื้อและสิทธิ์

- ไม่มี Product Variants ซับซ้อน ไซซ์เก็บเป็น JSON list และใช้สต็อกร่วมกันทั้งสินค้า
- ตะกร้าแยกบรรทัดตามสินค้าและไซซ์ แต่รวมจำนวนทุกไซซ์เพื่อตรวจสต็อก
- Checkout อ่านราคาและสต็อกจากฐานข้อมูลเสมอ ไม่เชื่อราคาจากฟอร์ม
- ใช้ `transaction.atomic()` และ conditional stock update ป้องกันการตัดสต็อกบางส่วนและสต็อกติดลบ
- ใช้ UUID token ต่อ checkout และ unique constraint ป้องกันสร้างคำสั่งซื้อซ้ำจากการกดส่งซ้ำ
- การลบสินค้า/ผู้ใช้ไม่ลบ Order History รายการสั่งซื้อเก็บ snapshot ชื่อ ราคา สี ไซซ์ จำนวน
- Customer ดูได้เฉพาะคำสั่งซื้อของตัวเองและเข้า Dashboard ไม่ได้
- Admin ไม่สามารถลบ ปิด หรือถอนสิทธิ์ตัวเอง และ Admin ทั่วไปจัดการ Superuser ไม่ได้
- ทุกการแก้ข้อมูลใช้ POST และ CSRF token

สถานะคำสั่งซื้อ:

```text
Pending -> Confirmed -> Shipped -> Completed
   |           |
   +-----------+----> Cancelled (คืนสต็อกครั้งเดียว)
```

คำสั่งซื้อที่ Shipped/Completed/Cancelled แล้วไม่สามารถย้อนสถานะได้

## Reset Password

ค่าเริ่มต้นใช้ Django console email backend สำหรับ Demo เมื่อกรอกอีเมลบัญชีที่มีอยู่ ลิงก์รีเซ็ตจะแสดงใน terminal ที่รัน `runserver` ให้นำ URL ไปเปิดในเบราว์เซอร์

ถ้าเปิดเซิร์ฟเวอร์แบบเบื้องหลังในเครื่องนี้ ลิงก์จะอยู่ใน `server-output.log` ใช้ลิงก์เพื่อเปลี่ยนรหัสผ่านและอย่าเผยแพร่ log

ส่งอีเมลจริงได้โดยตั้ง `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` ใน `.env` ยังไม่ได้ทดสอบ SMTP จริง

## CSS และ JavaScript

Tailwind ถูก compile เป็น `static/css/tailwind.css` และมีไฟล์ CSS พร้อมแล้ว ไม่ต้องใช้ Node.js หรืออินเทอร์เน็ตขณะเปิด Demo

เมื่อแก้ utility classes ใน templates ให้ build ใหม่:

```powershell
npm ci
npm run build:css
```

`static/css/site.css` เป็นสไตล์ MAMUDI และ responsive layout ส่วน `static/js/site.js` จัดการเมนูมือถือ พรีวิวรูป และป้องกันกด Place Order ซ้ำฝั่ง UI

## ทดสอบ

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

ชุดทดสอบใช้ฐานข้อมูลชั่วคราวและ temporary media ไม่แก้ข้อมูล Demo ครอบคลุม:

- หน้า Home/Shop/Detail/Auth/Dashboard และฟอร์มทั้ง 7 ประเภท
- Search, Filters, Sorting, Hidden Products และ Out of Stock
- Register, Email uniqueness, Login/Logout, Profile, Password Reset
- Permission, CSRF, Superuser protection และ self lockout protection
- Product/User/Category CRUD และการอัปโหลดภาพ
- Guest Cart, Quantity, Size และสต็อกรวมหลายไซซ์
- Checkout, Order History, Ownership, Stock deduction, Rollback, Double submit
- การยกเลิกคืนสต็อกครั้งเดียว และ snapshot หลังลบสินค้า/ผู้ใช้
- Seed ซ้ำโดยไม่รีเซ็ตข้อมูล

ตรวจเบราว์เซอร์จริงด้วย `agent-browser` หลังเปิดเซิร์ฟเวอร์:

```powershell
python scripts/browser_verify.py --browser "C:\path\to\agent-browser.exe"
```

สคริปต์นี้ต้องมี Admin/Customer ตาม `.env` จะลองใช้หน้าจอจริงที่ 375, 390, 768, 1280 px สร้าง/ลบข้อมูลตรวจสอบชั่วคราว และเหลือหนึ่งคำสั่งซื้อ Demo ที่ยกเลิกพร้อมคืนสต็อกไว้เป็นหลักฐาน ผลอยู่ใน `artifacts/browser-report.json` และภาพหน้าจอใน `artifacts/`

## โครงสร้าง

```text
mamudi/       settings, URL routes, WSGI
accounts/     custom User, authentication, profile, create_store_admin
catalog/      Category, Product, shop, seed_demo, original image generator
orders/       session cart, checkout, orders, transactional business logic
dashboard/    custom admin permissions, forms, CRUD views
templates/    Django templates ของหน้าร้านและ Dashboard
static/       compiled Tailwind, brand CSS, JavaScript, fallback image, hero
media/        รูปที่ seed และอัปโหลด
tests/        Django integration tests
scripts/      live browser acceptance test
setup_demo.py  ติดตั้ง Demo ครบในคำสั่งเดียวหลัง clone
```

## PostgreSQL และการนำขึ้นเซิร์ฟเวอร์

Local ใช้ SQLite โดยอัตโนมัติ ส่วน Production ใช้ `DATABASE_URL` จาก Neon และมี PostgreSQL driver ใน `requirements.txt` แล้ว การเปลี่ยน URL **ไม่ย้ายข้อมูล SQLite ให้อัตโนมัติ** ต้องรัน `python manage.py migrate`, `seed_demo` และ `create_store_admin --noinput` กับฐานข้อมูลปลายทาง

Vercel อ่าน `DJANGO_SECRET_KEY`, `DATABASE_URL` และ `BLOB_READ_WRITE_TOKEN` จาก Environment Variables โดยไม่เก็บค่าเหล่านี้ใน Git ตัวโปรเจกต์เลือก Django framework และ region สิงคโปร์ผ่าน `vercel.json` พร้อมล็อก Python ใน `pyproject.toml`/`.python-version`
