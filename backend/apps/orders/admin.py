from django.contrib import admin

from .models import Coupon, Order, OrderItem

admin.site.register(Coupon)
admin.site.register(Order)
admin.site.register(OrderItem)
