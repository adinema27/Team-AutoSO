from django.urls import path
from . import views

urlpatterns = [
    path('', views.create_sales_order_view, name='create_order'),                  # Prompt form (start)
    path('order-summary/', views.order_summary_view, name='order_summary'),        # Review order
    path('manual-edit/', views.manual_edit_view, name='manual_edit'),              # Manual value edit
    path('final-sales-order/', views.final_sales_order_view, name='final_sales_order'),
]
