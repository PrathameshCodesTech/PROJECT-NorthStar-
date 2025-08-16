"""
Template Distribution Utilities - Service 1
Only handles framework template copying, not tenant provisioning
"""

from django.db import connections
from templates.models import Framework, Domain, Category, Subcategory, Control
from company_compliance.models import CompanyFramework, CompanyControl
from template_service.database_router import set_current_tenant, clear_current_tenant, get_current_tenant


def copy_framework_templates_to_tenant(tenant_slug, framework_ids=None):
    """Copy framework templates from main DB to tenant DB"""
    print(f"\n📋 Starting template distribution to {tenant_slug}...")

    # Always clear to read templates from MAIN
    clear_current_tenant()

    # Read frameworks from MAIN (this is where errors would appear if schema is off)
# IMPORTANT: distinguish None (copy ALL) vs [] (copy NONE)
    if framework_ids is None:
        frameworks = Framework.objects.filter(is_active=True)
    elif len(framework_ids) == 0:
        frameworks = Framework.objects.none()
    else:
        frameworks = Framework.objects.filter(id__in=framework_ids, is_active=True)


    count = frameworks.count()
    print(f"📦 Found {count} frameworks to copy")

    # Switch to tenant DB to write
    set_current_tenant(tenant_slug)
    copied_frameworks = []

    try:
        for framework in frameworks:
            print(f"\n🔄 Copying framework: {framework.name} v{framework.version}")
            
            try:
                # Check if framework already exists in tenant DB
                existing = CompanyFramework.objects.filter(
                    name=framework.name, 
                    version=framework.version
                ).first()
                
                if existing:
                    print(f"   ⚠️  Framework already exists, skipping...")
                    continue
                
                # Create company framework
                company_framework = CompanyFramework.objects.create(
                    name=framework.name,
                    full_name=framework.full_name,
                    version=framework.version,
                    template_framework_id=framework.id,  # Reference to template
                    description=framework.description
                )
                
                print(f"   ✅ Created company framework: {company_framework.name}")
                
                # Copy all controls from this framework
                controls_copied = copy_framework_controls(framework, company_framework)
                
                copied_frameworks.append({
                    'framework': company_framework,
                    'controls_copied': controls_copied
                })
                
                print(f"   📊 Copied {controls_copied} controls")
                
            except Exception as e:
                print(f"   ❌ Error copying framework {framework.name}: {e}")
        
    finally:
        # Always clear regardless of success/failure
        clear_current_tenant()

    print(f"\n🎉 Template distribution complete!")
    ...
    return copied_frameworks



def copy_framework_controls(template_framework, company_framework):
    """Copy all controls from template framework to company framework"""
    
    # Get current tenant from context
    current_tenant = get_current_tenant()
    
    # Get all controls from template framework (main DB)
    clear_current_tenant()
    
    template_controls = Control.objects.filter(
        subcategory__category__domain__framework=template_framework,
        is_active=True
    ).select_related(
        'subcategory__category__domain'
    )
    
    controls_copied = 0
    
    # Switch back to tenant DB for writing
    if current_tenant:
        set_current_tenant(current_tenant)
    
    for template_control in template_controls:
        try:
            # Check if control already exists
            existing = CompanyControl.objects.filter(
                framework=company_framework,
                control_code=template_control.control_code
            ).first()
            
            if existing:
                continue
            
            # Create company control
            company_control = CompanyControl.objects.create(
                framework=company_framework,
                template_control_id=template_control.id,  # Now UUID
                control_code=template_control.control_code,
                title=template_control.title,
                description=template_control.description,
                objective=template_control.objective,
                control_type=template_control.control_type,
                frequency=template_control.frequency,
                risk_level=template_control.risk_level,
                sort_order=template_control.sort_order
            )
            
            controls_copied += 1
            
        except Exception as e:
            print(f"      ❌ Error copying control {template_control.control_code}: {e}")
    
    return controls_copied