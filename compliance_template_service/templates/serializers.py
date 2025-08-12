"""
Serializers for Template Service API
"""

from rest_framework import serializers
from .models import (
    Framework, Domain, Category, Subcategory, 
    Control, AssessmentQuestion, EvidenceRequirement
)


class EvidenceRequirementSerializer(serializers.ModelSerializer):
    """Serializer for Evidence Requirements"""
    
    class Meta:
        model = EvidenceRequirement
        fields = [
            'id', 'title', 'description', 'evidence_type', 
            'is_mandatory', 'file_format', 'sort_order',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AssessmentQuestionSerializer(serializers.ModelSerializer):
    """Serializer for Assessment Questions"""
    
    class Meta:
        model = AssessmentQuestion
        fields = [
            'id', 'question', 'question_type', 'options', 
            'is_mandatory', 'sort_order',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ControlDetailSerializer(serializers.ModelSerializer):
    """Detailed Control serializer with questions and evidence"""
    
    assessment_questions = AssessmentQuestionSerializer(many=True, read_only=True)
    evidence_requirements = EvidenceRequirementSerializer(many=True, read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True)
    category_name = serializers.CharField(source='subcategory.category.name', read_only=True)
    domain_name = serializers.CharField(source='subcategory.category.domain.name', read_only=True)
    framework_name = serializers.CharField(source='subcategory.category.domain.framework.name', read_only=True)
    
    class Meta:
        model = Control
        fields = [
            'id', 'control_code', 'title', 'description', 'objective',
            'control_type', 'frequency', 'risk_level', 'sort_order',
            'framework_name', 'domain_name', 'category_name', 'subcategory_name',
            'assessment_questions', 'evidence_requirements',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ControlBasicSerializer(serializers.ModelSerializer):
    """Basic Control serializer for lists"""
    
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True)
    
    class Meta:
        model = Control
        fields = [
            'id', 'control_code', 'title', 'control_type', 
            'frequency', 'risk_level', 'subcategory_name',
            'is_active'
        ]
        read_only_fields = ['id']


class SubcategoryDetailSerializer(serializers.ModelSerializer):
    """Detailed Subcategory serializer with controls"""
    
    controls = ControlBasicSerializer(many=True, read_only=True)
    control_count = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    def get_control_count(self, obj):
        return obj.controls.filter(is_active=True).count()
    
    class Meta:
        model = Subcategory
        fields = [
            'id', 'name', 'code', 'description', 'sort_order',
            'category_name', 'control_count', 'controls',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SubcategoryBasicSerializer(serializers.ModelSerializer):
    """Basic Subcategory serializer for lists"""
    
    control_count = serializers.SerializerMethodField()
    
    def get_control_count(self, obj):
        return obj.controls.filter(is_active=True).count()
    
    class Meta:
        model = Subcategory
        fields = [
            'id', 'name', 'code', 'description', 'sort_order',
            'control_count', 'is_active'
        ]
        read_only_fields = ['id']


class CategoryDetailSerializer(serializers.ModelSerializer):
    """Detailed Category serializer with subcategories"""
    
    subcategories = SubcategoryBasicSerializer(many=True, read_only=True)
    subcategory_count = serializers.SerializerMethodField()
    total_controls = serializers.SerializerMethodField()
    domain_name = serializers.CharField(source='domain.name', read_only=True)
    
    def get_subcategory_count(self, obj):
        return obj.subcategories.filter(is_active=True).count()
    
    def get_total_controls(self, obj):
        return sum(
            subcategory.controls.filter(is_active=True).count() 
            for subcategory in obj.subcategories.filter(is_active=True)
        )
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'code', 'description', 'sort_order',
            'domain_name', 'subcategory_count', 'total_controls',
            'subcategories', 'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CategoryBasicSerializer(serializers.ModelSerializer):
    """Basic Category serializer for lists"""
    
    subcategory_count = serializers.SerializerMethodField()
    total_controls = serializers.SerializerMethodField()
    
    def get_subcategory_count(self, obj):
        return obj.subcategories.filter(is_active=True).count()
    
    def get_total_controls(self, obj):
        return sum(
            subcategory.controls.filter(is_active=True).count() 
            for subcategory in obj.subcategories.filter(is_active=True)
        )
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'code', 'description', 'sort_order',
            'subcategory_count', 'total_controls', 'is_active'
        ]
        read_only_fields = ['id']

class DomainCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating domains"""
    def validate(self, attrs):
        """Custom validation for domain uniqueness"""
        framework = attrs.get('framework')
        name = attrs.get('name')
        code = attrs.get('code')
        
        # Check if domain with same name exists in same framework
        if Domain.objects.filter(framework=framework, name=name, is_active=True).exists():
            raise serializers.ValidationError({
                'name': f'Domain with name "{name}" already exists in framework "{framework.name}"'
            })
        
        # Check if domain with same code exists in same framework  
        if Domain.objects.filter(framework=framework, code=code, is_active=True).exists():
            raise serializers.ValidationError({
                'code': f'Domain with code "{code}" already exists in framework "{framework.name}"'
            })
            
        return attrs
    

    class Meta:
        model = Domain
        fields = [
            'id', 'framework', 'name', 'code', 'description', 'sort_order',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CategoryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating categories with validation"""
    
    def validate(self, attrs):
        """Custom validation for category uniqueness"""
        domain = attrs.get('domain')
        name = attrs.get('name')
        code = attrs.get('code')
        
        # Check if category with same name exists in same domain
        if Category.objects.filter(domain=domain, name=name, is_active=True).exists():
            raise serializers.ValidationError({
                'name': f'Category with name "{name}" already exists in domain "{domain.name}"'
            })
        
        # Check if category with same code exists in same domain
        if Category.objects.filter(domain=domain, code=code, is_active=True).exists():
            raise serializers.ValidationError({
                'code': f'Category with code "{code}" already exists in domain "{domain.name}"'
            })
            
        return attrs
    
    class Meta:
        model = Category
        fields = [
            'id', 'domain', 'name', 'code', 'description', 'sort_order',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# Update the existing DomainDetailSerializer to handle both create and detail
class DomainDetailSerializer(serializers.ModelSerializer):
    """Detailed Domain serializer with categories"""
    
    categories = CategoryBasicSerializer(many=True, read_only=True)
    category_count = serializers.SerializerMethodField()
    total_controls = serializers.SerializerMethodField()
    framework_name = serializers.CharField(source='framework.name', read_only=True)
    
    def get_category_count(self, obj):
        return obj.categories.filter(is_active=True).count()
    
    def get_total_controls(self, obj):
        return sum(
            sum(
                subcategory.controls.filter(is_active=True).count() 
                for subcategory in category.subcategories.filter(is_active=True)
            )
            for category in obj.categories.filter(is_active=True)
        )
    
    class Meta:
        model = Domain
        fields = [
            'id', 'framework', 'name', 'code', 'description', 'sort_order',
            'framework_name', 'category_count', 'total_controls',
            'categories', 'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']



class DomainBasicSerializer(serializers.ModelSerializer):
    """Basic Domain serializer for lists"""
    
    category_count = serializers.SerializerMethodField()
    total_controls = serializers.SerializerMethodField()
    
    def get_category_count(self, obj):
        return obj.categories.filter(is_active=True).count()
    
    def get_total_controls(self, obj):
        return sum(
            sum(
                subcategory.controls.filter(is_active=True).count() 
                for subcategory in category.subcategories.filter(is_active=True)
            )
            for category in obj.categories.filter(is_active=True)
        )
    
    class Meta:
        model = Domain
        fields = [
            'id', 'name', 'code', 'description', 'sort_order',
            'category_count', 'total_controls', 'is_active'
        ]
        read_only_fields = ['id']


class FrameworkDetailSerializer(serializers.ModelSerializer):
    """Detailed Framework serializer with domains"""
    
    domains = DomainBasicSerializer(many=True, read_only=True)
    stats = serializers.SerializerMethodField()
    
    def get_stats(self, obj):
        domains = obj.domains.filter(is_active=True)
        total_categories = sum(
            domain.categories.filter(is_active=True).count() 
            for domain in domains
        )
        total_subcategories = sum(
            sum(
                category.subcategories.filter(is_active=True).count() 
                for category in domain.categories.filter(is_active=True)
            )
            for domain in domains
        )
        total_controls = sum(
            sum(
                sum(
                    subcategory.controls.filter(is_active=True).count() 
                    for subcategory in category.subcategories.filter(is_active=True)
                )
                for category in domain.categories.filter(is_active=True)
            )
            for domain in domains
        )
        
        return {
            'domain_count': domains.count(),
            'category_count': total_categories,
            'subcategory_count': total_subcategories,
            'control_count': total_controls
        }
    
    def to_representation(self, instance):
        """Convert datetime to date for effective_date field"""
        data = super().to_representation(instance)
        
        # Convert datetime to date if needed
        if 'effective_date' in data and data['effective_date']:
            # If it's a datetime string, extract just the date part
            effective_date = data['effective_date']
            if 'T' in str(effective_date):  # datetime format
                data['effective_date'] = str(effective_date).split('T')[0]
        
        return data
    
    class Meta:
        model = Framework
        fields = [
            'id', 'name', 'full_name', 'description', 'version',
            'effective_date', 'status', 'stats', 'domains',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']




class FrameworkBasicSerializer(serializers.ModelSerializer):
    """Basic Framework serializer for lists"""
    
    domain_count = serializers.SerializerMethodField()
    total_controls = serializers.SerializerMethodField()
    
    def get_domain_count(self, obj):
        return obj.domains.filter(is_active=True).count()
    
    def get_total_controls(self, obj):
        return sum(
            sum(
                sum(
                    subcategory.controls.filter(is_active=True).count() 
                    for subcategory in category.subcategories.filter(is_active=True)
                )
                for category in domain.categories.filter(is_active=True)
            )
            for domain in obj.domains.filter(is_active=True)
        )
    
    class Meta:
        model = Framework
        fields = [
            'id', 'name', 'full_name', 'version', 'status',
            'effective_date', 'domain_count', 'total_controls', 'is_active'
        ]
        read_only_fields = ['id']