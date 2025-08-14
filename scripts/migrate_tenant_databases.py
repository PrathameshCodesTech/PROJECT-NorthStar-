"""
Manually migrate tenant databases
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'template_service.settings')
django.setup()

from scripts.tenant_utils import load_all_tenant_databases
from django.core.management import call_command
from scripts.tenant_models import TenantDatabaseInfo


def migrate_all_tenants():
    """Run migrations on all tenant databases"""
    
    print("🔄 Migrating all tenant databases...\n")
    
    # Load tenant databases
    load_all_tenant_databases()
    
    # Get all tenants
    tenants = TenantDatabaseInfo.objects.filter(is_active=True)
    
    for tenant in tenants:
        db_name = f"{tenant.tenant_slug}_compliance_db"
        print(f"🔄 Migrating {db_name}...")
        
        try:
            call_command(
                'migrate',
                'company_compliance',
                database=db_name,
                verbosity=2,
                interactive=False
            )
            print(f"✅ Migration completed for {db_name}")
            
        except Exception as e:
            print(f"❌ Migration failed for {db_name}: {e}")
        
        print("-" * 50)
    
    print("\n🎉 All tenant migrations complete!")


if __name__ == '__main__':
    migrate_all_tenants()