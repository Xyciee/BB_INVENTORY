import csv
import io
import json
import re
import uuid
from decimal import Decimal, InvalidOperation
import pandas as pd
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Q
from django.utils import timezone
from django.utils.text import slugify
from .models import Product, ProductVariant, Sale, SalesOrder, Category


def detect_category(name):
    cleaned = re.sub(r'(?i)\b(baby\s+bright(\s+philippines)?)\b', '', name).lower()
    if any(k in cleaned for k in ['body', 'scrub', 'lotion', 'bath', 'cleanser', 'peeling']):
        return 'bath_and_body'
    elif any(k in cleaned for k in ['mist', 'spray', 'perfume']):
        return 'fragrance'
    elif any(k in cleaned for k in ['eyeliner', 'eye lighter', 'lashbrow', 'brow', 'eye palette', 'eye set', 'cornflower', 'eyes']):
        return 'eyes'
    elif any(k in cleaned for k in ['lip', 'tint', 'gloss', 'jelly']):
        return 'lips'
    elif any(k in cleaned for k in ['bb cream', 'powder', 'cushion', 'serum', 'foundation', 'blush', 'mask', 'facial', 'booster', 'gluta', 'aha']):
        return 'face'
    return 'lips'


LIPS_PRODUCTS = [
    {
        'barcode': 'BB-LIPS-001',
        'name': 'Lip & Cheek Matte Tint',
        'category': 'lips',
        'variant': '#01 Peach Me, #03 Deep Sea Coral, #05 Just Peach, #13 Goji',
        'price': Decimal('149.00'),
        'quantity': 40,
    },
    {
        'barcode': 'BB-LIPS-002',
        'name': 'Plump Rejulight',
        'category': 'lips',
        'variant': '#01 Rosy Glow, #02 Coral Plump, #03 Berry Shine',
        'price': Decimal('199.00'),
        'quantity': 35,
    },
    {
        'barcode': 'BB-LIPS-003',
        'name': 'Gelato Icy Tint',
        'category': 'lips',
        'variant': '#01 Strawberry Sorbet, #02 Peach Gelato, #03 Cherry Ice',
        'price': Decimal('159.00'),
        'quantity': 30,
    },
    {
        'barcode': 'BB-LIPS-004',
        'name': 'Rejulight Jelly Lip Tint',
        'category': 'lips',
        'variant': '#01 Pink Jelly, #02 Apricot Jelly, #03 Ruby Jelly',
        'price': Decimal('179.00'),
        'quantity': 35,
    },
    {
        'barcode': 'BB-LIPS-005',
        'name': 'Morning C Color Lip Mask',
        'category': 'lips',
        'variant': '#01 Yuzu Orange, #02 Pink Grapefruit, #03 Sweet Berry',
        'price': Decimal('149.00'),
        'quantity': 25,
    },
    {
        'barcode': 'BB-LIPS-006',
        'name': 'Barrier Matte Lip Click',
        'category': 'lips',
        'variant': '#01 Nude Rose, #02 Brick Terracotta, #03 Velvet Mauve',
        'price': Decimal('189.00'),
        'quantity': 30,
    },
    {
        'barcode': 'BB-LIPS-007',
        'name': 'Sweet Cafe Shiny Tint',
        'category': 'lips',
        'variant': 'Brown Sugar, Milk Tea, Rose Tea, Peach Tea',
        'price': Decimal('89.00'),
        'quantity': 50,
    },
    {
        'barcode': 'BB-LIPS-008',
        'name': '8 Glasses Water Gloss',
        'category': 'lips',
        'variant': '#01 Crystal Dew, #02 Honey Water, #03 Rose Water',
        'price': Decimal('159.00'),
        'quantity': 40,
    },
]

FACE_PRODUCTS = [
    {
        'barcode': 'BB-FACE-001',
        'name': 'Aha & Gluta Whitening Facial Foam',
        'category': 'face',
        'variant': '120g Tube, 50g Travel',
        'price': Decimal('149.00'),
        'quantity': 35,
    },
    {
        'barcode': 'BB-FACE-002',
        'name': 'Exowhite Cushion Blush',
        'category': 'face',
        'variant': '#01 Coral Peach, #02 Rosy Pink, #03 Berry Flush',
        'price': Decimal('199.00'),
        'quantity': 30,
    },
    {
        'barcode': 'BB-FACE-003',
        'name': 'Cica Oil Control Filter Powder',
        'category': 'face',
        'variant': '#01 Natural Green, #02 Translucent Matte',
        'price': Decimal('169.00'),
        'quantity': 40,
    },
    {
        'barcode': 'BB-FACE-004',
        'name': 'Sakura Glow Tone Up Fairy Powder',
        'category': 'face',
        'variant': 'Sakura Pink, Pearl Shimmer',
        'price': Decimal('159.00'),
        'quantity': 35,
    },
    {
        'barcode': 'BB-FACE-005',
        'name': 'Booster Mask',
        'category': 'face',
        'variant': 'Brightening, Hydrating, Pore Care, Acne Clear',
        'price': Decimal('59.00'),
        'quantity': 60,
    },
    {
        'barcode': 'BB-FACE-006',
        'name': 'Watermelon & Tomato Matte Bb Cream (Tube)',
        'category': 'face',
        'variant': '#21 Light Beige, #23 Natural Beige',
        'price': Decimal('189.00'),
        'quantity': 30,
    },
    {
        'barcode': 'BB-FACE-007',
        'name': 'Watermelon & Tomato Matte Bb Cream (Sachet)',
        'category': 'face',
        'variant': '#21 Light Beige, #23 Natural Beige',
        'price': Decimal('49.00'),
        'quantity': 80,
    },
    {
        'barcode': 'BB-FACE-008',
        'name': 'High C Serum Foundation Spf50+ Pa++',
        'category': 'face',
        'variant': '#21 Warm Ivory, #23 Natural Beige, #25 Honey Sand',
        'price': Decimal('229.00'),
        'quantity': 28,
    },
    {
        'barcode': 'BB-FACE-009',
        'name': 'Exowhite 8 Hya Booster',
        'category': 'face',
        'variant': '30ml Serum, 15ml Mini',
        'price': Decimal('249.00'),
        'quantity': 25,
    },
    {
        'barcode': 'BB-FACE-010',
        'name': 'Body Sleeping Mask',
        'category': 'face',
        'variant': 'Lemon Vit C, White Pear, Mixed Berry',
        'price': Decimal('179.00'),
        'quantity': 30,
    },
]

EYES_PRODUCTS = [
    {
        'barcode': 'BB-EYES-001',
        'name': 'Trio Slim Lashbrow Cara & Eyeliner',
        'category': 'eyes',
        'variant': '#01 Jet Black, #02 Natural Brown',
        'price': Decimal('199.00'),
        'quantity': 35,
    },
    {
        'barcode': 'BB-EYES-002',
        'name': 'Corn Flower Eyeliner & Remover',
        'category': 'eyes',
        'variant': '#01 Deep Black, #02 Espresso Brown',
        'price': Decimal('169.00'),
        'quantity': 30,
    },
    {
        'barcode': 'BB-EYES-003',
        'name': 'Rosy Rose Eyeliner & Eyelighter',
        'category': 'eyes',
        'variant': '#01 Rose Gold, #02 Champagne Shimmer, #03 Peach Pearl',
        'price': Decimal('179.00'),
        'quantity': 30,
    },
    {
        'barcode': 'BB-EYES-004',
        'name': 'Ginger 3 In 1 Tiny Brow',
        'category': 'eyes',
        'variant': '#01 Caramel Brown, #02 Dark Brown, #03 Ash Brown',
        'price': Decimal('159.00'),
        'quantity': 40,
    },
    {
        'barcode': 'BB-EYES-005',
        'name': 'Eye Palette',
        'category': 'eyes',
        'variant': '#01 Sunset Coral, #02 Rose Quartz, #03 Warm Mocha',
        'price': Decimal('229.00'),
        'quantity': 25,
    },
]

BATH_AND_BODY_PRODUCTS = [
    {
        'barcode': 'BB-BODY-001',
        'name': 'Apple Honey Peeling Gel',
        'category': 'bath_and_body',
        'variant': '150ml Tube, 50ml Pouch',
        'price': Decimal('159.00'),
        'quantity': 30,
    },
    {
        'barcode': 'BB-BODY-002',
        'name': 'Yuzu Lemon Peeling Gel',
        'category': 'bath_and_body',
        'variant': '150ml Tube, 50ml Pouch',
        'price': Decimal('159.00'),
        'quantity': 30,
    },
    {
        'barcode': 'BB-BODY-003',
        'name': 'Moist Sun Cooling Body Lotion',
        'category': 'bath_and_body',
        'variant': '200ml Pump, 100ml Tube',
        'price': Decimal('189.00'),
        'quantity': 35,
    },
    {
        'barcode': 'BB-BODY-004',
        'name': 'White Sun Cooling Body Lotion',
        'category': 'bath_and_body',
        'variant': '200ml Pump, 100ml Tube',
        'price': Decimal('189.00'),
        'quantity': 35,
    },
    {
        'barcode': 'BB-BODY-005',
        'name': 'Vit C & Yuzu Body Scrub',
        'category': 'bath_and_body',
        'variant': '250g Jar, 100g Pouch',
        'price': Decimal('179.00'),
        'quantity': 28,
    },
    {
        'barcode': 'BB-BODY-006',
        'name': 'Milk And Lemon Body Bath Scrub',
        'category': 'bath_and_body',
        'variant': '250g Jar, 100g Pouch',
        'price': Decimal('179.00'),
        'quantity': 28,
    },
    {
        'barcode': 'BB-BODY-007',
        'name': 'Body Cleanser',
        'category': 'bath_and_body',
        'variant': 'Sweet Peony, Mixed Berry, Fresh Yuzu',
        'price': Decimal('199.00'),
        'quantity': 40,
    },
]

FRAGRANCE_PRODUCTS = [
    {
        'barcode': 'BB-FRAG-001',
        'name': 'Fresh Spray',
        'category': 'fragrance',
        'variant': '20ml Pocket Spray, 50ml Bottle',
        'price': Decimal('129.00'),
        'quantity': 35,
    },
    {
        'barcode': 'BB-FRAG-002',
        'name': 'Body Mist',
        'category': 'fragrance',
        'variant': 'Sweet Peony, Secret Love, Pure Vanilla, Floral Bloom',
        'price': Decimal('179.00'),
        'quantity': 30,
    },
]


def _ensure_catalog_products():
    # Disabled: do not automatically re-insert dummy data.
    pass


def _get_filtered_products(request, per_page=8):
    category = request.GET.get('category', 'all').strip().lower()
    search_query = request.GET.get('q', '').strip()
    page_number = request.GET.get('page', 1)

    qs = Product.objects.prefetch_related('variants').all()
    if category and category != 'all':
        qs = qs.filter(category=category)
    if search_query:
        qs = qs.filter(
            Q(name__icontains=search_query) |
            Q(variant__icontains=search_query) |
            Q(barcode__icontains=search_query)
        )

    paginator = Paginator(qs, per_page)
    page_obj = paginator.get_page(page_number)
    return page_obj, qs, category, search_query


def analytics_view(request):
    page_obj, _, selected_category, search_query = _get_filtered_products(request, per_page=9)
    return render(request, 'Pages/Analytics.html', {
        'page_title': 'Analytics',
        'current_page': 'analytics',
        'products': page_obj,
        'page_obj': page_obj,
        'selected_category': selected_category,
        'search_query': search_query,
    })


def inventory_view(request):
    error = None

    if request.method == 'POST':
        product_id = request.POST.get('product_id', '').strip()
        barcode = request.POST.get('barcode', '').strip()
        name = request.POST.get('name', '').strip()
        category = request.POST.get('category', 'lips').strip().lower()
        price_raw = request.POST.get('price', '0').strip()
        uploaded_image = request.FILES.get('image')

        variant_names = request.POST.getlist('variant_name[]')
        variant_stocks = request.POST.getlist('variant_stock[]')

        if not barcode:
            barcode = f"BB-{uuid.uuid4().hex[:6].upper()}"

        if not name:
            error = "Please enter the product name."
        else:
            try:
                price = Decimal(price_raw or '0.00')
            except (ValueError, InvalidOperation):
                error = "Invalid price format."

        cleaned_variants = []
        for v_name, v_stock in zip(variant_names, variant_stocks):
            v_name_clean = v_name.strip()
            if not v_name_clean:
                continue
            try:
                s_val = max(0, int(v_stock or 0))
            except ValueError:
                s_val = 0
            cleaned_variants.append((v_name_clean, s_val))

        if not cleaned_variants:
            cleaned_variants = [('Standard', 1)]

        total_qty = sum(s for _, s in cleaned_variants)
        variant_summary_str = ', '.join(v for v, _ in cleaned_variants)

        if not error:
            if product_id:
                product = get_object_or_404(Product, pk=product_id)
                product.barcode = barcode
                product.name = name
                product.category = category
                product.variant = variant_summary_str
                product.quantity = total_qty
                product.price = price
                if uploaded_image:
                    product.image = uploaded_image
                product.save()
            else:
                defaults = {
                    'name': name,
                    'category': category,
                    'variant': variant_summary_str,
                    'quantity': total_qty,
                    'price': price,
                }
                product, _ = Product.objects.update_or_create(
                    barcode=barcode,
                    defaults=defaults,
                )
                if uploaded_image:
                    product.image = uploaded_image
                    product.save()

            product.variants.all().delete()
            for v_name_clean, s_val in cleaned_variants:
                ProductVariant.objects.create(
                    product=product,
                    name=v_name_clean,
                    stock=s_val,
                )
            messages.success(request, f'Product "{product.name}" saved successfully!')
            return redirect('inventory')
        else:
            messages.error(request, error)

    page_obj, filtered_qs, selected_category, search_query = _get_filtered_products(request, per_page=8)
    total_stock = ProductVariant.objects.filter(product__in=filtered_qs).aggregate(total=Sum('stock'))['total'] or 0
    total_products_count = filtered_qs.count()
    low_stock_count = ProductVariant.objects.filter(product__in=filtered_qs, stock__gt=0, stock__lte=5).values('product').distinct().count()
    out_of_stock_count = ProductVariant.objects.filter(product__in=filtered_qs, stock=0).values('product').distinct().count()

    return render(request, 'Pages/Inventory.html', {
        'page_title': 'Inventory',
        'current_page': 'inventory',
        'products': page_obj,
        'page_obj': page_obj,
        'selected_category': selected_category,
        'search_query': search_query,
        'total_stock': total_stock,
        'total_products_count': total_products_count,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'error': error,
    })


def sales_view(request):
    search_query = request.GET.get('q', '').strip()
    date_filter = request.GET.get('date', 'all').strip().lower()
    payment_filter = request.GET.get('payment', 'all').strip()
    page_number = request.GET.get('page', 1)
    per_page_param = request.GET.get('per_page', '10').strip()
    try:
        per_page = int(per_page_param)
        if per_page not in [5, 10, 20, 50]:
            per_page = 10
    except ValueError:
        per_page = 10

    qs = SalesOrder.objects.prefetch_related('items__product').all()

    now = timezone.now()
    today = now.date()

    if date_filter == 'today':
        qs = qs.filter(created_at__date=today)
    elif date_filter == 'yesterday':
        yesterday = today - timezone.timedelta(days=1)
        qs = qs.filter(created_at__date=yesterday)
    elif date_filter == 'this_week':
        week_start = today - timezone.timedelta(days=today.weekday())
        qs = qs.filter(created_at__date__gte=week_start)
    elif date_filter == 'this_month':
        qs = qs.filter(created_at__year=today.year, created_at__month=today.month)

    if payment_filter and payment_filter != 'all':
        qs = qs.filter(payment_method__iexact=payment_filter)

    if search_query:
        qs = qs.filter(
            Q(order_number__icontains=search_query) |
            Q(customer_name__icontains=search_query) |
            Q(items__product__name__icontains=search_query) |
            Q(items__variant_name__icontains=search_query)
        ).distinct()

    # Metrics
    all_orders = SalesOrder.objects.all()
    total_revenue = all_orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    total_orders_count = all_orders.count()
    total_items_sold = all_orders.aggregate(total=Sum('total_items'))['total'] or 0

    today_orders_qs = all_orders.filter(created_at__date=today)
    today_revenue = today_orders_qs.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    today_orders_count = today_orders_qs.count()

    paginator = Paginator(qs, per_page)
    page_obj = paginator.get_page(page_number)

    return render(request, 'Pages/Sales.html', {
        'page_title': 'Sales Module',
        'current_page': 'sales',
        'orders': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'date_filter': date_filter,
        'payment_filter': payment_filter,
        'per_page': per_page,
        'total_revenue': total_revenue,
        'total_orders_count': total_orders_count,
        'total_items_sold': total_items_sold,
        'today_revenue': today_revenue,
        'today_orders_count': today_orders_count,
    })


def void_sales_order(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(SalesOrder, pk=order_id)
        order_num = order.order_number
        with transaction.atomic():
            # Return sold items back to inventory stock
            for sale_item in order.items.select_related('product').all():
                prod = sale_item.product
                v_name = sale_item.variant_name
                var_obj = prod.variants.filter(name=v_name).first() if v_name else None
                if var_obj:
                    var_obj.stock += sale_item.quantity_sold
                    var_obj.save()
                    prod.quantity = sum(v.stock for v in prod.variants.all())
                    prod.save()
                else:
                    prod.quantity += sale_item.quantity_sold
                    prod.save()
            order.items.all().delete()
            order.delete()
        messages.success(request, f'Order #{order_num} was voided/deleted and inventory stocks were returned.')
    return redirect('sales')


def export_sales_csv(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    filename = f"sales_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow([
        'Order Number', 'Date & Time', 'Customer Name', 'Payment Method',
        'Total Items', 'Total Amount (PHP)', 'Items Breakdown'
    ])

    orders = SalesOrder.objects.prefetch_related('items__product').all()
    for o in orders:
        items_desc = []
        for itm in o.items.all():
            v_info = f" ({itm.variant_name})" if itm.variant_name and itm.variant_name != 'Standard' else ""
            items_desc.append(f"{itm.product.name}{v_info} x{itm.quantity_sold} @ \u20B1{itm.unit_price} = \u20B1{itm.total_amount}")
        writer.writerow([
            o.order_number,
            o.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            o.customer_name,
            o.payment_method,
            o.total_items,
            f"{o.total_amount:.2f}",
            " | ".join(items_desc)
        ])
    return response


def categories_view(request):
    search_query = request.GET.get('q', '').strip()

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        icon = request.POST.get('icon', '✨').strip()
        description = request.POST.get('description', '').strip()
        custom_slug = request.POST.get('slug', '').strip()

        if not name:
            messages.error(request, 'Pakilagay ang pangalan ng kategorya (Category Name).')
            return redirect('categories')

        slug = slugify(custom_slug) if custom_slug else slugify(name)
        if not slug:
            slug = f"cat-{uuid.uuid4().hex[:6]}"

        if Category.objects.filter(Q(name__iexact=name) | Q(slug=slug)).exists():
            messages.error(request, f'Ang kategoryang "{name}" o slug "{slug}" ay umiiral na sa database.')
            return redirect('categories')

        cat = Category.objects.create(
            name=name,
            slug=slug,
            icon=icon or '✨',
            description=description,
        )
        messages.success(request, f'Tagumpay na nalikha ang kategoryang "{cat.name}" ({cat.icon})!')
        return redirect('categories')

    categories_qs = Category.objects.all().order_by('name')
    if search_query:
        categories_qs = categories_qs.filter(
            Q(name__icontains=search_query) |
            Q(slug__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    category_data = []
    total_stock_all = 0

    for cat in categories_qs:
        p_count = cat.product_count
        stock_sum = cat.total_stock
        total_stock_all += stock_sum
        category_data.append({
            'category': cat,
            'product_count': p_count,
            'total_stock': stock_sum,
        })

    total_categories_count = Category.objects.count()
    total_products_count = Product.objects.count()

    top_category = None
    if category_data:
        top_category = max(category_data, key=lambda c: c['product_count'])

    return render(request, 'Pages/Categories.html', {
        'page_title': 'Category Management',
        'current_page': 'categories',
        'categories_list': category_data,
        'search_query': search_query,
        'total_categories_count': total_categories_count,
        'total_products_count': total_products_count,
        'total_stock_all': total_stock_all,
        'top_category': top_category,
    })


def edit_category(request, category_id):
    if request.method == 'POST':
        category = get_object_or_404(Category, pk=category_id)
        name = request.POST.get('name', '').strip()
        icon = request.POST.get('icon', '✨').strip()
        description = request.POST.get('description', '').strip()
        new_slug = request.POST.get('slug', '').strip()

        if not name:
            messages.error(request, 'Hindi maaaring walang laman ang Category Name.')
            return redirect('categories')

        target_slug = slugify(new_slug) if new_slug else slugify(name)
        if not target_slug:
            target_slug = category.slug

        conflict = Category.objects.filter(~Q(pk=category.id), Q(name__iexact=name) | Q(slug=target_slug)).first()
        if conflict:
            messages.error(request, f'Ang pangalan o slug ay ginagamit na ng ibang kategorya ("{conflict.name}").')
            return redirect('categories')

        old_slug = category.slug
        category.name = name
        category.icon = icon or '✨'
        category.description = description
        category.slug = target_slug
        category.save()

        if old_slug != target_slug:
            Product.objects.filter(category=old_slug).update(category=target_slug)

        messages.success(request, f'Na-update ang kategoryang "{name}" ({category.icon})!')
    return redirect('categories')


def delete_category(request, category_id):
    if request.method == 'POST':
        category = get_object_or_404(Category, pk=category_id)
        cat_name = category.name
        cat_slug = category.slug

        reassign_slug = request.POST.get('reassign_to', '').strip()
        affected_count = Product.objects.filter(category=cat_slug).count()

        with transaction.atomic():
            if affected_count > 0:
                if not reassign_slug:
                    fallback_cat = Category.objects.exclude(pk=category.id).first()
                    reassign_slug = fallback_cat.slug if fallback_cat else 'lips'
                Product.objects.filter(category=cat_slug).update(category=reassign_slug)

            category.delete()

        if affected_count > 0:
            messages.success(request, f'Nabura ang kategoryang "{cat_name}". Ang {affected_count} apektadong produkto ay inilipat sa "{reassign_slug}".')
        else:
            messages.success(request, f'Matagumpay na nabura ang kategoryang "{cat_name}".')
    return redirect('categories')


def checkout_api(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Invalid request method.'}, status=405)

    try:
        payload = json.loads(request.body.decode('utf-8'))
        items = payload.get('items', [])
    except Exception:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON payload.'}, status=400)

    if not items:
        return JsonResponse({'ok': False, 'error': 'Walang laman ang cart.'}, status=400)

    # 1. Validation Phase: Check if any item has 0 stock or requested quantity exceeds available stock
    out_of_stock_errors = []
    validated_items = []

    for entry in items:
        product_id = entry.get('id')
        variant_name = (entry.get('variant') or '').strip()
        qty = max(1, int(entry.get('qty', 1)))
        product = Product.objects.filter(pk=product_id).first()
        if not product:
            out_of_stock_errors.append(f'Ang item na may ID #{product_id} ay wala na sa inventory.')
            continue

        variant_obj = product.variants.filter(name=variant_name).first() if variant_name else product.variants.first()
        available_stock = variant_obj.stock if variant_obj else product.quantity

        var_label = f" ({variant_name})" if variant_name and variant_name != 'Standard' else ""

        if available_stock <= 0:
            out_of_stock_errors.append(f'OUT OF STOCK: Ang "{product.name}{var_label}" ay 0 na ang stock.')
        elif qty > available_stock:
            out_of_stock_errors.append(f'Kulang ang stock: Ang "{product.name}{var_label}" ay may {available_stock} pcs na lang (hinihingi: {qty}).')
        else:
            validated_items.append((product, variant_obj, variant_name, qty))

    if out_of_stock_errors:
        return JsonResponse({
            'ok': False,
            'error': 'Hindi ma-checkout dahil sa kakulangan ng stock:\n• ' + '\n• '.join(out_of_stock_errors),
            'errors': out_of_stock_errors,
        }, status=400)

    # 2. Execution Phase: Save sales and deduct inventory inside atomic transaction
    with transaction.atomic():
        today_str = timezone.now().strftime('%Y%m%d')
        count_today = SalesOrder.objects.filter(order_number__startswith=f"BB-{today_str}").count() + 1
        order_number = f"BB-{today_str}-{count_today:04d}"

        customer_name = (payload.get('customer_name') or '').strip() or 'Walk-in Customer'
        payment_method = (payload.get('payment_method') or 'Cash').strip() or 'Cash'

        total_order = Decimal('0.00')
        total_items_count = 0
        for product, variant_obj, variant_name, qty in validated_items:
            unit_price = product.selling_price
            line_total = unit_price * qty
            total_order += line_total
            total_items_count += qty

        sales_order = SalesOrder.objects.create(
            order_number=order_number,
            customer_name=customer_name,
            payment_method=payment_method,
            total_items=total_items_count,
            total_amount=total_order,
        )

        for product, variant_obj, variant_name, qty in validated_items:
            unit_price = product.selling_price
            line_total = unit_price * qty
            Sale.objects.create(
                order=sales_order,
                product=product,
                variant_name=variant_name,
                quantity_sold=qty,
                unit_price=unit_price,
                total_amount=line_total,
            )
            if variant_obj:
                variant_obj.stock = max(0, variant_obj.stock - qty)
                variant_obj.save()
                product.quantity = sum(v.stock for v in product.variants.all())
                product.save()
            else:
                product.quantity = max(0, product.quantity - qty)
                product.save()

    return JsonResponse({
        'ok': True,
        'order_number': sales_order.order_number,
        'customer_name': sales_order.customer_name,
        'payment_method': sales_order.payment_method,
        'total_items': sales_order.total_items,
        'total_amount': f"{sales_order.total_amount:.2f}",
    })


def update_variant_stock(request, variant_id):
    if request.method == 'POST':
        variant_obj = get_object_or_404(ProductVariant, pk=variant_id)
        change = request.POST.get('change')
        if change == 'inc':
            variant_obj.stock += 1
        elif change == 'dec' and variant_obj.stock > 0:
            variant_obj.stock -= 1
        variant_obj.save()
        product = variant_obj.product
        product.quantity = sum(v.stock for v in product.variants.all())
        product.save()
    return redirect(request.META.get('HTTP_REFERER', 'inventory'))


def update_stock(request, pk):
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=pk)
        change = request.POST.get('change')
        if change == 'inc':
            product.quantity += 1
        elif change == 'dec' and product.quantity > 0:
            product.quantity -= 1
        product.save()
    return redirect('inventory')


@transaction.atomic
def delete_product(request, pk):
    if request.method == 'POST':
        try:
            product = get_object_or_404(Product, pk=pk)
            name = product.name
            product.variants.all().delete()
            product.sales.all().delete()
            product.delete()
            messages.success(request, f'Product "{name}" deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting product: {str(e)}')
    return redirect('inventory')


def import_inventory(request):
    if request.method != 'POST':
        return redirect('inventory')

    file = request.FILES.get('file')
    if not file:
        messages.error(request, 'Please select an Excel (.xlsx, .xls) or CSV file.')
        return redirect('inventory')

    filename = file.name.lower()
    if not (filename.endswith('.csv') or filename.endswith('.xlsx') or filename.endswith('.xls')):
        messages.error(request, 'Invalid file type. Please upload a .xlsx, .xls, or .csv file.')
        return redirect('inventory')

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
        messages.error(request, f'Failed to parse file: {str(e)}')
        return redirect('inventory')

    df.columns = [str(c).strip() for c in df.columns]

    # Find columns flexibly
    col_master_code = next((c for c in df.columns if 'master' in c.lower() and 'code' in c.lower()), None)
    if not col_master_code:
        col_master_code = next((c for c in df.columns if any(k in c.lower() for k in ['barcode', 'code', 'sku'])), None)

    col_name = next((c for c in df.columns if c.lower() == 'name' or 'app name' in c.lower() or 'product' in c.lower()), None)
    col_stock = next((c for c in df.columns if c.lower() == 'total' or 'stock in hand' in c.lower() or 'stock' in c.lower() or 'qty' in c.lower()), None)
    col_cost = next((c for c in df.columns if 'cost' in c.lower() or 'price' in c.lower()), None)

    if not col_master_code or not col_name:
        messages.error(request, f'Could not find required columns ("Master Code" and "Name"). Found columns: {", ".join(df.columns)}')
        return redirect('inventory')

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

    messages.success(request, f'Successfully imported {created_count + updated_count} items ({created_count} added, {updated_count} updated). {skipped_count} skipped.')
    return redirect('inventory')


def download_sample_template(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sample_inventory_template.csv"'
    writer = csv.writer(response)
    writer.writerow([
        'Master Code', 'Name', 'Brand Name', 'POS App Name', 'Seller SKU',
        'Cost', 'Update Time', 'Branch', 'Stock In Hand', 'Total', 'Active'
    ])
    writer.writerow([
        '8858842063187', 'Baby Bright Philippines Lip & Cheek Matte Tint 2.4G___DRY LEAF',
        'Baby Bright', 'Baby Bright Philippines Lip & Cheek Matte Tint 2.4G___DRY LEAF',
        '8858842063187', '149.00', '2026-11-16 15:10:52', 'SHOPEE & LAZADA QS', '191', '190', 'Yes'
    ])
    writer.writerow([
        '8858842044674', 'Baby Bright Philippines White Sun Cooling Body Lotion SPF50 PA+++ 160ml',
        'Baby Bright', 'Baby Bright Philippines White Sun Cooling Body Lotion SPF50 PA+++ 160ml',
        '8858842044674', '189.00', '2026-11-11 11:47:33', 'SHOPEE & LAZADA QS', '218', '218', 'Yes'
    ])
    return response


def barcode_lookup(request, barcode):
    code = barcode.strip()
    product = Product.objects.filter(barcode__iexact=code).first()
    if not product:
        product = Product.objects.filter(Q(barcode__icontains=code) | Q(name__icontains=code)).first()

    if product:
        variants = [{'id': v.id, 'name': v.name, 'stock': v.stock} for v in product.variants.all()]
        default_variant = product.variant or (variants[0]['name'] if variants else 'Standard')
        if variants:
            matched_var = next((v for v in variants if v['name'] == default_variant), variants[0])
            variant_stock = matched_var['stock']
        else:
            variant_stock = product.quantity

        return JsonResponse({
            'found': True,
            'id': product.id,
            'barcode': product.barcode,
            'name': product.name,
            'variant': default_variant,
            'variants': variants,
            'price': float(product.selling_price),
            'display_image': product.display_image,
            'stock': variant_stock,
            'total_stock': product.total_stock,
        })
    return JsonResponse({'found': False, 'error': f'Product with barcode / Master Code "{code}" not found.'})


def realtime_sales_api(request):
    total_sales_revenue = Sale.objects.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    total_units_sold = Sale.objects.aggregate(total=Sum('quantity_sold'))['total'] or 0
    return JsonResponse({
        'total_sales_revenue': f"{total_sales_revenue:.2f}",
        'total_units_sold': total_units_sold,
    })
