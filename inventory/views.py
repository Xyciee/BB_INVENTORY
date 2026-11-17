import json
from decimal import Decimal, InvalidOperation
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from .models import Product, Sale


DEFAULT_COSMETICS = [
    {
        'barcode': 'BB-FACE-001',
        'name': 'Radiant Cushion Foundation SPF50',
        'category': 'face',
        'variant': '21N Warm Ivory, 23N Natural Beige, 25N Honey Sand',
        'price': Decimal('599.00'),
        'quantity': 25,
        'image_url': 'https://images.unsplash.com/photo-1631729371254-42c2892f0e6e?auto=format&fit=crop&w=600&q=80',
    },
    {
        'barcode': 'BB-FACE-002',
        'name': 'Pore Blur Setting Powder',
        'category': 'face',
        'variant': 'Translucent, Soft Pink, Warm Nude',
        'price': Decimal('349.00'),
        'quantity': 30,
        'image_url': 'https://images.unsplash.com/photo-1596462502278-27bfdc403348?auto=format&fit=crop&w=600&q=80',
    },
    {
        'barcode': 'BB-LIPS-001',
        'name': 'Velvet Matte Lip Tint',
        'category': 'lips',
        'variant': '#01 Peach Nude, #04 Rose Petal, #07 Berry Wine',
        'price': Decimal('299.00'),
        'quantity': 40,
        'image_url': 'https://images.unsplash.com/photo-1586495777744-4413f21062fa?auto=format&fit=crop&w=600&q=80',
    },
    {
        'barcode': 'BB-LIPS-002',
        'name': 'Hydro Plump Lip Gloss',
        'category': 'lips',
        'variant': '#01 Clear Crystal, #02 Honey Glow, #03 Cherry Dew',
        'price': Decimal('279.00'),
        'quantity': 35,
        'image_url': 'https://images.unsplash.com/photo-1619451334792-150fd785ee74?auto=format&fit=crop&w=600&q=80',
    },
    {
        'barcode': 'BB-EYES-001',
        'name': '9-Pan Eyeshadow Palette',
        'category': 'eyes',
        'variant': 'Sunset Rose, Cocoa Mocha, Champagne Gold',
        'price': Decimal('499.00'),
        'quantity': 20,
        'image_url': 'https://images.unsplash.com/photo-1512496015851-a90fb38ba796?auto=format&fit=crop&w=600&q=80',
    },
    {
        'barcode': 'BB-CHEEKS-001',
        'name': 'Silk Dew Liquid Blush',
        'category': 'cheeks',
        'variant': '#01 Peony Flush, #02 Coral Crush, #03 Mauve Haze',
        'price': Decimal('329.00'),
        'quantity': 28,
        'image_url': 'https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?auto=format&fit=crop&w=600&q=80',
    },
    {
        'barcode': 'BB-SKIN-001',
        'name': 'Niacinamide 10% Glow Serum',
        'category': 'skincare',
        'variant': '15ml Travel, 30ml Regular, 50ml Jumbo',
        'price': Decimal('450.00'),
        'quantity': 32,
        'image_url': 'https://images.unsplash.com/photo-1620916566398-39f1143ab7be?auto=format&fit=crop&w=600&q=80',
    },
    {
        'barcode': 'BB-FRAG-001',
        'name': 'Eau de Parfum Floral Mist',
        'category': 'fragrance',
        'variant': '30ml Spray, 50ml Spray, 100ml Bottle',
        'price': Decimal('799.00'),
        'quantity': 18,
        'image_url': 'https://images.unsplash.com/photo-1541643600914-78b084683601?auto=format&fit=crop&w=600&q=80',
    },
    {
        'barcode': 'BB-TOOLS-001',
        'name': 'Pro Kabuki Makeup Brush Set',
        'category': 'tools',
        'variant': 'Rose Gold, Matte Black, Pearl White',
        'price': Decimal('399.00'),
        'quantity': 22,
        'image_url': 'https://images.unsplash.com/photo-1527799820374-dcf8d9d4a388?auto=format&fit=crop&w=600&q=80',
    },
]


def _ensure_sample_products():
    for item in DEFAULT_COSMETICS:
        obj, created = Product.objects.get_or_create(
            barcode=item['barcode'],
            defaults=item,
        )
        if not created and ',' not in obj.variant:
            obj.variant = item['variant']
            obj.save()


def _get_filtered_products(request):
    _ensure_sample_products()
    category = request.GET.get('category', 'all').strip().lower()
    qs = Product.objects.all()
    if category and category != 'all':
        qs = qs.filter(category=category)
    return qs, category


def analytics_view(request):
    products, selected_category = _get_filtered_products(request)
    return render(request, 'Pages/Analytics.html', {
        'page_title': 'Analytics',
        'current_page': 'analytics',
        'products': products,
        'selected_category': selected_category,
    })


def inventory_view(request):
    products, selected_category = _get_filtered_products(request)
    return render(request, 'Pages/Inventory.html', {
        'page_title': 'Inventory',
        'current_page': 'inventory',
        'products': products,
        'selected_category': selected_category,
    })


def sales_view(request):
    products, selected_category = _get_filtered_products(request)
    return render(request, 'Pages/Sales.html', {
        'page_title': 'Sales',
        'current_page': 'sales',
        'products': products,
        'selected_category': selected_category,
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
        qty = max(1, int(entry.get('qty', 1)))
        product = Product.objects.filter(pk=product_id).first()
        if not product:
            continue
        unit_price = product.selling_price
        line_total = unit_price * qty
        Sale.objects.create(
            product=product,
            quantity_sold=qty,
            unit_price=unit_price,
            total_amount=line_total,
        )
        if product.quantity >= qty:
            product.quantity -= qty
        else:
            product.quantity = 0
        product.save()
        total_order += line_total

    return JsonResponse({
        'ok': True,
        'total_amount': f"{total_order:.2f}",
    })


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
