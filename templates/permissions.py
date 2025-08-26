"""
Custom permissions for Template Service
"""

from rest_framework.permissions import BasePermission


class IsSuperAdminUser(BasePermission):
    """
    Permission for Super Admin users who can manage compliance frameworks.
    Super admins can create, edit, and delete framework templates.
    """
    
    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user is superuser
        return request.user.is_superuser
    
    def has_object_permission(self, request, view, obj):
        # Object-level permission check
        return self.has_permission(request, view)


class IsAdminOrReadOnly(BasePermission):
    """
    Permission that allows admins full access and read-only for others.
    Useful for some template endpoints that employees might need to view.
    """
    
    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Allow read permissions for any authenticated user
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # Write permissions only for admins
        return request.user.is_staff or request.user.is_superuser


class IsTenantMember(BasePermission):
    """
    Permission for tenant-specific operations.
    Users can only access data for their own tenant.
    """
    
    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # For now, allow all authenticated users
        # TODO: Add tenant membership validation
        return True
    
    def has_object_permission(self, request, view, obj):
        # TODO: Implement tenant-specific object access
        return self.has_permission(request, view)