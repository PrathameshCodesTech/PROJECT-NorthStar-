"""
API Views for Template Service
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .models import (
    Framework, Domain, Category, Subcategory, 
    Control, AssessmentQuestion, EvidenceRequirement
)
from .serializers import (
    FrameworkDetailSerializer, FrameworkBasicSerializer,
    DomainDetailSerializer, DomainBasicSerializer,
    CategoryDetailSerializer, CategoryBasicSerializer,
    SubcategoryDetailSerializer, SubcategoryBasicSerializer,
    ControlDetailSerializer, ControlBasicSerializer, CategoryCreateSerializer,
    AssessmentQuestionSerializer, EvidenceRequirementSerializer,DomainCreateSerializer,SubcategoryCreateSerializer,ControlCreateSerializer
)


class FrameworkViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Compliance Frameworks
    
    Provides CRUD operations for frameworks like SOX, ISO 27001, etc.
    """
    queryset = Framework.objects.filter(is_active=True)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'name']
    search_fields = ['name', 'full_name', 'description']
    ordering_fields = ['name', 'version', 'created_at']
    ordering = ['name', 'version']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return FrameworkBasicSerializer
        return FrameworkDetailSerializer
    
    @action(detail=True, methods=['get'])
    def domains(self, request, pk=None):
        """Get all domains for a specific framework"""
        framework = self.get_object()
        domains = framework.domains.filter(is_active=True).order_by('sort_order')
        serializer = DomainBasicSerializer(domains, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get framework statistics"""
        framework = self.get_object()
        domains = framework.domains.filter(is_active=True)
        
        stats = {
            'framework_id': framework.id,
            'framework_name': framework.name,
            'version': framework.version,
            'domain_count': domains.count(),
            'category_count': sum(
                domain.categories.filter(is_active=True).count() 
                for domain in domains
            ),
            'subcategory_count': sum(
                sum(
                    category.subcategories.filter(is_active=True).count() 
                    for category in domain.categories.filter(is_active=True)
                )
                for domain in domains
            ),
            'control_count': sum(
                sum(
                    sum(
                        subcategory.controls.filter(is_active=True).count() 
                        for subcategory in category.subcategories.filter(is_active=True)
                    )
                    for category in domain.categories.filter(is_active=True)
                )
                for domain in domains
            )
        }
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def clone(self, request, pk=None):
        """Clone a framework with new version"""
        framework = self.get_object()
        new_version = request.data.get('version')
        new_name = request.data.get('name', f"{framework.name}_COPY")
        
        if not new_version:
            return Response(
                {'error': 'Version is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create new framework
        new_framework = Framework.objects.create(
            name=new_name,
            full_name=f"{framework.full_name} (Copy)",
            description=framework.description,
            version=new_version,
            status='DRAFT'
        )
        
        serializer = FrameworkDetailSerializer(new_framework)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DomainViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Framework Domains
    """
    queryset = Domain.objects.filter(is_active=True)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['framework', 'code']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'sort_order', 'created_at']
    ordering = ['framework', 'sort_order']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DomainCreateSerializer  # Use create serializer for POST
        elif self.action == 'list':
            return DomainBasicSerializer
        return DomainDetailSerializer
    
    @action(detail=True, methods=['get'])
    def categories(self, request, pk=None):
        """Get all categories for a specific domain"""
        domain = self.get_object()
        categories = domain.categories.filter(is_active=True).order_by('sort_order')
        serializer = CategoryBasicSerializer(categories, many=True)
        return Response(serializer.data)

    

class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Categories
    """
    queryset = Category.objects.filter(is_active=True)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['domain', 'code']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'sort_order', 'created_at']
    ordering = ['domain', 'sort_order']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CategoryCreateSerializer
        elif self.action == 'list':
            return CategoryBasicSerializer
        return CategoryDetailSerializer
    
    @action(detail=True, methods=['get'])
    def subcategories(self, request, pk=None):
        """Get all subcategories for a specific category"""
        category = self.get_object()
        subcategories = category.subcategories.filter(is_active=True).order_by('sort_order')
        serializer = SubcategoryBasicSerializer(subcategories, many=True)
        return Response(serializer.data)


class SubcategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Subcategories
    """
    queryset = Subcategory.objects.filter(is_active=True)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'code']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'sort_order', 'created_at']
    ordering = ['category', 'sort_order']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SubcategoryCreateSerializer
        elif self.action == 'list':
            return SubcategoryBasicSerializer
        return SubcategoryDetailSerializer
    
    @action(detail=True, methods=['get'])
    def controls(self, request, pk=None):
        """Get all controls for a specific subcategory"""
        subcategory = self.get_object()
        controls = subcategory.controls.filter(is_active=True).order_by('sort_order')
        serializer = ControlBasicSerializer(controls, many=True)
        return Response(serializer.data)


class ControlViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Controls
    """
    queryset = Control.objects.filter(is_active=True)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['subcategory', 'control_type', 'frequency', 'risk_level']
    search_fields = ['control_code', 'title', 'description', 'objective']
    ordering_fields = ['control_code', 'title', 'sort_order', 'created_at']
    ordering = ['subcategory', 'sort_order']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ControlCreateSerializer
        elif self.action == 'list':
            return ControlBasicSerializer
        return ControlDetailSerializer
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced search across all controls"""
        query = request.GET.get('q', '')
        framework = request.GET.get('framework', '')
        control_type = request.GET.get('control_type', '')
        risk_level = request.GET.get('risk_level', '')
        
        queryset = self.get_queryset()
        
        if query:
            queryset = queryset.filter(
                Q(control_code__icontains=query) |
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(objective__icontains=query)
            )
        
        if framework:
            queryset = queryset.filter(
                subcategory__category__domain__framework__name__iexact=framework
            )
        
        if control_type:
            queryset = queryset.filter(control_type=control_type)
        
        if risk_level:
            queryset = queryset.filter(risk_level=risk_level)
        
        serializer = ControlBasicSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def questions(self, request, pk=None):
        """Get assessment questions for a control"""
        control = self.get_object()
        questions = control.assessment_questions.filter(is_active=True).order_by('sort_order')
        serializer = AssessmentQuestionSerializer(questions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def evidence(self, request, pk=None):
        """Get evidence requirements for a control"""
        control = self.get_object()
        evidence = control.evidence_requirements.filter(is_active=True).order_by('sort_order')
        serializer = EvidenceRequirementSerializer(evidence, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_question(self, request, pk=None):
        """Add assessment question to a control"""
        control = self.get_object()
        data = request.data.copy()
        data['control'] = control.id
        
        serializer = AssessmentQuestionSerializer(data=data)
        if serializer.is_valid():
            serializer.save(control=control)  # Pass control explicitly
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def add_evidence(self, request, pk=None):
        """Add evidence requirement to a control"""
        control = self.get_object()
        data = request.data.copy()
        data['control'] = control.id
        
        serializer = EvidenceRequirementSerializer(data=data)
        if serializer.is_valid():
            serializer.save(control=control)  # Pass control explicitly
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AssessmentQuestionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Assessment Questions
    """
    queryset = AssessmentQuestion.objects.filter(is_active=True)
    serializer_class = AssessmentQuestionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['control', 'question_type', 'is_mandatory']
    search_fields = ['question']
    ordering_fields = ['sort_order', 'created_at']
    ordering = ['control', 'sort_order']


class EvidenceRequirementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Evidence Requirements
    """
    queryset = EvidenceRequirement.objects.filter(is_active=True)
    serializer_class = EvidenceRequirementSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['control', 'evidence_type', 'is_mandatory']
    search_fields = ['title', 'description']
    ordering_fields = ['sort_order', 'created_at']
    ordering = ['control', 'sort_order']