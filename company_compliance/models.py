"""
Models for Company-specific Compliance Operations
These models exist in TENANT databases (techcorp_db, microsoft_db, etc.)
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils import timezone
import uuid


class BaseModel(models.Model):
    """Abstract base model with common fields"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class CompanyFramework(models.Model):
    """Company's copy of framework (customizable)"""
    name = models.CharField(max_length=100)  # "SOX"
    full_name = models.CharField(max_length=200)  # "Sarbanes-Oxley Act"
    version = models.CharField(max_length=50)  # "2024.1"
    template_framework_id = models.UUIDField() # References templates.Framework
    is_customized = models.BooleanField(default=False)
    customized_date = models.DateTimeField(null=True, blank=True)
    activated_date = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'company_frameworks'
        ordering = ['name', 'version']

    def __str__(self):
        return f"{self.name} v{self.version}"


class CompanyDomain(models.Model):
    """Company's copy of domain (customizable)"""
    framework = models.ForeignKey(
        CompanyFramework, 
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='domains'
    )
    template_domain_id = models.UUIDField()  # References templates.Domain
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    description = models.TextField(blank=True)
    sort_order = models.IntegerField(default=1)
    
    # Customization fields
    is_customized = models.BooleanField(default=False)
    custom_description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'company_domains'
        ordering = ['framework', 'sort_order', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['framework', 'code'],
                condition=models.Q(framework__isnull=False),
                name='unique_company_domain_code_per_framework'
            )
        ]

    def __str__(self):
        fw = self.framework.name if self.framework_id else "Unlinked"
        return f"{fw} - {self.name}"



class CompanyCategory(models.Model):
    """Company's copy of category (customizable)"""
    domain = models.ForeignKey(
        CompanyDomain,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='categories'
    )
    template_category_id = models.UUIDField()  # References templates.Category
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    description = models.TextField(blank=True)
    sort_order = models.IntegerField(default=1)
    
    # Customization fields
    is_customized = models.BooleanField(default=False)
    custom_description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'company_categories'
        ordering = ['domain', 'sort_order', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['domain', 'code'],
                condition=models.Q(domain__isnull=False),
                name='unique_company_category_code_per_domain'
            )
        ]

    def __str__(self):
        dom = self.domain
        fw = dom.framework.name if (dom and dom.framework_id) else "Unlinked"
        return f"{fw} - {self.name}"



class CompanySubcategory(models.Model):
    """Company's copy of subcategory (customizable)"""
    category = models.ForeignKey(
        CompanyCategory,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='subcategories'
    )
    template_subcategory_id = models.UUIDField()  # References templates.Subcategory
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    description = models.TextField(blank=True)
    sort_order = models.IntegerField(default=1)
    
    # Customization fields
    is_customized = models.BooleanField(default=False)
    custom_description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'company_subcategories'
        ordering = ['category', 'sort_order', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['category', 'code'],
                condition=models.Q(category__isnull=False),
                name='unique_company_subcategory_code_per_category'
            )
        ]

    def __str__(self):
        cat = self.category
        dom = cat.domain if cat else None
        fw = dom.framework.name if (dom and dom.framework_id) else "Unlinked"
        return f"{fw} - {self.name}"



class CompanyControl(models.Model):
    """Company's copy of control (customizable)"""
    subcategory = models.ForeignKey(
        CompanySubcategory, 
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='controls'
    )
    control_code = models.CharField(max_length=20)  # "AC-001"
    title = models.CharField(max_length=200)
    description = models.TextField()
    objective = models.TextField()
    
    # Reference to original template
    template_control_id = models.UUIDField()  # References templates.Control
    # Customization fields
    is_customized = models.BooleanField(default=False)
    custom_description = models.TextField(blank=True)
    custom_objective = models.TextField(blank=True)
    custom_questions = models.JSONField(default=list)  # Company-specific additions
    
    # Control properties
    control_type = models.CharField(max_length=20, choices=[
        ('PREVENTIVE', 'Preventive'),
        ('DETECTIVE', 'Detective'),
        ('CORRECTIVE', 'Corrective'),
    ], default='PREVENTIVE')
    
    frequency = models.CharField(max_length=20, choices=[
        ('CONTINUOUS', 'Continuous'),
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('ANNUALLY', 'Annually'),
    ], default='MONTHLY')
    
    risk_level = models.CharField(max_length=10, choices=[
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
    ], default='MEDIUM')
    
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=1)
    
    class Meta:
        db_table = 'company_controls'
        ordering = ['subcategory', 'sort_order', 'control_code']
        constraints = [
            models.UniqueConstraint(
                fields=['subcategory', 'control_code'],
                condition=models.Q(subcategory__isnull=False),
                name='unique_company_control_code_per_subcategory'
            )
        ]

    def __str__(self):
        return f"{self.control_code} - {self.title}"


class ControlAssignment(models.Model):
    """Assignment of control to employee"""
    control = models.ForeignKey(CompanyControl, on_delete=models.CASCADE, related_name='assignments')
    
    @property 
    def framework(self):
        """Helper property to get framework through hierarchy"""
        return self.control.subcategory.category.domain.framework
    
    # Employee references (external system IDs)
    assigned_to_employee_id = models.IntegerField()  # References external HR system
    assigned_by_employee_id = models.IntegerField()  # Admin who assigned
    
    # Assignment details
    assignment_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    
    status = models.CharField(max_length=20, choices=[
        ('NOT_STARTED', 'Not Started'),
        ('IN_PROGRESS', 'In Progress'),
        ('PENDING_REVIEW', 'Pending Review'),
        ('COMPLETED', 'Completed'),
        ('NEEDS_REMEDIATION', 'Needs Remediation'),
        ('OVERDUE', 'Overdue'),
    ], default='NOT_STARTED')
    
    priority = models.CharField(max_length=10, choices=[
        ('CRITICAL', 'Critical'),
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
    ], default='MEDIUM')
    
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'control_assignments'
        ordering = ['-assignment_date']
        unique_together = ['control', 'assigned_to_employee_id']  # One assignment per employee per control

    def __str__(self):
        return f"{self.control.control_code} → Employee {self.assigned_to_employee_id}"


class AssessmentCampaign(models.Model):
    """Quarterly/Annual assessment campaigns"""
    campaign_name = models.CharField(max_length=200)  # "Q1 2025 SOX Assessment"
    framework = models.ForeignKey(CompanyFramework, on_delete=models.CASCADE, related_name='campaigns')
    
    start_date = models.DateField()
    end_date = models.DateField()
    
    status = models.CharField(max_length=20, choices=[
        ('PLANNING', 'Planning'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ], default='PLANNING')
    
    created_by_employee_id = models.IntegerField()  # Admin who created
    created_date = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'assessment_campaigns'
        ordering = ['-created_date']

    def __str__(self):
        return f"{self.campaign_name} ({self.framework.name})"


class AssessmentResponse(models.Model):
    """Employee's answers to assessment questions"""
    assignment = models.ForeignKey(ControlAssignment, on_delete=models.CASCADE, related_name='responses')
    campaign = models.ForeignKey(AssessmentCampaign, on_delete=models.CASCADE, null=True, blank=True)
    
    # Question reference (from template)
    question_id = models.UUIDField() # References templates.AssessmentQuestion
    question_text = models.TextField()  # Snapshot of question at time of response
    question_type = models.CharField(max_length=20)
    
    # Response data
    answer = models.TextField()
    answered_by_employee_id = models.IntegerField()
    answered_date = models.DateTimeField(auto_now_add=True)
    
    confidence_level = models.CharField(max_length=10, choices=[
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
    ], default='MEDIUM')
    
    comments = models.TextField(blank=True)
    
    class Meta:
        db_table = 'assessment_responses'
        ordering = ['assignment', 'question_id']
        unique_together = ['assignment', 'question_id']

    def __str__(self):
        return f"{self.assignment.control.control_code} - Q{self.question_id}"


class EvidenceDocument(models.Model):
    """Evidence files uploaded by employees"""
    assignment = models.ForeignKey(ControlAssignment, on_delete=models.CASCADE, related_name='evidence')
    evidence_requirement_id = models.UUIDField() # References templates.EvidenceRequirement
    
    # Document details
    document_name = models.CharField(max_length=300)
    original_filename = models.CharField(max_length=300)
    file_path = models.CharField(max_length=500)  # Path in storage
    file_size_mb = models.DecimalField(max_digits=10, decimal_places=2)
    file_type = models.CharField(max_length=50)  # pdf, docx, xlsx, etc.
    
    # Upload details
    uploaded_by_employee_id = models.IntegerField()
    upload_date = models.DateTimeField(auto_now_add=True)
    
    # Review status
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('NEEDS_UPDATE', 'Needs Update'),
    ], default='PENDING')
    
    reviewed_by_employee_id = models.IntegerField(null=True, blank=True)
    review_date = models.DateTimeField(null=True, blank=True)
    review_comments = models.TextField(blank=True)
    
    class Meta:
        db_table = 'evidence_documents'
        ordering = ['-upload_date']

    def __str__(self):
        return f"{self.assignment.control.control_code} - {self.document_name}"


class RemediationPlan(models.Model):
    """Plan to fix compliance gaps"""
    assignment = models.ForeignKey(ControlAssignment, on_delete=models.CASCADE, related_name='remediation_plans')
    
    # Gap details
    gap_description = models.TextField()  # What's wrong
    root_cause = models.TextField(blank=True)  # Why it happened
    
    # Remediation details
    remediation_steps = models.TextField()  # How to fix it
    target_completion_date = models.DateField()
    actual_completion_date = models.DateField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=[
        ('PLANNED', 'Planned'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('DELAYED', 'Delayed'),
        ('CANCELLED', 'Cancelled'),
    ], default='PLANNED')
    
    priority = models.CharField(max_length=10, choices=[
        ('CRITICAL', 'Critical'),
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
    ], default='MEDIUM')
    
    # Assignment details
    created_by_employee_id = models.IntegerField()
    assigned_to_employee_id = models.IntegerField()
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'remediation_plans'
        ordering = ['-created_date']

    def __str__(self):
        return f"{self.assignment.control.control_code} - Remediation"


class ComplianceReport(models.Model):
    """Generated compliance reports"""
    report_name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=[
        ('DASHBOARD', 'Dashboard Summary'),
        ('EXECUTIVE', 'Executive Report'),
        ('DETAILED', 'Detailed Assessment'),
        ('GAP_ANALYSIS', 'Gap Analysis'),
        ('AUDIT_TRAIL', 'Audit Trail'),
    ])
    
    framework = models.ForeignKey(CompanyFramework, on_delete=models.CASCADE, related_name='reports')
    campaign = models.ForeignKey(AssessmentCampaign, on_delete=models.CASCADE, null=True, blank=True)
    
    # Report data
    generated_date = models.DateTimeField(auto_now_add=True)
    generated_by_employee_id = models.IntegerField()
    
    # Metrics
    overall_compliance_rate = models.DecimalField(max_digits=5, decimal_places=2)
    total_controls = models.IntegerField()
    completed_controls = models.IntegerField()
    
    # Report content
    report_data = models.JSONField()  # Detailed report data
    file_path = models.CharField(max_length=500, blank=True)  # If exported to PDF/Excel
    
    class Meta:
        db_table = 'compliance_reports'
        ordering = ['-generated_date']

    def __str__(self):
        return f"{self.report_name} - {self.generated_date.strftime('%Y-%m-%d')}"
    
    
class TenantUser(models.Model):
    """Tenant-specific user storage for ISOLATED residency mode"""
    
    ROLE_CHOICES = [
        ('TENANT_ADMIN', 'Tenant Admin'),
        ('COMPLIANCE_MANAGER', 'Compliance Manager'),
        ('AUDITOR', 'Auditor'),
        ('EMPLOYEE', 'Employee'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField()
    password_hash = models.CharField(max_length=128)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='EMPLOYEE')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'tenant_users'
        ordering = ['username']