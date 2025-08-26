"""
API Views for Company Compliance Service
"""
from rest_framework import viewsets, status, filters
from rest_framework.permissions import IsAuthenticated
from .permissions import IsTenantMember, IsTenantAdmin, CanAssignControls, IsOwnerOrTenantAdmin
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
import requests
from django.conf import settings

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
from .permissions import CanCreateUsers, IsTenantMember
from template_service.database_router import get_current_tenant
from .permissions import validate_role_creation

class CompanyFrameworkViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Company Frameworks
    REQUIRES AUTHENTICATION
    """
    queryset = CompanyFramework.objects.all()
    serializer_class = CompanyFrameworkSerializer
    permission_classes = [IsTenantMember]
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
    permission_classes = [IsTenantMember]
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
    permission_classes = [IsTenantMember, IsOwnerOrTenantAdmin]
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
    permission_classes = [IsTenantAdmin]
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
    permission_classes = [IsTenantMember, IsOwnerOrTenantAdmin]
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
    permission_classes = [IsTenantMember, IsOwnerOrTenantAdmin]
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
    permission_classes = [IsTenantMember]
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
    permission_classes = [IsTenantAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['framework', 'campaign', 'report_type', 'generated_by_employee_id']
    search_fields = ['report_name']
    ordering_fields = ['generated_date', 'overall_compliance_rate']
    ordering = ['-generated_date']


def create_isolated_user(self, data, tenant_slug):
    """Create user in tenant database for isolated mode"""
    try:
        from .models import TenantUser
        from django.contrib.auth.hashers import make_password
        from template_service.database_router import set_current_tenant, clear_current_tenant
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'EMPLOYEE')
        
        if not all([username, email, password]):
            return Response({'error': 'Missing required fields'}, status=400)
        
        # Set tenant context for database routing
        set_current_tenant(tenant_slug)
        
        try:
            # Check if user already exists in tenant database
            if TenantUser.objects.filter(username=username).exists():
                return Response({'error': 'Username already exists'}, status=400)
            
            if TenantUser.objects.filter(email=email).exists():
                return Response({'error': 'Email already exists'}, status=400)
            
            # Create tenant user
            tenant_user = TenantUser.objects.create(
                username=username,
                email=email,
                password_hash=make_password(password),
                role=role,
                is_active=True
            )
            
            return Response({
                'success': True,
                'user': {
                    'id': str(tenant_user.id),
                    'username': tenant_user.username,
                    'email': tenant_user.email,
                    'role': tenant_user.role,
                    'tenant_slug': tenant_slug
                }
            }, status=201)
            
        finally:
            clear_current_tenant()
            
    except Exception as e:
        return Response({'error': str(e)}, status=500)

def get_tenant_info(self, tenant_slug):
    """Get tenant information from Service 2"""
    try:
        response = requests.get(
            f'{settings.SERVICE2_URL}/api/v2/internal/tenants/{tenant_slug}/residency/',
            headers={'X-Internal-Token': settings.SERVICE_TO_SERVICE_TOKEN},
            timeout=5
        )
        
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None

class TenantUserViewSet(viewsets.ViewSet):
    """Handle user creation for ISOLATED mode"""
    permission_classes = [IsTenantMember, CanCreateUsers]
    
    def create(self, request):
        """Create user in isolated tenant database"""
        tenant_slug = get_current_tenant()
        
        # Verify tenant uses isolated mode
        tenant_info = self.get_tenant_info(tenant_slug)
        if tenant_info.get('user_data_residency') != 'ISOLATED':
            return Response({'error': 'This tenant uses centralized user management'}, status=400)
        
        # Validate role assignment
        creator_role = request.tenant_membership.get('role')
        target_role = request.data.get('role', 'EMPLOYEE')
        
        if not validate_role_creation(creator_role, target_role):
            return Response({'error': f'Cannot assign role {target_role}'}, status=403)
        
        return self.create_isolated_user(request.data, tenant_slug)