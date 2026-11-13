from django.contrib import admin
from .models import Product, Sale


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('barcode', 'name', 'variant', 'quantity', 'price', 'discounted_price', 'updated_at')
    search_fields = ('barcode', 'name', 'variant')


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity_sold', 'unit_price', 'total_amount', 'sold_at')
    list_filter = ('sold_at',)
