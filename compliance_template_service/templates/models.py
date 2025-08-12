"""
Models for Template Service - Compliance Framework Management
"""

from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
import uuid
from datetime import date

class BaseModel(models.Model):
    """Abstract base model with common fields"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=100, default='system')
    updated_by = models.CharField(max_length=100, default='system')
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class Framework(BaseModel):
    """Top level - SOX, ISO 27001, NIST, etc."""
    
    name = models.CharField(
        max_length=50, 
        unique=True,
        help_text="Short name like 'SOX', 'ISO27001'"
    )
    full_name = models.CharField(
        max_length=200,
        help_text="Full name like 'Sarbanes-Oxley Act'"
    )
    description = models.TextField(blank=True)
    version = models.CharField(
        max_length=20,
        default="1.0",
        help_text="Version like '2024.1', '2022.1'"
    )
    effective_date = models.DateField(
    default=date.today,
    help_text="When this framework version becomes effective"
)
    status = models.CharField(
        max_length=20,
        choices=[
            ('DRAFT', 'Draft'),
            ('ACTIVE', 'Active'),
            ('DEPRECATED', 'Deprecated'),
        ],
        default='DRAFT'
    )
    
    class Meta:
        db_table = 'frameworks'
        ordering = ['name', 'version']

        constraints = [
            models.UniqueConstraint(
                fields=['name', 'version'], 
                name='unique_framework_name_version'
            )
        ]
        
    def __str__(self):
        return f"{self.name} v{self.version}"



class Domain(BaseModel):
    """Second level - IT General Controls, Application Controls, etc."""
    
    framework = models.ForeignKey(
        Framework, 
        on_delete=models.CASCADE, 
        related_name='domains'
    )
    name = models.CharField(max_length=100)
    code = models.CharField(
        max_length=10,
        help_text="Short code like 'ITGC', 'BPC'"
    )
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=1)
    
    class Meta:
        db_table = 'domains'
        ordering = ['framework', 'sort_order', 'name']
        unique_together = ['framework', 'code']
        # Enforce uniqueness within same framework
        constraints = [
            models.UniqueConstraint(
                fields=['framework', 'code'], 
                name='unique_domain_code_per_framework'
            ),
            models.UniqueConstraint(
                fields=['framework', 'name'], 
                name='unique_domain_name_per_framework'
            )
        ]
        
    def __str__(self):
        return f"{self.framework.name} - {self.name}"


class Category(BaseModel):
    """Third level - Access Controls, Change Management, etc."""
    
    domain = models.ForeignKey(
        Domain, 
        on_delete=models.CASCADE, 
        related_name='categories'
    )
    name = models.CharField(max_length=100)
    code = models.CharField(
        max_length=10,
        help_text="Short code like 'AC', 'CM'"
    )
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=1)
    
    class Meta:
        db_table = 'categories'
        ordering = ['domain', 'sort_order', 'name']
        unique_together = ['domain', 'code']
        verbose_name_plural = 'categories'
        constraints = [
            models.UniqueConstraint(
                fields=['domain', 'code'], 
                name='unique_category_code_per_domain'
            ),
            models.UniqueConstraint(
                fields=['domain', 'name'], 
                name='unique_category_name_per_domain'
            )
        ]

    def __str__(self):
        return f"{self.domain.framework.name} - {self.name}"


class Subcategory(BaseModel):
    """Fourth level - User Access Management, System Monitoring, etc."""
    
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name='subcategories'
    )
    name = models.CharField(max_length=100)
    code = models.CharField(
        max_length=10,
        help_text="Short code like 'UAM', 'SAM'"
    )
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=1)
    
    class Meta:
        db_table = 'subcategories'
        ordering = ['category', 'sort_order', 'name']
        unique_together = ['category', 'code']
        verbose_name_plural = 'subcategories'
        constraints = [
            models.UniqueConstraint(
                fields=['category', 'code'], 
                name='unique_subcategory_code_per_category'
            ),
            models.UniqueConstraint(
                fields=['category', 'name'], 
                name='unique_subcategory_name_per_category'
            )
        ]
    def __str__(self):
        return f"{self.category.domain.framework.name} - {self.name}"


class Control(BaseModel):
    """Fifth level - Actual controls like AC-001, CM-001, etc."""
    
    subcategory = models.ForeignKey(
        Subcategory, 
        on_delete=models.CASCADE, 
        related_name='controls'
    )
    control_code = models.CharField(
        max_length=20,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Z]{2,4}-\d{3}$',
                message='Control code must be like AC-001, CM-001'
            )
        ],
        help_text="Unique control code like 'AC-001'"
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    objective = models.TextField(
        help_text="What this control aims to achieve"
    )
    control_type = models.CharField(
        max_length=20,
        choices=[
            ('PREVENTIVE', 'Preventive'),
            ('DETECTIVE', 'Detective'),
            ('CORRECTIVE', 'Corrective'),
        ],
        default='PREVENTIVE'
    )
    frequency = models.CharField(
        max_length=20,
        choices=[
            ('CONTINUOUS', 'Continuous'),
            ('DAILY', 'Daily'),
            ('WEEKLY', 'Weekly'),
            ('MONTHLY', 'Monthly'),
            ('QUARTERLY', 'Quarterly'),
            ('ANNUALLY', 'Annually'),
        ],
        default='MONTHLY'
    )
    risk_level = models.CharField(
        max_length=10,
        choices=[
            ('HIGH', 'High'),
            ('MEDIUM', 'Medium'),
            ('LOW', 'Low'),
        ],
        default='MEDIUM'
    )
    sort_order = models.PositiveIntegerField(default=1)
    
    class Meta:
        db_table = 'controls'
        ordering = ['subcategory', 'sort_order', 'control_code']
        
    def __str__(self):
        return f"{self.control_code} - {self.title}"


class AssessmentQuestion(BaseModel):
    """Questions for each control during assessment"""
    
    control = models.ForeignKey(
        Control, 
        on_delete=models.CASCADE, 
        related_name='assessment_questions'
    )
    question = models.TextField()
    question_type = models.CharField(
        max_length=20,
        choices=[
            ('YES_NO', 'Yes/No'),
            ('MULTIPLE_CHOICE', 'Multiple Choice'),
            ('TEXT', 'Text Response'),
            ('NUMERIC', 'Numeric'),
            ('DATE', 'Date'),
        ],
        default='YES_NO'
    )
    options = models.JSONField(
        blank=True, 
        null=True,
        help_text="For multiple choice questions - list of options"
    )
    is_mandatory = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=1)
    
    class Meta:
        db_table = 'assessment_questions'
        ordering = ['control', 'sort_order']
        
    def __str__(self):
        return f"{self.control.control_code} - Q{self.sort_order}"


class EvidenceRequirement(BaseModel):
    """Evidence requirements for each control"""
    
    control = models.ForeignKey(
        Control, 
        on_delete=models.CASCADE, 
        related_name='evidence_requirements'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    evidence_type = models.CharField(
        max_length=20,
        choices=[
            ('DOCUMENT', 'Document'),
            ('SCREENSHOT', 'Screenshot'),
            ('VIDEO', 'Video'),
            ('LOG_FILE', 'Log File'),
            ('REPORT', 'Report'),
            ('POLICY', 'Policy'),
            ('PROCEDURE', 'Procedure'),
        ],
        default='DOCUMENT'
    )
    is_mandatory = models.BooleanField(default=True)
    file_format = models.CharField(
        max_length=50,
        blank=True,
        help_text="Accepted file formats like 'PDF, DOC, XLSX'"
    )
    sort_order = models.PositiveIntegerField(default=1)
    
    class Meta:
        db_table = 'evidence_requirements'
        ordering = ['control', 'sort_order']
        
    def __str__(self):
        return f"{self.control.control_code} - {self.title}"