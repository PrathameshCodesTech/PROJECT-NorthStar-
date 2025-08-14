"""
Script to create SOX framework with sample data for testing
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'template_service.settings')
django.setup()

from templates.models import (
    Framework, Domain, Category, Subcategory, 
    Control, AssessmentQuestion, EvidenceRequirement
)
from template_service.database_router import clear_current_tenant


def create_sox_framework():
    """Create complete SOX framework with sample data"""
    
    print("🏗️  Creating SOX Framework in PostgreSQL...\n")
    
    # Ensure we're working with main database
    clear_current_tenant()
    
    # Check if SOX already exists
    existing_sox = Framework.objects.filter(name='SOX', version='2024.1').first()
    if existing_sox:
        print("⚠️  SOX framework already exists, deleting and recreating...")
        existing_sox.delete()
    
    # 1. Create Framework
    print("📋 Step 1: Creating SOX Framework")
    framework = Framework.objects.create(
        name='SOX',
        full_name='Sarbanes-Oxley Act',
        description='The Sarbanes-Oxley Act of 2002 compliance framework for financial reporting controls',
        version='2024.1',
        status='ACTIVE'
    )
    print(f"   ✅ Created framework: {framework.name} v{framework.version}")
    
    # 2. Create Domain
    print("\n🏢 Step 2: Creating ITGC Domain")
    domain = Domain.objects.create(
        framework=framework,
        name='IT General Controls',
        code='ITGC',
        description='IT General Controls for SOX compliance including access controls and change management',
        sort_order=1
    )
    print(f"   ✅ Created domain: {domain.name}")
    
    # 3. Create Category
    print("\n🔐 Step 3: Creating Access Controls Category")
    category = Category.objects.create(
        domain=domain,
        name='Access Controls',
        code='AC',
        description='Controls for managing user access to systems and data',
        sort_order=1
    )
    print(f"   ✅ Created category: {category.name}")
    
    # 4. Create Subcategory
    print("\n👤 Step 4: Creating User Access Management Subcategory")
    subcategory = Subcategory.objects.create(
        category=category,
        name='User Access Management',
        code='UAM',
        description='Controls for managing user account provisioning, modification, and termination',
        sort_order=1
    )
    print(f"   ✅ Created subcategory: {subcategory.name}")
    
    # 5. Create Controls
    print("\n⚙️  Step 5: Creating Controls")
    
    controls_data = [
        {
            'code': 'AC-001',
            'title': 'User Account Provisioning',
            'description': 'Ensure that user accounts are provisioned in accordance with established policies and procedures',
            'objective': 'To control access to systems and applications through proper user account creation and management',
            'type': 'PREVENTIVE',
            'frequency': 'MONTHLY',
            'risk': 'HIGH'
        },
        {
            'code': 'AC-002', 
            'title': 'User Account Termination',
            'description': 'Ensure that user accounts are properly terminated when employees leave or change roles',
            'objective': 'To prevent unauthorized access by former employees or users who have changed roles',
            'type': 'PREVENTIVE',
            'frequency': 'MONTHLY',
            'risk': 'HIGH'
        },
        {
            'code': 'AC-003',
            'title': 'Periodic Access Review',
            'description': 'Conduct periodic reviews of user access rights to ensure they remain appropriate',
            'objective': 'To ensure that users have only the access rights necessary for their current job functions',
            'type': 'DETECTIVE',
            'frequency': 'QUARTERLY',
            'risk': 'MEDIUM'
        }
    ]
    
    created_controls = []
    
    for i, control_data in enumerate(controls_data, 1):
        control = Control.objects.create(
            subcategory=subcategory,
            control_code=control_data['code'],
            title=control_data['title'],
            description=control_data['description'],
            objective=control_data['objective'],
            control_type=control_data['type'],
            frequency=control_data['frequency'],
            risk_level=control_data['risk'],
            sort_order=i
        )
        created_controls.append(control)
        print(f"   ✅ Created control: {control.control_code} - {control.title}")
    
    # 6. Create Assessment Questions
    print("\n❓ Step 6: Creating Assessment Questions")
    
    questions_data = [
        {
            'control': created_controls[0],  # AC-001
            'question': 'Are user accounts provisioned only after proper authorization and approval?',
            'type': 'YES_NO'
        },
        {
            'control': created_controls[0],  # AC-001
            'question': 'Is there a documented process for user account creation?',
            'type': 'YES_NO'
        },
        {
            'control': created_controls[1],  # AC-002
            'question': 'Are user accounts terminated within 24 hours of employee departure?',
            'type': 'YES_NO'
        },
        {
            'control': created_controls[2],  # AC-003
            'question': 'How frequently are access reviews conducted?',
            'type': 'MULTIPLE_CHOICE',
            'options': ['Monthly', 'Quarterly', 'Annually', 'Never']
        }
    ]
    
    for i, q_data in enumerate(questions_data, 1):
        question = AssessmentQuestion.objects.create(
            control=q_data['control'],
            question=q_data['question'],
            question_type=q_data['type'],
            options=q_data.get('options'),
            is_mandatory=True,
            sort_order=i
        )
        print(f"   ✅ Created question for {question.control.control_code}")
    
    # 7. Create Evidence Requirements
    print("\n📄 Step 7: Creating Evidence Requirements")
    
    evidence_data = [
        {
            'control': created_controls[0],  # AC-001
            'title': 'User Provisioning Report',
            'description': 'Monthly report showing all user accounts created with approval documentation',
            'type': 'REPORT'
        },
        {
            'control': created_controls[1],  # AC-002
            'title': 'User Termination Report',
            'description': 'Monthly report showing all user accounts terminated',
            'type': 'REPORT'
        },
        {
            'control': created_controls[2],  # AC-003
            'title': 'Access Review Documentation',
            'description': 'Quarterly access review reports with manager sign-offs',
            'type': 'DOCUMENT'
        }
    ]
    
    for i, e_data in enumerate(evidence_data, 1):
        evidence = EvidenceRequirement.objects.create(
            control=e_data['control'],
            title=e_data['title'],
            description=e_data['description'],
            evidence_type=e_data['type'],
            is_mandatory=True,
            file_format='PDF, Excel',
            sort_order=i
        )
        print(f"   ✅ Created evidence requirement for {evidence.control.control_code}")
    
    # 8. Display Summary
    print("\n" + "="*60)
    print("📊 SOX FRAMEWORK CREATION SUMMARY:")
    print(f"   Framework: {framework.name} v{framework.version}")
    print(f"   Domains: 1")
    print(f"   Categories: 1") 
    print(f"   Subcategories: 1")
    print(f"   Controls: {len(created_controls)}")
    print(f"   Assessment Questions: {len(questions_data)}")
    print(f"   Evidence Requirements: {len(evidence_data)}")
    
    print(f"\n🎉 SOX Framework created successfully!")
    print(f"   Framework ID: {framework.id}")
    
    return framework


if __name__ == '__main__':
    create_sox_framework()