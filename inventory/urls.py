from django.urls import path
from . import views

urlpatterns = [
    path('', views.analytics_view, name='analytics'),
    path('analytics/', views.analytics_view, name='analytics_page'),
    path('inventory/', views.inventory_view, name='inventory'),
    path('inventory/stock/<int:pk>/', views.update_stock, name='update_stock'),
    path('inventory/variant-stock/<int:variant_id>/', views.update_variant_stock, name='update_variant_stock'),
    path('inventory/delete/<int:pk>/', views.delete_product, name='delete_product'),
    path('inventory/import/', views.import_inventory, name='import_inventory'),
    path('inventory/download-template/', views.download_sample_template, name='download_sample_template'),
    path('api/barcode/<str:barcode>/', views.barcode_lookup, name='barcode_lookup'),
    path('api/realtime-sales/', views.realtime_sales_api, name='realtime_sales_api'),
    path('api/checkout/', views.checkout_api, name='checkout_api'),
    path('sales/', views.sales_view, name='sales'),
    path('sales/void/<int:order_id>/', views.void_sales_order, name='void_sales_order'),
    path('sales/export/', views.export_sales_csv, name='export_sales_csv'),
]
