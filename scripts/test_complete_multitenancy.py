"""
Test complete multi-tenant workflow with TechCorp
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'template_service.settings')
django.setup()

from template_service.database_router import set_current_tenant, clear_current_tenant
from scripts.tenant_utils import load_all_tenant_databases
from company_compliance.models import CompanyFramework, CompanyControl, ControlAssignment


def test_complete_multitenancy():
    """Test complete workflow in TechCorp tenant database"""
    
    print("🧪 Testing Complete Multi-Tenant Workflow\n")
    
    # Load tenant databases
    load_all_tenant_databases()
    
    # Test TechCorp workflow
    print("🏢 Testing TechCorp Tenant Operations:")
    set_current_tenant('techcorp')
    
    try:
        # Get TechCorp's frameworks
        frameworks = CompanyFramework.objects.all()
        print(f"   📋 TechCorp frameworks: {frameworks.count()}")
        
        if frameworks.exists():
            framework = frameworks.first()
            print(f"   • {framework.name} v{framework.version}")
            
            # Get TechCorp's controls
            controls = CompanyControl.objects.filter(framework=framework)
            print(f"   ⚙️  TechCorp controls: {controls.count()}")
            
            for control in controls:
                print(f"   • {control.control_code} - {control.title}")
            
            # Test assignment in TechCorp database
            if controls.exists():
                control = controls.first()
                print(f"\n   📝 Testing assignment in TechCorp database:")
                
                # Create assignment
                assignment = ControlAssignment.objects.create(
                    control=control,
                    assigned_to_employee_id=11111,  # TechCorp employee
                    assigned_by_employee_id=22222,  # TechCorp manager
                    due_date='2024-04-15',
                    status='NOT_STARTED',
                    priority='HIGH',
                    notes='TechCorp-specific assignment'
                )
                
                print(f"   ✅ Created assignment: {assignment.control.control_code} → Employee {assignment.assigned_to_employee_id}")
                
                # Check assignment count
                assignments = ControlAssignment.objects.all()
                print(f"   📊 Total TechCorp assignments: {assignments.count()}")
    
    except Exception as e:
        print(f"   ❌ Error in TechCorp operations: {e}")
    
    print("\n" + "="*60 + "\n")
    
    # Test DemoCorp isolation
    print("🏢 Testing DemoCorp Tenant Isolation:")
    set_current_tenant('democorp')
    
    try:
        # Check DemoCorp assignments (should be empty)
        assignments = ControlAssignment.objects.all()
        print(f"   📊 DemoCorp assignments: {assignments.count()}")
        
        if assignments.count() == 0:
            print("   ✅ Perfect isolation! DemoCorp can't see TechCorp's assignments")
        else:
            print("   ❌ Data isolation failed - DemoCorp can see TechCorp data")
    
    except Exception as e:
        print(f"   ❌ Error in DemoCorp operations: {e}")
    
    # Clear tenant context
    clear_current_tenant()
    
    print("\n🎉 Multi-tenant workflow test complete!")


if __name__ == '__main__':
    test_complete_multitenancy()