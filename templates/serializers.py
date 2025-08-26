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
    subcategory_name = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    domain_name = serializers.SerializerMethodField()
    framework_name = serializers.SerializerMethodField()

    def get_subcategory_name(self, obj):
        return getattr(obj.subcategory, 'name', None)

    def get_category_name(self, obj):
        return getattr(getattr(obj.subcategory, 'category', None), 'name', None)

    def get_domain_name(self, obj):
        cat = getattr(obj.subcategory, 'category', None)
        dom = getattr(cat, 'domain', None)
        return getattr(dom, 'name', None)

    def get_framework_name(self, obj):
        cat = getattr(obj.subcategory, 'category', None)
        dom = getattr(cat, 'domain', None)
        fw = getattr(dom, 'framework', None)
        return getattr(fw, 'name', None)

    
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
    
    subcategory_name = serializers.SerializerMethodField()
    def get_subcategory_name(self, obj):
        return getattr(obj.subcategory, 'name', None)

    
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
    category_name = serializers.SerializerMethodField()
    def get_category_name(self, obj):
        return getattr(obj.category, 'name', None)

    
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
    domain_name = serializers.SerializerMethodField()
    def get_domain_name(self, obj):
        return getattr(obj.domain, 'name', None)

    
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
    """Serializer for creating domains (framework is optional)"""

    framework = serializers.PrimaryKeyRelatedField(
        queryset=Framework.objects.all(),
        required=False,
        allow_null=True,
    )

    def validate(self, attrs):
        framework = attrs.get('framework', None)
        name = attrs.get('name')
        code = attrs.get('code')

        # Only enforce uniqueness when attached to a framework
        if framework:
            if Domain.objects.filter(framework=framework, name=name, is_active=True).exists():
                raise serializers.ValidationError({
                    'name': f'Domain with name "{name}" already exists in framework "{framework.name}"'
                })
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
    # make domain optional
    domain = serializers.PrimaryKeyRelatedField(
        queryset=Domain.objects.all(),
        required=False,
        allow_null=True,
    )

    def validate(self, attrs):
        domain = attrs.get('domain', None)
        name = attrs.get('name')
        code = attrs.get('code')

        # Uniqueness is scoped to the domain when provided
        if domain:
            if Category.objects.filter(domain=domain, name=name, is_active=True).exists():
                raise serializers.ValidationError({
                    'name': f'Category with name "{name}" already exists in domain "{domain.name}"'
                })
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
    framework_name = serializers.SerializerMethodField()

    def get_framework_name(self, obj):
        return getattr(obj.framework, 'name', None)

    
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


class SubcategoryCreateSerializer(serializers.ModelSerializer):
    # make category optional
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        required=False,
        allow_null=True,
    )

    def validate(self, attrs):
        category = attrs.get('category', None)
        name = attrs.get('name')
        code = attrs.get('code')

        if category:
            if Subcategory.objects.filter(category=category, name=name, is_active=True).exists():
                raise serializers.ValidationError({
                    'name': f'Subcategory with name "{name}" already exists in category "{category.name}"'
                })
            if Subcategory.objects.filter(category=category, code=code, is_active=True).exists():
                raise serializers.ValidationError({
                    'code': f'Subcategory with code "{code}" already exists in category "{category.name}"'
                })
        return attrs

    class Meta:
        model = Subcategory
        fields = [
            'id', 'category', 'name', 'code', 'description', 'sort_order',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ControlCreateSerializer(serializers.ModelSerializer):
    # make subcategory optional
    subcategory = serializers.PrimaryKeyRelatedField(
        queryset=Subcategory.objects.all(),
        required=False,
        allow_null=True,
    )

    def validate(self, attrs):
        subcategory = attrs.get('subcategory', None)
        control_code = attrs.get('control_code')

        # If attached, enforce uniqueness within that subcategory
        if subcategory and Control.objects.filter(
            subcategory=subcategory, control_code=control_code, is_active=True
        ).exists():
            raise serializers.ValidationError({
                'control_code': f'Control "{control_code}" already exists in this subcategory'
            })
        # If unattached (subcategory is None): allow duplicates (standalone pool)
        return attrs

    class Meta:
        model = Control
        fields = [
            'id', 'subcategory', 'control_code', 'title', 'description',
            'objective', 'control_type', 'frequency', 'risk_level', 'sort_order',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
