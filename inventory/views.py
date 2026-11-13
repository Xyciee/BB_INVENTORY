from decimal import Decimal, InvalidOperation
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Max
from django.utils.timezone import localtime
from .models import Product, Sale


def _save_product_from_post(request):
    product_id = request.POST.get('product_id', '').strip()
    barcode = request.POST.get('barcode', '').strip()
    name = request.POST.get('name', '').strip()
    variant = request.POST.get('variant', '').strip()
    quantity_raw = request.POST.get('quantity', '1').strip()
    price_raw = request.POST.get('price', '0').strip()
    discounted_raw = request.POST.get('discounted_price', '').strip()

    if not barcode or not name or not price_raw:
        return None, "Please enter the barcode number, product name, and price."

    try:
        quantity = max(0, int(quantity_raw or 0))
        price = Decimal(price_raw)
        discounted_price = Decimal(discounted_raw) if discounted_raw else None
    except (ValueError, InvalidOperation):
        return None, "Invalid price or quantity format."

    if product_id:
        product = get_object_or_404(Product, pk=product_id)
        if Product.objects.exclude(pk=product.pk).filter(barcode=barcode).exists():
            return None, f"Another product with barcode '{barcode}' already exists."
        product.barcode = barcode
        product.name = name
        product.variant = variant
        product.quantity = quantity
        product.price = price
        product.discounted_price = discounted_price
        product.save()
        return product, None

    product, _ = Product.objects.update_or_create(
        barcode=barcode,
        defaults={
            'name': name,
            'variant': variant,
            'quantity': quantity,
            'price': price,
            'discounted_price': discounted_price,
        }
    )
    return product, None


def _build_product_sales_rows():
    products = Product.objects.annotate(
        units_sold=Sum('sales__quantity_sold'),
        revenue=Sum('sales__total_amount'),
        last_sold=Max('sales__sold_at'),
    ).order_by('-revenue', '-updated_at')

    rows = []
    for p in products:
        selling_price = p.discounted_price if p.discounted_price is not None else p.price
        units_sold = p.units_sold or 0
        revenue = p.revenue or Decimal('0.00')
        last_sold_str = localtime(p.last_sold).strftime('%Y-%m-%d %H:%M:%S') if p.last_sold else 'No sales yet'
        rows.append({
            'id': p.id,
            'barcode': p.barcode,
            'name': p.name,
            'variant': p.variant or '—',
            'selling_price': f"{selling_price:.2f}",
            'stock': p.quantity,
            'units_sold': units_sold,
            'revenue': f"{revenue:.2f}",
            'last_sold': last_sold_str,
        })
    return rows


def analytics_view(request):
    products = Product.objects.all()
    total_products = products.count()
    total_stock = products.aggregate(total=Sum('quantity'))['total'] or 0
    in_stock_count = products.filter(quantity__gt=5).count()
    low_stock_count = products.filter(quantity__gt=0, quantity__lte=5).count()
    out_of_stock_count = products.filter(quantity=0).count()

    total_value = sum(
        (p.discounted_price if p.discounted_price is not None else p.price) * p.quantity
        for p in products
    )
    total_sales_revenue = Sale.objects.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

    top_products = list(products.order_by('-quantity')[:8])
    chart_labels = [
        f"{p.name} ({p.variant})" if p.variant else p.name
        for p in top_products
    ]
    chart_quantities = [p.quantity for p in top_products]
    chart_prices = [float(p.price) for p in top_products]
    chart_discounted_prices = [
        float(p.discounted_price if p.discounted_price is not None else p.price)
        for p in top_products
    ]

    product_sales_rows = _build_product_sales_rows()

    return render(request, 'Pages/Analytics.html', {
        'page_title': 'Analytics',
        'current_page': 'analytics',
        'total_products': total_products,
        'total_stock': total_stock,
        'low_stock_count': low_stock_count + out_of_stock_count,
        'total_value': total_value,
        'total_sales_revenue': total_sales_revenue,
        'product_sales_rows': product_sales_rows,
        'chart_data': {
            'labels': chart_labels,
            'quantities': chart_quantities,
            'prices': chart_prices,
            'discounted_prices': chart_discounted_prices,
            'status_counts': [in_stock_count, low_stock_count, out_of_stock_count],
        },
    })


def realtime_sales_api(request):
    rows = _build_product_sales_rows()
    total_sales_revenue = Sale.objects.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    total_units_sold = Sale.objects.aggregate(total=Sum('quantity_sold'))['total'] or 0
    return JsonResponse({
        'rows': rows,
        'total_sales_revenue': f"{total_sales_revenue:.2f}",
        'total_units_sold': total_units_sold,
    })


def inventory_view(request):
    error = None
    edit_product = None

    edit_id = request.GET.get('edit')
    if edit_id:
        edit_product = Product.objects.filter(pk=edit_id).first()

    if request.method == 'POST':
        product, error = _save_product_from_post(request)
        if product and not error:
            return redirect('inventory')

    products = Product.objects.all()
    total_stock = products.aggregate(total=Sum('quantity'))['total'] or 0
    low_stock_count = products.filter(quantity__lte=5).count()

    return render(request, 'Pages/Inventory.html', {
        'page_title': 'Inventory',
        'current_page': 'inventory',
        'products': products,
        'total_stock': total_stock,
        'low_stock_count': low_stock_count,
        'edit_product': edit_product,
        'error': error,
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


def sales_view(request):
    error = None
    if request.method == 'POST':
        barcode = request.POST.get('barcode', '').strip()
        qty_raw = request.POST.get('quantity_sold', '1').strip()
        try:
            qty = max(1, int(qty_raw or 1))
        except ValueError:
            qty = 1

        product = Product.objects.filter(barcode=barcode).first()
        if not product:
            error = f"No product found with barcode '{barcode}'."
        elif product.quantity < qty:
            error = f"Insufficient stock for {product.name} (Available: {product.quantity})."
        else:
            unit_price = product.discounted_price if product.discounted_price is not None else product.price
            total_amount = unit_price * qty
            Sale.objects.create(
                product=product,
                quantity_sold=qty,
                unit_price=unit_price,
                total_amount=total_amount,
            )
            product.quantity -= qty
            product.save()
            return redirect('sales')

    recent_sales = Sale.objects.select_related('product').all()[:30]
    products = Product.objects.all()
    total_revenue = Sale.objects.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    total_units_sold = Sale.objects.aggregate(total=Sum('quantity_sold'))['total'] or 0

    return render(request, 'Pages/Sales.html', {
        'page_title': 'Sales',
        'current_page': 'sales',
        'recent_sales': recent_sales,
        'products': products,
        'total_revenue': total_revenue,
        'total_units_sold': total_units_sold,
        'error': error,
    })
