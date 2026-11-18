import os
import re
from decimal import Decimal
import pandas as pd
from django.contrib import admin, messages
from django.db import transaction
from django.shortcuts import render, redirect
from django.urls import path
from .models import Product, ProductVariant, Sale, SalesOrder, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('icon', 'name', 'slug', 'product_count', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

    def product_count(self, obj):
        return f"{obj.product_count} products"
    product_count.short_description = "Products"
from .views import detect_category


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    change_list_template = "admin/inventory/product/change_list.html"
    list_display = ('barcode', 'name', 'category', 'price', 'total_stock', 'updated_at')
    search_fields = ('barcode', 'name', 'variant')
    list_filter = ('category',)
    inlines = [ProductVariantInline]

    def total_stock(self, obj):
        return f"{obj.total_stock} pcs"
    total_stock.short_description = "Stock"

    def delete_model(self, request, obj):
        with transaction.atomic():
            obj.variants.all().delete()
            obj.sales.all().delete()
            obj.delete()

    def delete_queryset(self, request, queryset):
        with transaction.atomic():
            for obj in queryset:
                obj.variants.all().delete()
                obj.sales.all().delete()
                obj.delete()

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-excel/', self.admin_site.admin_view(self.import_excel_view), name='product_import_excel'),
        ]
        return custom_urls + urls

    def import_excel_view(self, request):
        if request.method == 'POST':
            file = request.FILES.get('file')
            if not file:
                self.message_user(request, "Please choose an Excel (.xlsx, .xls) or CSV file.", level=messages.ERROR)
                return redirect('admin:product_import_excel')

            filename = file.name.lower()
            if not (filename.endswith('.csv') or filename.endswith('.xlsx') or filename.endswith('.xls')):
                self.message_user(request, "Invalid file format. Upload .xlsx, .xls, or .csv.", level=messages.ERROR)
                return redirect('admin:product_import_excel')

            try:
                if filename.endswith('.csv'):
                    try:
                        df = pd.read_csv(file, encoding='utf-8')
                    except UnicodeDecodeError:
                        file.seek(0)
                        df = pd.read_csv(file, encoding='latin1')
                else:
                    df = pd.read_excel(file)
            except Exception as e:
                self.message_user(request, f"Failed to read file: {str(e)}", level=messages.ERROR)
                return redirect('admin:product_import_excel')

            df.columns = [str(c).strip() for c in df.columns]

            col_master_code = next((c for c in df.columns if 'master' in c.lower() and 'code' in c.lower()), None)
            if not col_master_code:
                col_master_code = next((c for c in df.columns if any(k in c.lower() for k in ['barcode', 'code', 'sku'])), None)

            col_name = next((c for c in df.columns if c.lower() == 'name' or 'app name' in c.lower() or 'product' in c.lower()), None)
            col_stock = next((c for c in df.columns if c.lower() == 'total' or 'stock in hand' in c.lower() or 'stock' in c.lower() or 'qty' in c.lower()), None)
            col_cost = next((c for c in df.columns if 'cost' in c.lower() or 'price' in c.lower()), None)

            if not col_master_code or not col_name:
                self.message_user(request, f'Could not find "Master Code" and "Name" columns. Columns found: {", ".join(df.columns)}', level=messages.ERROR)
                return redirect('admin:product_import_excel')

            created_count = 0
            updated_count = 0
            skipped_count = 0

            with transaction.atomic():
                for _, row in df.iterrows():
                    raw_code = str(row.get(col_master_code, '')).strip()
                    if not raw_code or raw_code.lower() == 'nan':
                        skipped_count += 1
                        continue
                    if raw_code.endswith('.0'):
                        raw_code = raw_code[:-2]

                    raw_name = str(row.get(col_name, '')).strip()
                    if not raw_name or raw_name.lower() == 'nan':
                        skipped_count += 1
                        continue

                    stock_val = 0
                    if col_stock and pd.notna(row.get(col_stock)):
                        try:
                            stock_val = max(0, int(float(row.get(col_stock))))
                        except (ValueError, TypeError):
                            stock_val = 0
                    if stock_val == 0 and 'Stock In Hand' in df.columns and pd.notna(row.get('Stock In Hand')):
                        try:
                            stock_val = max(0, int(float(row.get('Stock In Hand'))))
                        except (ValueError, TypeError):
                            pass

                    price_val = Decimal('149.00')
                    if col_cost and pd.notna(row.get(col_cost)):
                        try:
                            cleaned_price = re.sub(r'[^\d.]', '', str(row.get(col_cost)))
                            if cleaned_price:
                                parsed_p = Decimal(cleaned_price)
                                if parsed_p > 0:
                                    price_val = parsed_p
                        except Exception:
                            pass

                    if '___' in raw_name:
                        parts = raw_name.split('___', 1)
                        display_name = f"{parts[0].strip()} - {parts[1].strip()}"
                        variant_name = parts[1].strip()
                    else:
                        display_name = raw_name
                        variant_name = 'Standard'

                    cat = detect_category(raw_name)

                    product, created = Product.objects.get_or_create(
                        barcode=raw_code,
                        defaults={
                            'name': display_name,
                            'category': cat,
                            'variant': variant_name,
                            'quantity': stock_val,
                            'price': price_val,
                        }
                    )

                    if created:
                        created_count += 1
                    else:
                        product.name = display_name
                        product.category = cat
                        product.variant = variant_name
                        product.quantity = stock_val
                        if price_val > 0 and product.price == 0:
                            product.price = price_val
                        product.save()
                        updated_count += 1

                    var_obj, _ = ProductVariant.objects.get_or_create(
                        product=product,
                        name=variant_name,
                        defaults={'stock': stock_val}
                    )
                    var_obj.stock = stock_val
                    var_obj.save()

            self.message_user(
                request,
                f"Successfully imported {created_count + updated_count} items ({created_count} added, {updated_count} updated). {skipped_count} skipped.",
                level=messages.SUCCESS
            )
            return redirect('admin:inventory_product_changelist')

        context = dict(
            self.admin_site.each_context(request),
            title="Import Products from Excel / CSV",
            opts=self.model._meta,
        )
        return render(request, "admin/inventory/product/import_excel.html", context)


class SaleInline(admin.TabularInline):
    model = Sale
    extra = 0
    readonly_fields = ('product', 'variant_name', 'quantity_sold', 'unit_price', 'total_amount', 'sold_at')


@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer_name', 'payment_method', 'total_items', 'total_amount', 'created_at')
    search_fields = ('order_number', 'customer_name')
    list_filter = ('payment_method', 'created_at')
    inlines = [SaleInline]


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'variant_name', 'quantity_sold', 'unit_price', 'total_amount', 'sold_at')
    list_filter = ('sold_at',)
