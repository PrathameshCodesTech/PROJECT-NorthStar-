"""
API Views for Company Compliance Service
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count

from .models import (
    CompanyFramework, CompanyControl, ControlAssignment,
    AssessmentCampaign, AssessmentResponse, EvidenceDocument,
    RemediationPlan, ComplianceReport
)
from .serializers import (
    CompanyFrameworkSerializer, CompanyControlBasicSerializer,
    CompanyControlDetailSerializer, ControlAssignmentSerializer,
    AssessmentCampaignSerializer, AssessmentResponseSerializer,
    EvidenceDocumentSerializer, RemediationPlanSerializer,
    ComplianceReportSerializer
)


class CompanyFrameworkViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Company Frameworks
    """
    queryset = CompanyFramework.objects.all()
    serializer_class = CompanyFrameworkSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['name', 'version', 'is_customized']
    search_fields = ['name', 'full_name', 'description']
    ordering_fields = ['name', 'version', 'activated_date']
    ordering = ['name', 'version']
    
    @action(detail=True, methods=['get'])
    def controls(self, request, pk=None):
        """Get all controls for this framework"""
        framework = self.get_object()
        controls = framework.controls.filter(is_active=True).order_by('sort_order')
        serializer = CompanyControlBasicSerializer(controls, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get framework statistics"""
        framework = self.get_object()
        controls = framework.controls.filter(is_active=True)
        
        stats = {
            'framework_id': framework.id,
            'framework_name': framework.name,
            'total_controls': controls.count(),
            'assigned_controls': controls.filter(assignments__isnull=False).distinct().count(),
            'completed_assignments': ControlAssignment.objects.filter(
                control__framework=framework, status='COMPLETED'
            ).count(),
            'pending_assignments': ControlAssignment.objects.filter(
                control__framework=framework, status__in=['NOT_STARTED', 'IN_PROGRESS']
            ).count(),
        }
        return Response(stats)


class CompanyControlViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Company Controls
    """
    queryset = CompanyControl.objects.filter(is_active=True)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['framework', 'control_type', 'frequency', 'risk_level', 'is_customized']
    search_fields = ['control_code', 'title', 'description', 'objective']
    ordering_fields = ['control_code', 'title', 'sort_order']
    ordering = ['framework', 'sort_order']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CompanyControlBasicSerializer
        return CompanyControlDetailSerializer
    
    @action(detail=True, methods=['get'])
    def assignments(self, request, pk=None):
        """Get all assignments for this control"""
        control = self.get_object()
        assignments = control.assignments.all().order_by('-assignment_date')
        serializer = ControlAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign this control to an employee"""
        control = self.get_object()
        data = request.data.copy()
        data['control'] = control.id
        
        serializer = ControlAssignmentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ControlAssignmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Control Assignments
    """
    queryset = ControlAssignment.objects.all()
    serializer_class = ControlAssignmentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['control', 'assigned_to_employee_id', 'status', 'priority']
    search_fields = ['control__control_code', 'control__title', 'notes']
    ordering_fields = ['assignment_date', 'due_date', 'status']
    ordering = ['-assignment_date']
    
    @action(detail=False, methods=['get'])
    def my_assignments(self, request):
        """Get assignments for specific employee"""
        employee_id = request.GET.get('employee_id')
        if not employee_id:
            return Response({'error': 'employee_id parameter required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        assignments = self.get_queryset().filter(assigned_to_employee_id=employee_id)
        serializer = self.get_serializer(assignments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update assignment status"""
        assignment = self.get_object()
        new_status = request.data.get('status')
        notes = request.data.get('notes', '')
        
        if new_status not in ['NOT_STARTED', 'IN_PROGRESS', 'PENDING_REVIEW', 
                             'COMPLETED', 'NEEDS_REMEDIATION', 'OVERDUE']:
            return Response({'error': 'Invalid status'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        assignment.status = new_status
        if notes:
            assignment.notes = notes
        assignment.save()
        
        serializer = self.get_serializer(assignment)
        return Response(serializer.data)


class AssessmentCampaignViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Assessment Campaigns
    """
    queryset = AssessmentCampaign.objects.all()
    serializer_class = AssessmentCampaignSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['framework', 'status', 'created_by_employee_id']
    search_fields = ['campaign_name', 'description']
    ordering_fields = ['start_date', 'end_date', 'created_date']
    ordering = ['-created_date']
    
    @action(detail=True, methods=['get'])
    def responses(self, request, pk=None):
        """Get all responses for this campaign"""
        campaign = self.get_object()
        responses = AssessmentResponse.objects.filter(campaign=campaign)
        serializer = AssessmentResponseSerializer(responses, many=True)
        return Response(serializer.data)


class AssessmentResponseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Assessment Responses
    """
    queryset = AssessmentResponse.objects.all()
    serializer_class = AssessmentResponseSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['assignment', 'campaign', 'answered_by_employee_id', 'confidence_level']
    search_fields = ['question_text', 'answer', 'comments']
    ordering_fields = ['answered_date', 'question_id']
    ordering = ['assignment', 'question_id']


class EvidenceDocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Evidence Documents
    """
    queryset = EvidenceDocument.objects.all()
    serializer_class = EvidenceDocumentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['assignment', 'status', 'file_type', 'uploaded_by_employee_id']
    search_fields = ['document_name', 'original_filename']
    ordering_fields = ['upload_date', 'file_size_mb']
    ordering = ['-upload_date']
    
    @action(detail=True, methods=['patch'])
    def review(self, request, pk=None):
        """Review evidence document"""
        document = self.get_object()
        new_status = request.data.get('status')
        comments = request.data.get('review_comments', '')
        reviewer_id = request.data.get('reviewed_by_employee_id')
        
        if new_status not in ['APPROVED', 'REJECTED', 'NEEDS_UPDATE']:
            return Response({'error': 'Invalid status'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        document.status = new_status
        document.review_comments = comments
        document.reviewed_by_employee_id = reviewer_id
        from django.utils import timezone
        document.review_date = timezone.now()
        document.save()
        
        serializer = self.get_serializer(document)
        return Response(serializer.data)


class RemediationPlanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Remediation Plans
    """
    queryset = RemediationPlan.objects.all()
    serializer_class = RemediationPlanSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['assignment', 'status', 'priority', 'assigned_to_employee_id']
    search_fields = ['gap_description', 'remediation_steps']
    ordering_fields = ['created_date', 'target_completion_date']
    ordering = ['-created_date']


class ComplianceReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Compliance Reports
    """
    queryset = ComplianceReport.objects.all()
    serializer_class = ComplianceReportSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['framework', 'campaign', 'report_type', 'generated_by_employee_id']
    search_fields = ['report_name']
    ordering_fields = ['generated_date', 'overall_compliance_rate']
    ordering = ['-generated_date']