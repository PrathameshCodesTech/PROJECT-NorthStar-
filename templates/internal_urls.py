"""
Internal API URLs for Service 1 - Inter-service communication
"""

from django.urls import path
from .internal_views import InternalMigrateTenantView, InternalDistributeTemplatesView

urlpatterns = [
    path('migrate-tenant/', 
         InternalMigrateTenantView.as_view(), 
         name='internal-migrate-tenant'),
    
    path('distribute-templates/', 
         InternalDistributeTemplatesView.as_view(), 
         name='internal-distribute-templates'),
]