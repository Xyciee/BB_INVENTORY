import json
import uuid
from decimal import Decimal, InvalidOperation
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Q
from .models import Product, ProductVariant, Sale


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
    Product.objects.exclude(image_url='').update(image_url='')
    for item in LIPS_PRODUCTS + FACE_PRODUCTS + EYES_PRODUCTS + BATH_AND_BODY_PRODUCTS + FRAGRANCE_PRODUCTS:
        product, _ = Product.objects.get_or_create(
            barcode=item['barcode'],
            defaults=item,
        )
        if not product.variants.exists():
            raw_variants = [v.strip() for v in (product.variant or item.get('variant', '')).split(',') if v.strip()]
            if not raw_variants:
                raw_variants = ['Standard']
            per_variant_stock = max(5, int(product.quantity // max(1, len(raw_variants))))
            for idx, v_name in enumerate(raw_variants):
                ProductVariant.objects.create(
                    product=product,
                    name=v_name,
                    stock=per_variant_stock + (idx * 2),
                )
            product.quantity = sum(v.stock for v in product.variants.all())
            product.save()


def _get_filtered_products(request, per_page=8):
    _ensure_catalog_products()
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
    _ensure_catalog_products()
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
            return redirect('inventory')

    page_obj, filtered_qs, selected_category, search_query = _get_filtered_products(request, per_page=8)
    total_stock = ProductVariant.objects.filter(product__in=filtered_qs).aggregate(total=Sum('stock'))['total'] or 0

    return render(request, 'Pages/Inventory.html', {
        'page_title': 'Inventory',
        'current_page': 'inventory',
        'products': page_obj,
        'page_obj': page_obj,
        'selected_category': selected_category,
        'search_query': search_query,
        'total_stock': total_stock,
        'error': error,
    })


def sales_view(request):
    page_obj, _, selected_category, search_query = _get_filtered_products(request, per_page=9)
    return render(request, 'Pages/Sales.html', {
        'page_title': 'Sales',
        'current_page': 'sales',
        'products': page_obj,
        'page_obj': page_obj,
        'selected_category': selected_category,
        'search_query': search_query,
    })


def checkout_api(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Invalid request method.'}, status=405)

    try:
        payload = json.loads(request.body.decode('utf-8'))
        items = payload.get('items', [])
    except Exception:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON payload.'}, status=400)

    if not items:
        return JsonResponse({'ok': False, 'error': 'No items in checkout.'}, status=400)

    total_order = Decimal('0.00')
    for entry in items:
        product_id = entry.get('id')
        variant_name = (entry.get('variant') or '').strip()
        qty = max(1, int(entry.get('qty', 1)))
        product = Product.objects.filter(pk=product_id).first()
        if not product:
            continue
        unit_price = product.selling_price
        line_total = unit_price * qty
        Sale.objects.create(
            product=product,
            variant_name=variant_name,
            quantity_sold=qty,
            unit_price=unit_price,
            total_amount=line_total,
        )
        variant_obj = product.variants.filter(name=variant_name).first()
        if variant_obj:
            variant_obj.stock = max(0, variant_obj.stock - qty)
            variant_obj.save()
            product.quantity = sum(v.stock for v in product.variants.all())
            product.save()
        else:
            product.quantity = max(0, product.quantity - qty)
            product.save()
        total_order += line_total

    return JsonResponse({
        'ok': True,
        'total_amount': f"{total_order:.2f}",
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


def delete_product(request, pk):
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=pk)
        product.delete()
    return redirect('inventory')


def barcode_lookup(request, barcode):
    product = Product.objects.filter(barcode=barcode).first()
    if product:
        return JsonResponse({
            'found': True,
            'id': product.id,
            'barcode': product.barcode,
            'name': product.name,
            'variant': product.variant,
            'quantity': product.quantity,
            'price': str(product.price),
            'discounted_price': str(product.discounted_price) if product.discounted_price is not None else '',
        })
    return JsonResponse({'found': False})


def realtime_sales_api(request):
    total_sales_revenue = Sale.objects.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    total_units_sold = Sale.objects.aggregate(total=Sum('quantity_sold'))['total'] or 0
    return JsonResponse({
        'total_sales_revenue': f"{total_sales_revenue:.2f}",
        'total_units_sold': total_units_sold,
    })
