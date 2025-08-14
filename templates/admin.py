"""
Admin interface for Template Service
"""

from django.contrib import admin
from .models import (
    Framework, Domain, Category, Subcategory, 
    Control, AssessmentQuestion, EvidenceRequirement
)


@admin.register(Framework)
class FrameworkAdmin(admin.ModelAdmin):
    list_display = ['name', 'full_name', 'version', 'status', 'effective_date', 'is_active']
    list_filter = ['status', 'is_active', 'created_at']
    search_fields = ['name', 'full_name', 'description']
    ordering = ['name', 'version']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'framework', 'sort_order', 'is_active']
    list_filter = ['framework', 'is_active', 'created_at']
    search_fields = ['name', 'code', 'description']
    ordering = ['framework', 'sort_order']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'domain', 'sort_order', 'is_active']
    list_filter = ['domain__framework', 'is_active', 'created_at']
    search_fields = ['name', 'code', 'description']
    ordering = ['domain', 'sort_order']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'category', 'sort_order', 'is_active']
    list_filter = ['category__domain__framework', 'is_active', 'created_at']
    search_fields = ['name', 'code', 'description']
    ordering = ['category', 'sort_order']
    readonly_fields = ['id', 'created_at', 'updated_at']


class AssessmentQuestionInline(admin.TabularInline):
    model = AssessmentQuestion
    extra = 1
    fields = ['question', 'question_type', 'is_mandatory', 'sort_order']


class EvidenceRequirementInline(admin.TabularInline):
    model = EvidenceRequirement
    extra = 1
    fields = ['title', 'evidence_type', 'is_mandatory', 'sort_order']


@admin.register(Control)
class ControlAdmin(admin.ModelAdmin):
    list_display = ['control_code', 'title', 'subcategory', 'control_type', 'risk_level', 'is_active']
    list_filter = [
        'subcategory__category__domain__framework', 
        'control_type', 'frequency', 'risk_level', 'is_active', 'created_at'
    ]
    search_fields = ['control_code', 'title', 'description', 'objective']
    ordering = ['subcategory', 'sort_order']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [AssessmentQuestionInline, EvidenceRequirementInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('subcategory', 'control_code', 'title', 'sort_order')
        }),
        ('Details', {
            'fields': ('description', 'objective')
        }),
        ('Control Properties', {
            'fields': ('control_type', 'frequency', 'risk_level')
        }),
        ('System Fields', {
            'fields': ('id', 'is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(AssessmentQuestion)
class AssessmentQuestionAdmin(admin.ModelAdmin):
    list_display = ['control', 'question_type', 'is_mandatory', 'sort_order', 'is_active']
    list_filter = ['question_type', 'is_mandatory', 'is_active', 'created_at']
    search_fields = ['question', 'control__control_code']
    ordering = ['control', 'sort_order']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(EvidenceRequirement)
class EvidenceRequirementAdmin(admin.ModelAdmin):
    list_display = ['title', 'control', 'evidence_type', 'is_mandatory', 'sort_order', 'is_active']
    list_filter = ['evidence_type', 'is_mandatory', 'is_active', 'created_at']
    search_fields = ['title', 'description', 'control__control_code']
    ordering = ['control', 'sort_order']
    readonly_fields = ['id', 'created_at', 'updated_at']