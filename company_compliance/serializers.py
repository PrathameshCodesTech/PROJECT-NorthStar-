"""
Serializers for Company Compliance API
"""

from rest_framework import serializers
from .models import (
    CompanyFramework, CompanyControl, ControlAssignment,
    AssessmentCampaign, AssessmentResponse, EvidenceDocument,
    RemediationPlan, ComplianceReport
)


class CompanyFrameworkSerializer(serializers.ModelSerializer):
    """Serializer for Company Framework"""
    
    control_count = serializers.SerializerMethodField()
    
    def get_control_count(self, obj):
        return obj.controls.filter(is_active=True).count()
    
    class Meta:
        model = CompanyFramework
        fields = [
            'id', 'name', 'full_name', 'version', 'description',
            'template_framework_id', 'is_customized', 'customized_date',
            'activated_date', 'control_count'
        ]
        read_only_fields = ['id', 'activated_date']


class CompanyControlBasicSerializer(serializers.ModelSerializer):
    """Basic Company Control serializer for lists"""
    
    framework_name = serializers.CharField(source='framework.name', read_only=True)
    assignment_count = serializers.SerializerMethodField()
    
    def get_assignment_count(self, obj):
        return obj.assignments.count()
    
    class Meta:
        model = CompanyControl
        fields = [
            'id', 'control_code', 'title', 'control_type',
            'frequency', 'risk_level', 'framework_name',
            'assignment_count', 'is_active'
        ]
        read_only_fields = ['id']


class CompanyControlDetailSerializer(serializers.ModelSerializer):
    """Detailed Company Control serializer"""
    
    framework_name = serializers.CharField(source='framework.name', read_only=True)
    assignment_count = serializers.SerializerMethodField()
    completed_assignments = serializers.SerializerMethodField()
    
    def get_assignment_count(self, obj):
        return obj.assignments.count()
    
    def get_completed_assignments(self, obj):
        return obj.assignments.filter(status='COMPLETED').count()
    
    class Meta:
        model = CompanyControl
        fields = [
            'id', 'framework', 'control_code', 'title', 'description',
            'objective', 'template_control_id', 'is_customized',
            'custom_description', 'custom_objective', 'custom_questions',
            'control_type', 'frequency', 'risk_level', 'sort_order',
            'framework_name', 'assignment_count', 'completed_assignments',
            'is_active'
        ]
        read_only_fields = ['id']


class ControlAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for Control Assignments"""
    
    control_code = serializers.CharField(source='control.control_code', read_only=True)
    control_title = serializers.CharField(source='control.title', read_only=True)
    framework_name = serializers.CharField(source='control.framework.name', read_only=True)
    
    class Meta:
        model = ControlAssignment
        fields = [
            'id', 'control', 'assigned_to_employee_id', 'assigned_by_employee_id',
            'assignment_date', 'due_date', 'status', 'priority', 'notes',
            'control_code', 'control_title', 'framework_name'
        ]
        read_only_fields = ['id', 'assignment_date']


class AssessmentCampaignSerializer(serializers.ModelSerializer):
    """Serializer for Assessment Campaigns"""
    
    framework_name = serializers.CharField(source='framework.name', read_only=True)
    
    class Meta:
        model = AssessmentCampaign
        fields = [
            'id', 'campaign_name', 'framework', 'start_date', 'end_date',
            'status', 'created_by_employee_id', 'created_date', 'description',
            'framework_name'
        ]
        read_only_fields = ['id', 'created_date']


class AssessmentResponseSerializer(serializers.ModelSerializer):
    """Serializer for Assessment Responses"""
    
    control_code = serializers.CharField(source='assignment.control.control_code', read_only=True)
    campaign_name = serializers.CharField(source='campaign.campaign_name', read_only=True)
    
    class Meta:
        model = AssessmentResponse
        fields = [
            'id', 'assignment', 'campaign', 'question_id', 'question_text',
            'question_type', 'answer', 'answered_by_employee_id',
            'answered_date', 'confidence_level', 'comments',
            'control_code', 'campaign_name'
        ]
        read_only_fields = ['id', 'answered_date']


class EvidenceDocumentSerializer(serializers.ModelSerializer):
    """Serializer for Evidence Documents"""
    
    control_code = serializers.CharField(source='assignment.control.control_code', read_only=True)
    
    class Meta:
        model = EvidenceDocument
        fields = [
            'id', 'assignment', 'evidence_requirement_id', 'document_name',
            'original_filename', 'file_path', 'file_size_mb', 'file_type',
            'uploaded_by_employee_id', 'upload_date', 'status',
            'reviewed_by_employee_id', 'review_date', 'review_comments',
            'control_code'
        ]
        read_only_fields = ['id', 'upload_date']


class RemediationPlanSerializer(serializers.ModelSerializer):
    """Serializer for Remediation Plans"""
    
    control_code = serializers.CharField(source='assignment.control.control_code', read_only=True)
    
    class Meta:
        model = RemediationPlan
        fields = [
            'id', 'assignment', 'gap_description', 'root_cause',
            'remediation_steps', 'target_completion_date', 'actual_completion_date',
            'status', 'priority', 'created_by_employee_id', 'assigned_to_employee_id',
            'created_date', 'updated_date', 'control_code'
        ]
        read_only_fields = ['id', 'created_date', 'updated_date']


class ComplianceReportSerializer(serializers.ModelSerializer):
    """Serializer for Compliance Reports"""
    
    framework_name = serializers.CharField(source='framework.name', read_only=True)
    campaign_name = serializers.CharField(source='campaign.campaign_name', read_only=True)
    
    class Meta:
        model = ComplianceReport
        fields = [
            'id', 'report_name', 'report_type', 'framework', 'campaign',
            'generated_date', 'generated_by_employee_id', 'overall_compliance_rate',
            'total_controls', 'completed_controls', 'report_data', 'file_path',
            'framework_name', 'campaign_name'
        ]
        read_only_fields = ['id', 'generated_date']