"""
Simple tenant database recreation
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'template_service.settings')
django.setup()

from scripts.tenant_models import TenantDatabaseInfo
from scripts.tenant_utils import register_tenant_database


def recreate_tenants_simple():
    """Delete and recreate tenant databases"""
    
    print("🔄 Recreating tenant databases...\n")
    
    # Delete existing tenant records
    TenantDatabaseInfo.objects.all().delete()
    print("🗑️  Deleted existing tenant records")
    
    # Recreate TechCorp
    try:
        techcorp = register_tenant_database(
            tenant_slug='techcorp',
            company_name='TechCorp Inc.',
            subscription_plan='ENTERPRISE'
        )
        print(f"✅ TechCorp recreated successfully")
    except Exception as e:
        print(f"❌ Error recreating TechCorp: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Recreate DemoCorp
    try:
        democorp = register_tenant_database(
            tenant_slug='democorp',
            company_name='Demo Corporation',
            subscription_plan='PROFESSIONAL'
        )
        print(f"✅ DemoCorp recreated successfully")
    except Exception as e:
        print(f"❌ Error recreating DemoCorp: {e}")
    
    print("\n🎉 Tenant recreation complete!")


if __name__ == '__main__':
    recreate_tenants_simple()