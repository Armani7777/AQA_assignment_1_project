from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.users.urls")),
    path("api/users/", include("apps.users.urls_profile")),
    path("api/products/", include("apps.products.urls_products")),
    path("api/categories/", include("apps.products.urls_categories")),
    path("api/cart/", include("apps.products.urls_cart")),
    path("api/orders/", include("apps.orders.urls")),
    path("api/reviews/", include("apps.reviews.urls")),
    path("api/coupons/", include("apps.orders.urls_coupons")),
]
