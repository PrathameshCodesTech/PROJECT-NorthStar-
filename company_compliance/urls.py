"""
URL Configuration for Company Compliance API
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and register viewsets
router = DefaultRouter()
router.register(r'frameworks', views.CompanyFrameworkViewSet, basename='companyframework')
router.register(r'controls', views.CompanyControlViewSet, basename='companycontrol')
router.register(r'assignments', views.ControlAssignmentViewSet, basename='controlassignment')
router.register(r'campaigns', views.AssessmentCampaignViewSet, basename='assessmentcampaign')
router.register(r'responses', views.AssessmentResponseViewSet, basename='assessmentresponse')
router.register(r'evidence', views.EvidenceDocumentViewSet, basename='evidencedocument')
router.register(r'remediation', views.RemediationPlanViewSet, basename='remediationplan')
router.register(r'reports', views.ComplianceReportViewSet, basename='compliancereport')

urlpatterns = [
    path('', include(router.urls)),  
    path('tenant-users/', views.TenantUserViewSet.as_view({'post': 'create'}), name='create-tenant-user'),
    path('tenants/<str:tenant_slug>/users/', views.TenantUserViewSet.as_view({'post': 'create'}), name='create-tenant-user-with-slug'),
    path('tenants/<str:tenant_slug>/invite/', views.TenantUserViewSet.as_view({'post': 'invite_isolated_user'}), name='invite-tenant-user'),
]