"""
Fix tenant databases by recreating them with correct UUID schema
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'template_service.settings')
django.setup()

from scripts.tenant_models import TenantDatabaseInfo
from scripts.tenant_utils import create_postgresql_database, add_tenant_database_to_django
from django.core.management import call_command
from django.db import connections
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from django.conf import settings


def recreate_tenant_databases():
    """Recreate tenant databases with new UUID schema"""
    
    print("🔧 Fixing tenant databases with UUID schema...\n")
    
    # Get all tenants
    tenants = TenantDatabaseInfo.objects.all()
    
    for tenant in tenants:
        print(f"🔄 Recreating {tenant.tenant_slug} database...")
        
        try:
            # Drop and recreate database
            db_name = tenant.database_name
            db_user = tenant.database_user
            db_password = tenant.decrypt_password()
            
            # Connect to PostgreSQL
            conn = psycopg2.connect(
                host=settings.DATABASES['default']['HOST'],
                port=settings.DATABASES['default']['PORT'],
                user=settings.DATABASES['default']['USER'],
                password=settings.DATABASES['default']['PASSWORD'],
                database='postgres'
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Drop existing database
            cursor.execute(f"DROP DATABASE IF EXISTS {db_name};")
            print(f"   🗑️  Dropped database: {db_name}")
            
            # Create new database
            cursor.execute(f"CREATE DATABASE {db_name} OWNER {db_user};")
            print(f"   ✅ Created database: {db_name}")
            
            cursor.close()
            conn.close()
            
            # Add to Django connections
            add_tenant_database_to_django(tenant)
            
            # Run migrations with new schema
            connection_name = f"{tenant.tenant_slug}_compliance_db"
            
            # Remove old connection if exists
            if connection_name in connections.databases:
                if connection_name in connections._connections:
                    connections._connections[connection_name].close()
                    del connections._connections[connection_name]
            
            # Add fresh connection
            add_tenant_database_to_django(tenant)
            
            # Run migrations
            call_command(
                'migrate',
                'company_compliance',
                database=connection_name,
                verbosity=1,
                interactive=False
            )
            
            print(f"   ✅ Migrations completed for {tenant.tenant_slug}")
            
        except Exception as e:
            print(f"   ❌ Error recreating {tenant.tenant_slug}: {e}")
        
        print("-" * 50)
    
    print("\n🎉 All tenant databases recreated with UUID schema!")


if __name__ == '__main__':
    recreate_tenant_databases()