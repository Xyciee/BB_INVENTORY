from django.db import models


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('lips', 'LIPS'),
        ('face', 'FACE'),
        ('eyes', 'EYES'),
        ('bath_and_body', 'BATH AND BODY'),
        ('fragrance', 'FRAGRANCE'),
    ]

    barcode = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='lips')
    variant = models.CharField(max_length=255, blank=True, default='')
    image = models.FileField(upload_to='products/', blank=True, null=True)
    image_url = models.URLField(max_length=500, blank=True, default='')
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']

    @property
    def is_low_stock(self):
        return 0 < self.total_stock <= 5

    @property
    def selling_price(self):
        return self.discounted_price if self.discounted_price is not None else self.price

    @property
    def display_image(self):
        if self.image:
            return self.image.url
        return ''

    @property
    def total_stock(self):
        variants_qs = self.variants.all()
        if variants_qs.exists():
            return sum(v.stock for v in variants_qs)
        return self.quantity

    @property
    def variants_json(self):
        import json
        items = [{'id': v.id, 'name': v.name, 'stock': v.stock} for v in self.variants.all()]
        if not items:
            items = [{'id': '', 'name': 'Standard', 'stock': self.quantity}]
        return json.dumps(items)

    def __str__(self):
        return f"{self.barcode} - {self.name}"


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=150)
    stock = models.PositiveIntegerField(default=10)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.product.name} - {self.name} (Stock: {self.stock})"


class SalesOrder(models.Model):
    PAYMENT_CHOICES = [
        ('Cash', 'Cash'),
        ('GCash', 'GCash'),
        ('Maya', 'Maya'),
        ('Card', 'Credit/Debit Card'),
    ]

    order_number = models.CharField(max_length=50, unique=True)
    customer_name = models.CharField(max_length=150, default='Walk-in Customer', blank=True)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_CHOICES, default='Cash')
    total_items = models.PositiveIntegerField(default=1)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    change_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_number} - {self.customer_name} (\u20B1{self.total_amount})"

    @property
    def items_list(self):
        return self.items.select_related('product').all()


class Sale(models.Model):
    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='items', null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sales')
    variant_name = models.CharField(max_length=150, blank=True, default='')
    quantity_sold = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    sold_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sold_at']

    def __str__(self):
        return f"{self.product.name} ({self.variant_name}) x{self.quantity_sold}"
