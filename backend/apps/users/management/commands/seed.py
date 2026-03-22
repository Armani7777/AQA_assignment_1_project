import random
from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.orders.models import Coupon, Order, OrderItem
from apps.products.models import Category, Product
from apps.reviews.models import Review
from apps.users.models import CustomUser


class Command(BaseCommand):
    help = "Seed marketplace demo data."

    def handle(self, *args, **options):
        users = self.seed_users()
        categories = self.seed_categories()
        products = self.seed_products(users, categories)
        self.seed_coupons()
        self.seed_orders(users, products)
        self.seed_reviews(users, products)
        self.stdout.write(self.style.SUCCESS("Seed completed."))

    def seed_users(self):
        definitions = [
            ("admin", "admin@marketplace.com", "Admin123!", True, True, False),
            ("seller1", "seller1@test.com", "Test123!", False, False, True),
            ("seller2", "seller2@test.com", "Test123!", False, False, True),
            ("seller3", "seller3@test.com", "Test123!", False, False, True),
        ]
        for i in range(1, 7):
            definitions.append((f"buyer{i}", f"buyer{i}@test.com", "Test123!", False, False, False))
        users = {}
        for username, email, password, is_staff, is_superuser, is_seller in definitions:
            user, created = CustomUser.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "is_staff": is_staff,
                    "is_superuser": is_superuser,
                    "is_seller": is_seller,
                    "full_name": username.title(),
                },
            )
            if created or not user.check_password(password):
                user.set_password(password)
            user.email = email
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.is_seller = is_seller
            user.save()
            users[username] = user
        return users

    def seed_categories(self):
        definitions = [
            ("Electronics", "electronics"),
            ("Clothing", "clothing"),
            ("Books", "books"),
            ("Home & Garden", "home-garden"),
            ("Sports", "sports"),
            ("Toys", "toys"),
        ]
        categories = {}
        for name, slug in definitions:
            categories[name], _ = Category.objects.get_or_create(name=name, defaults={"slug": slug})
            if categories[name].slug != slug:
                categories[name].slug = slug
                categories[name].save(update_fields=["slug"])
        return categories

    def seed_products(self, users, categories):
        catalog = {
            "Electronics": [("iPhone 15 Pro", "999.99", 50), ("Samsung Galaxy S24", "799.99", 30), ("MacBook Air M2", "1299.99", 20), ("Sony WH-1000XM5 Headphones", "349.99", 100), ("iPad Pro 12.9", "1099.99", 40)],
            "Clothing": [("Classic White T-Shirt", "19.99", 200), ("Slim Fit Jeans", "49.99", 150), ("Winter Jacket", "129.99", 80), ("Running Sneakers", "89.99", 120), ("Formal Suit", "299.99", 30)],
            "Books": [("Clean Code by Robert Martin", "39.99", 500), ("The Pragmatic Programmer", "44.99", 400), ("Design Patterns", "54.99", 300), ("Python Crash Course", "34.99", 600), ("JavaScript: The Good Parts", "29.99", 450)],
            "Home & Garden": [("Coffee Maker Deluxe", "79.99", 60), ("Robot Vacuum Cleaner", "299.99", 25), ("Air Purifier HEPA", "149.99", 40), ("Instant Pot 7-in-1", "89.99", 70), ("Memory Foam Pillow", "49.99", 200)],
            "Sports": [("Yoga Mat Premium", "39.99", 150), ("Resistance Bands Set", "24.99", 300), ("Adjustable Dumbbells", "199.99", 35), ("Running Shoes Pro", "119.99", 80), ("Cycling Helmet", "69.99", 90)],
            "Toys": [("LEGO Creator Set", "59.99", 100), ("Remote Control Car", "49.99", 75), ("Educational Robot Kit", "89.99", 45), ("Board Game Strategy", "34.99", 120), ("Wooden Puzzle 1000pc", "24.99", 200)],
        }
        sellers = [users["seller1"], users["seller2"], users["seller3"]]
        products = []
        seller_idx = 0
        for category_name, items in catalog.items():
            for title, price, stock in items:
                seller = sellers[seller_idx % len(sellers)]
                seller_idx += 1
                # Deterministic placeholder: blue background (#3B82F6), white text with product title
                text = title.replace(" ", "+")
                image_url = f"https://dummyimage.com/600x400/3B82F6/ffffff&text={text}"
                product, _ = Product.objects.get_or_create(
                    title=title,
                    defaults={
                        "description": f"{title} description for QA testing.",
                        "price": Decimal(price),
                        "stock": stock,
                        "seller": seller,
                        "category": categories[category_name],
                        "image_url": image_url,
                    },
                )
                # Backfill image_url if missing on existing records
                if not product.image_url:
                    product.image_url = image_url
                    product.save(update_fields=["image_url"])
                products.append(product)
        return products

    def seed_coupons(self):
        for code, percent in [("SAVE10", 10), ("SAVE25", 25), ("HALFOFF", 50)]:
            Coupon.objects.get_or_create(code=code, defaults={"discount_percent": percent, "is_active": True})

    def seed_orders(self, users, products):
        if Order.objects.count() >= 10:
            return
        buyers = [users[f"buyer{i}"] for i in range(1, 7)]
        statuses = ["delivered"] * 3 + ["shipped"] * 2 + ["confirmed"] * 2 + ["pending"] * 2 + ["cancelled"]
        for idx, status in enumerate(statuses):
            buyer = buyers[idx % len(buyers)]
            chosen = random.sample(products, 2)
            subtotal = chosen[0].price + chosen[1].price
            order = Order.objects.create(
                user=buyer,
                status=status,
                total_price=subtotal,
                shipping_address=f"Test address #{idx + 1}, QA city",
            )
            for product in chosen:
                OrderItem.objects.create(order=order, product=product, quantity=1, price=product.price)

    def seed_reviews(self, users, products):
        if Review.objects.count() >= 20:
            return
        buyers = [users[f"buyer{i}"] for i in range(1, 7)]
        attempts = 0
        while Review.objects.count() < 20 and attempts < 200:
            attempts += 1
            user = random.choice(buyers)
            product = random.choice(products)
            Review.objects.get_or_create(
                product=product,
                user=user,
                defaults={
                    "rating": random.randint(1, 5),
                    "comment": "Great product for testing marketplace reviews.",
                },
            )
