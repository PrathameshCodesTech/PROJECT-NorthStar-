"""
Permission classes for Service 1
"""

from rest_framework.permissions import BasePermission


class IsSuperAdminUser(BasePermission):
    """
    Permission class that only allows platform superusers
    """
    
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.is_superuser
        )