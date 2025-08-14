"""
Test script to create tenant databases
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'template_service.settings')
django.setup()

from scripts.tenant_utils import (
    generate_database_credentials, 
    create_postgresql_database,
    register_tenant_database
)
from scripts.tenant_models import TenantDatabaseInfo


def create_test_tenants():
    """Create test tenant databases"""
    
    print("🚀 Creating test tenant databases...\n")
    
    # Create TechCorp tenant
    try:
        print("Creating TechCorp...")
        techcorp = register_tenant_database(
            tenant_slug='techcorp',
            company_name='TechCorp Inc.',
            subscription_plan='ENTERPRISE'
        )
        print(f"✅ TechCorp tenant created successfully!")
        print(f"   Database: {techcorp.database_name}")
        print(f"   User: {techcorp.database_user}")
        
    except Exception as e:
        print(f"❌ Error creating TechCorp: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Create DemoCorp tenant
    try:
        print("Creating DemoCorp...")
        democorp = register_tenant_database(
            tenant_slug='democorp',
            company_name='Demo Corporation',
            subscription_plan='PROFESSIONAL'
        )
        print(f"✅ DemoCorp tenant created successfully!")
        print(f"   Database: {democorp.database_name}")
        print(f"   User: {democorp.database_user}")
        
    except Exception as e:
        print(f"❌ Error creating DemoCorp: {e}")
    
    print("\n" + "="*50)
    print("📋 Tenant Summary:")
    
    # List all tenants
    for tenant in TenantDatabaseInfo.objects.all():
        print(f"   • {tenant.company_name} ({tenant.tenant_slug})")
        print(f"     Database: {tenant.database_name}")
        print(f"     Status: {tenant.status}")
    
    print("\n🎉 Tenant creation test complete!")


if __name__ == '__main__':
    create_test_tenants()