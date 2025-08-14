"""
Test template distribution from main DB to tenant databases
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'template_service.settings')
django.setup()

from scripts.tenant_utils import copy_framework_templates_to_tenant, load_all_tenant_databases
from template_service.database_router import set_current_tenant, clear_current_tenant
from templates.models import Framework
from company_compliance.models import CompanyFramework, CompanyControl


def test_template_distribution():
    """Test copying templates from main DB to tenant databases"""
    
    print("🚀 Testing Template Distribution System\n")
    
    # Check what templates exist in main database
    print("📋 Step 1: Check Main Database Templates")
    clear_current_tenant()
    
    main_frameworks = Framework.objects.filter(is_active=True)
    print(f"   Found {main_frameworks.count()} frameworks in main database:")
    
    for fw in main_frameworks:
        stats = fw.stats if hasattr(fw, 'stats') else {}
        control_count = stats.get('control_count', 0) if isinstance(stats, dict) else 0
        print(f"   • {fw.name} v{fw.version} ({control_count} controls)")
    
    if main_frameworks.count() == 0:
        print("   ⚠️  No frameworks found in main database!")
        print("   💡 You need to create frameworks in the templates app first")
        return
    
    print("\n" + "="*60 + "\n")
    
    # Distribute templates to TechCorp
    print("🏢 Step 2: Distribute Templates to TechCorp")
    
    techcorp_result = copy_framework_templates_to_tenant(
        tenant_slug='techcorp',
        framework_ids=None  # Copy all frameworks
    )
    
    print("\n" + "="*60 + "\n")
    
    # Distribute templates to DemoCorp  
    print("🏢 Step 3: Distribute Templates to DemoCorp")
    
    democorp_result = copy_framework_templates_to_tenant(
        tenant_slug='democorp',
        framework_ids=None  # Copy all frameworks
    )
    
    print("\n" + "="*60 + "\n")
    
    # Verify distribution worked
    print("🔍 Step 4: Verify Template Distribution")
    
    # Check TechCorp database
    print("\n📊 TechCorp Database:")
    set_current_tenant('techcorp')
    
    techcorp_frameworks = CompanyFramework.objects.all()
    print(f"   Frameworks: {techcorp_frameworks.count()}")
    
    for fw in techcorp_frameworks:
        control_count = CompanyControl.objects.filter(framework=fw).count()
        print(f"   • {fw.name} v{fw.version} ({control_count} controls)")
    
    # Check DemoCorp database
    print("\n📊 DemoCorp Database:")
    set_current_tenant('democorp')
    
    democorp_frameworks = CompanyFramework.objects.all()
    print(f"   Frameworks: {democorp_frameworks.count()}")
    
    for fw in democorp_frameworks:
        control_count = CompanyControl.objects.filter(framework=fw).count()
        print(f"   • {fw.name} v{fw.version} ({control_count} controls)")
    
    # Clear tenant context
    clear_current_tenant()
    
    print("\n" + "="*60)
    print("📈 DISTRIBUTION SUMMARY:")
    print(f"   Main DB: {main_frameworks.count()} template frameworks")
    print(f"   TechCorp: {techcorp_frameworks.count()} company frameworks")  
    print(f"   DemoCorp: {democorp_frameworks.count()} company frameworks")
    
    if techcorp_frameworks.count() > 0 and democorp_frameworks.count() > 0:
        print("   ✅ Template distribution successful!")
        print("   🎉 Multi-tenant template system is working!")
    else:
        print("   ⚠️  Template distribution may have issues")
    
    print("\n🏁 Template distribution test complete!")


if __name__ == '__main__':
    test_template_distribution()