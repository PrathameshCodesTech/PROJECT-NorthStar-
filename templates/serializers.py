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
    subcategory_id = serializers.SerializerMethodField()
    subcategory_name = serializers.SerializerMethodField()
    category_id = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    domain_id = serializers.SerializerMethodField()
    domain_name = serializers.SerializerMethodField()
    framework_id = serializers.SerializerMethodField()
    framework_name = serializers.SerializerMethodField()


    def _cat(self, obj):
        return getattr(obj.subcategory, 'category', None)

    def _dom(self, obj):
        cat = self._cat(obj)
        return getattr(cat, 'domain', None)

    def _fw(self, obj):
        dom = self._dom(obj)
        return getattr(dom, 'framework', None)
    
    def get_subcategory_id(self, obj):
        sub = getattr(obj, 'subcategory', None)
        return getattr(sub, 'id', None)

    def get_subcategory_name(self, obj):
        sub = getattr(obj, 'subcategory', None)
        return getattr(sub, 'name', None)

    def get_category_id(self, obj):
        cat = self._cat(obj)
        return getattr(cat, 'id', None)

    def get_category_name(self, obj):
        cat = self._cat(obj)
        return getattr(cat, 'name', None)

    def get_domain_id(self, obj):
        dom = self._dom(obj)
        return getattr(dom, 'id', None)

    def get_domain_name(self, obj):
        dom = self._dom(obj)
        return getattr(dom, 'name', None)

    def get_framework_id(self, obj):
        fw = self._fw(obj)
        return getattr(fw, 'id', None)

    def get_framework_name(self, obj):
        fw = self._fw(obj)
        return getattr(fw, 'name', None)


    
    class Meta:
        model = Control
        fields = [
            'id', 'control_code', 'title', 'description', 'objective',
            'control_type', 'frequency', 'risk_level', 'sort_order',
            # NEW fields you asked for:
            'framework_id', 'framework_name',
            'domain_id', 'domain_name',
            'category_id', 'category_name',
            'subcategory_id', 'subcategory_name',
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



    # ✅ category info
    category_id = serializers.UUIDField(read_only=True)                         # model column `category_id`
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)

    # ✅ domain info (via category → domain)
    domain_id = serializers.SerializerMethodField()
    domain_name = serializers.SerializerMethodField()

    # ✅ framework info (via category → domain → framework)
    framework_id = serializers.SerializerMethodField()
    framework_name = serializers.SerializerMethodField()
    def get_category_name(self, obj):
        return getattr(obj.category, 'name', None)

    
    def get_control_count(self, obj):
        return obj.controls.filter(is_active=True).count()
    
    class Meta:
        model = Subcategory
        fields = [
            'id', 'name', 'code', 'description', 'sort_order',
             # category linkage
            'category_id', 'category_name',
            # domain linkage
            'domain_id', 'domain_name',
            # framework linkage
            'framework_id', 'framework_name',
            'control_count', 'controls',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_domain_id(self, obj):
        # category can be None; domain can be None
        return getattr(obj.category, 'domain_id', None) if obj.category else None

    def get_domain_name(self, obj):
        if not obj.category or not obj.category.domain:
            return None
        return obj.category.domain.name

    def get_framework_id(self, obj):
        if not obj.category or not obj.category.domain:
            return None
        return getattr(obj.category.domain, 'framework_id', None)

    def get_framework_name(self, obj):
        if not obj.category or not obj.category.domain or not obj.category.domain.framework:
            return None
        return obj.category.domain.framework.name

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
    domain_id = serializers.UUIDField(read_only=True)
    framework_id = serializers.SerializerMethodField()
    framework_name = serializers.SerializerMethodField()
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
            'id', 'name', 'code', 'description', 'sort_order','framework_id', 'framework_name', 'domain_id',
            'domain_name', 'subcategory_count', 'total_controls',
            'subcategories', 'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_framework_id(self, obj):
        # obj.domain may be None
        return getattr(obj.domain, 'framework_id', None) if obj.domain else None

    def get_framework_name(self, obj):
        if not obj.domain or not obj.domain.framework:
            return None
        return obj.domain.framework.name


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


# serializers.py (templates app)

class AssessmentQuestionMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentQuestion
        fields = ['id', 'question', 'question_type', 'is_mandatory', 'sort_order']

class EvidenceRequirementMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvidenceRequirement
        fields = ['id', 'title', 'evidence_type', 'is_mandatory', 'file_format']

class ControlNestedSerializer(serializers.ModelSerializer):
    assessment_questions = AssessmentQuestionMiniSerializer(many=True, read_only=True)
    evidence_requirements = EvidenceRequirementMiniSerializer(many=True, read_only=True)

    # chain context (safe if something is null)
    subcategory_id   = serializers.SerializerMethodField()
    subcategory_name = serializers.SerializerMethodField()
    category_id      = serializers.SerializerMethodField()
    category_name    = serializers.SerializerMethodField()
    domain_id        = serializers.SerializerMethodField()
    domain_name      = serializers.SerializerMethodField()
    framework_id     = serializers.SerializerMethodField()
    framework_name   = serializers.SerializerMethodField()

    class Meta:
        model = Control
        fields = [
            'id','control_code','title','description','objective',
            'control_type','frequency','risk_level','sort_order',
            'subcategory_id','subcategory_name',
            'category_id','category_name',
            'domain_id','domain_name',
            'framework_id','framework_name',
            'assessment_questions','evidence_requirements',
            'created_at','updated_at','is_active'
        ]

    def _cat(self, obj): return getattr(obj.subcategory, 'category', None)
    def _dom(self, obj): 
        cat = self._cat(obj); return getattr(cat, 'domain', None) if cat else None
    def _fw(self, obj):
        dom = self._dom(obj); return getattr(dom, 'framework', None) if dom else None

    def get_subcategory_id(self, obj):   return getattr(obj.subcategory, 'id', None)
    def get_subcategory_name(self, obj): return getattr(obj.subcategory, 'name', None)
    def get_category_id(self, obj):      return getattr(self._cat(obj), 'id', None)
    def get_category_name(self, obj):    return getattr(self._cat(obj), 'name', None)
    def get_domain_id(self, obj):        return getattr(self._dom(obj), 'id', None)
    def get_domain_name(self, obj):      return getattr(self._dom(obj), 'name', None)
    def get_framework_id(self, obj):     return getattr(self._fw(obj), 'id', None)
    def get_framework_name(self, obj):   return getattr(self._fw(obj), 'name', None)

class SubcategoryNestedSerializer(serializers.ModelSerializer):
    # assumes Control has related_name='controls'
    controls = ControlNestedSerializer(many=True, read_only=True)
    class Meta:
        model = Subcategory
        fields = ['id','name','code','description','sort_order','controls','created_at','updated_at','is_active']

class CategoryNestedSerializer(serializers.ModelSerializer):
    # assumes Subcategory has related_name='subcategories'
    subcategories = SubcategoryNestedSerializer(many=True, read_only=True)
    domain_id      = serializers.UUIDField(read_only=True)
    domain_name    = serializers.CharField(source='domain.name', read_only=True)
    framework_id   = serializers.SerializerMethodField()
    framework_name = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id','name','code','description','sort_order',
            'domain_id','domain_name','framework_id','framework_name',
            'subcategories','created_at','updated_at','is_active'
        ]

    def get_framework_id(self, obj):
        dom = getattr(obj, 'domain', None)
        fw = getattr(dom, 'framework', None) if dom else None
        return getattr(fw, 'id', None)

    def get_framework_name(self, obj):
        dom = getattr(obj, 'domain', None)
        fw = getattr(dom, 'framework', None) if dom else None
        return getattr(fw, 'name', None)

class DomainNestedSerializer(serializers.ModelSerializer):
    # assumes Category has related_name='categories'
    categories = CategoryNestedSerializer(many=True, read_only=True)
    category_count = serializers.SerializerMethodField()   # ← add
    total_controls = serializers.SerializerMethodField()   # ← add

    class Meta:
        model = Domain
        fields = ['id','name','code','description','sort_order','category_count','total_controls','categories','is_active']

    def get_category_count(self, obj):
        return obj.categories.filter(is_active=True).count()

    def get_total_controls(self, obj):
        return sum(
            sum(sc.controls.filter(is_active=True).count()
                for sc in c.subcategories.filter(is_active=True))
            for c in obj.categories.filter(is_active=True)
        )



class FrameworkDeepSerializer(serializers.ModelSerializer):
    domains = DomainNestedSerializer(many=True, read_only=True)
    stats = serializers.SerializerMethodField()   # ← add this

    class Meta:
        model = Framework
        fields = [
            'id','name','full_name','description','version','effective_date','status',
            'stats','domains','created_at','updated_at','is_active'
        ]

    def get_stats(self, obj):
        # Uses same logic as your view’s /stats action
        domains = obj.domains.filter(is_active=True)
        return {
            'domain_count': domains.count(),
            'category_count': sum(
                d.categories.filter(is_active=True).count()
                for d in domains
            ),
            'subcategory_count': sum(
                sum(c.subcategories.filter(is_active=True).count()
                    for c in d.categories.filter(is_active=True))
                for d in domains
            ),
            'control_count': sum(
                sum(
                    sum(sc.controls.filter(is_active=True).count()
                        for sc in c.subcategories.filter(is_active=True))
                    for c in d.categories.filter(is_active=True)
                )
                for d in domains
            ),
        }

