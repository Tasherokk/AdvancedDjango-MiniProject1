import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sales_and_trading.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

SUPERUSER_EMAIL = "admin@kbtu.kz"
SUPERUSER_USERNAME = "admin"
SUPERUSER_PASSWORD = "admin"

if not User.objects.filter(username=SUPERUSER_USERNAME).exists():
    User.objects.create_superuser(
        username=SUPERUSER_USERNAME,
        email=SUPERUSER_EMAIL,
        password=SUPERUSER_PASSWORD
    )
    print(f"Superuser {SUPERUSER_USERNAME} created successfully!")
else:
    print(f"Superuser {SUPERUSER_USERNAME} already exists.")
