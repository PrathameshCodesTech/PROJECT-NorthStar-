"""
Complete fresh start for multi-tenant system
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'template_service.settings')
django.setup()

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from django.conf import settings
from scripts.tenant_models import TenantDatabaseInfo
from scripts.tenant_utils import register_tenant_database, copy_framework_templates_to_tenant


def complete_fresh_start():
    """Complete fresh start - drop everything and recreate"""
    
    print("🚀 COMPLETE FRESH START - Multi-Tenant System\n")
    
    # Step 1: Drop all tenant databases from PostgreSQL
    print("🗑️  Step 1: Dropping All Tenant Databases")
    drop_all_tenant_databases()
    
    # Step 2: Delete all tenant records from main database
    print("\n🗑️  Step 2: Deleting Tenant Records")
    deleted_count = TenantDatabaseInfo.objects.all().delete()[0]
    print(f"   ✅ Deleted {deleted_count} tenant records")
    
    # Step 3: Create fresh tenant databases
    print("\n🏗️  Step 3: Creating Fresh Tenant Databases")
    create_fresh_tenants()
    
    # Step 4: Test template distribution
    print("\n📋 Step 4: Testing Template Distribution")
    test_template_distribution()
    
    print("\n🎉 Fresh start complete!")


def drop_all_tenant_databases():
    """Drop all tenant-related databases and users from PostgreSQL"""
    
    # Get existing tenant info before deleting records
    existing_tenants = list(TenantDatabaseInfo.objects.all().values('tenant_slug', 'database_name', 'database_user'))
    
    if not existing_tenants:
        print("   ℹ️  No existing tenants found")
        return
    
    # Connect to PostgreSQL as superuser
    try:
        conn = psycopg2.connect(
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        for tenant in existing_tenants:
            try:
                # Drop database
                cursor.execute(f"DROP DATABASE IF EXISTS {tenant['database_name']};")
                print(f"   🗑️  Dropped database: {tenant['database_name']}")
                
                # Drop user
                cursor.execute(f"DROP USER IF EXISTS {tenant['database_user']};")
                print(f"   🗑️  Dropped user: {tenant['database_user']}")
                
            except Exception as e:
                print(f"   ⚠️  Error dropping {tenant['tenant_slug']}: {e}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Error connecting to PostgreSQL: {e}")


def create_fresh_tenants():
    """Create fresh tenant databases with correct schema"""
    
    tenants_to_create = [
        {
            'slug': 'techcorp',
            'name': 'TechCorp Inc.',
            'plan': 'ENTERPRISE'
        },
        {
            'slug': 'democorp', 
            'name': 'Demo Corporation',
            'plan': 'PROFESSIONAL'
        }
    ]
    
    created_tenants = []
    
    for tenant_data in tenants_to_create:
        try:
            print(f"   🏗️  Creating {tenant_data['name']}...")
            
            tenant_info = register_tenant_database(
                tenant_slug=tenant_data['slug'],
                company_name=tenant_data['name'],
                subscription_plan=tenant_data['plan']
            )
            
            created_tenants.append(tenant_info)
            print(f"   ✅ {tenant_data['name']} created successfully")
            
        except Exception as e:
            print(f"   ❌ Error creating {tenant_data['name']}: {e}")
        
        print("-" * 40)
    
    print(f"\n✅ Created {len(created_tenants)} tenant databases")
    return created_tenants


def test_template_distribution():
    """Test distributing SOX framework to tenant databases"""
    
    print("📋 Testing Template Distribution...")
    
    # Distribute to TechCorp
    print("\n   🏢 Distributing to TechCorp:")
    try:
        techcorp_result = copy_framework_templates_to_tenant('techcorp')
        print(f"   ✅ TechCorp distribution: {len(techcorp_result)} frameworks copied")
    except Exception as e:
        print(f"   ❌ TechCorp distribution failed: {e}")
    
    # Distribute to DemoCorp
    print("\n   🏢 Distributing to DemoCorp:")
    try:
        democorp_result = copy_framework_templates_to_tenant('democorp')
        print(f"   ✅ DemoCorp distribution: {len(democorp_result)} frameworks copied")
    except Exception as e:
        print(f"   ❌ DemoCorp distribution failed: {e}")


if __name__ == '__main__':
    complete_fresh_start()