from django.contrib import admin
from .models import Product, ProductVariant, Sale


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('barcode', 'name', 'category', 'price', 'updated_at')
    search_fields = ('barcode', 'name')
    inlines = [ProductVariantInline]


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('product', 'variant_name', 'quantity_sold', 'unit_price', 'total_amount', 'sold_at')
    list_filter = ('sold_at',)
