from django.db import models


class Product(models.Model):
    barcode = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    variant = models.CharField(max_length=150, blank=True, default='')
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    @property
    def is_low_stock(self):
        return 0 < self.quantity <= 5

    def __str__(self):
        if self.variant:
            return f"{self.barcode} - {self.name} ({self.variant})"
        return f"{self.barcode} - {self.name}"


class Sale(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sales')
    quantity_sold = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    sold_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sold_at']

    def __str__(self):
        return f"{self.product.name} x{self.quantity_sold} ({self.total_amount})"
