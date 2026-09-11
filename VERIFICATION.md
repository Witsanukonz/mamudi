# MAMUDI verification

Verified locally on 11 September 2026 with Python 3.14, Django 5.2.17, SQLite and headless Google Chrome.

| Check | Result |
| --- | --- |
| Initial migrations | Applied successfully |
| `python manage.py check` | No issues |
| `python manage.py makemigrations --check --dry-run` | No changes detected |
| `python manage.py test` | 36 tests passed |
| `npm run build:css` | Tailwind compiled successfully |
| Repeated `seed_demo` | No duplicates, existing stock preserved |
| Browser page/viewport checks | 64 passed at 375, 390, 768 and 1280 px |
| Page width and images | No horizontal page overflow or missing images |
| Browser JavaScript errors / console | No errors recorded |
| Links from customer/admin pages | 144 route checks, no failures |
| Static/media assets | 26 asset URLs returned HTTP 200 |
| Form action URLs | 23 action URLs resolved |
| Final seed data | 20 products, 8 categories, exact prices/colors/sizes/stock |
| Final demo accounts | Admin and Customer, temporary accounts removed |

Live browser workflows exercised:

- Mobile menu, search, category and size filters.
- Register, login, logout and profile update.
- Product size selection, add to cart, increase/decrease quantity.
- Checkout, saved order items, actual stock deduction, empty cart and order history.
- Dashboard page navigation at all four viewport widths.
- Category create/edit/delete.
- Product create/edit/delete with local image upload and visible preview.
- User create/edit, password hashing and preservation, disable/enable/delete.
- Order confirmation and cancellation, with stock restored.

Order **MM-00001** remains as a cancelled demo order for the sample customer. Stock has been verified against all 20 original seed definitions after cancellation.

Machine-readable reports and reviewed screenshots:

- `artifacts/browser-report.json`
- `artifacts/link-report.json`
- `artifacts/home-desktop.png`
- `artifacts/home-mobile.png`
- `artifacts/shop-mobile.png`
- `artifacts/cart-mobile.png`
- `artifacts/order-success-mobile.png`
- `artifacts/dashboard-desktop.png`
- `artifacts/product-form-desktop.png`

The initial browser driver attempt raced form completion and its date typing depended on browser locale. The verification script now waits for form navigation and sets date inputs using ISO format. The affected workflows were resumed and passed. These were verification-driver fixes; Django's submitted date validation and password behavior are covered by the integration tests.

Product visuals are original generated placeholders, not product photography. Password reset was tested with Django's test email backend; the local demo uses console email. Real SMTP, PostgreSQL, production hosting and real payments were not exercised.
