"""
URL Configuration for Templates App
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and register viewsets
router = DefaultRouter()
router.register(r'frameworks', views.FrameworkViewSet)
router.register(r'domains', views.DomainViewSet)
router.register(r'categories', views.CategoryViewSet)
router.register(r'subcategories', views.SubcategoryViewSet)
router.register(r'controls', views.ControlViewSet)
router.register(r'questions', views.AssessmentQuestionViewSet)
router.register(r'evidence', views.EvidenceRequirementViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]