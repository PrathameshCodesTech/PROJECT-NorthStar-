"""
Tenant-based permissions for Company Compliance API
Now gets user info from Service 2 via API calls
"""

from rest_framework.permissions import BasePermission
from template_service.database_router import get_current_tenant
import requests
from django.conf import settings


# def get_user_tenant_membership(user, tenant_slug):
#     """
#     Get user's tenant membership from Service 2
#     Returns membership info or None
#     """
#     try:
#         response = requests.get(
#             f'{settings.SERVICE2_URL}/api/v2/users/memberships/',
#             params={'user': user.id, 'tenant_slug': tenant_slug},
#             headers={'Authorization': f'Bearer {get_service2_token()}'},
#             timeout=5
#         )
        
#         if response.status_code == 200:
#             memberships = response.json().get('results', [])
#             for membership in memberships:
#                 if (membership.get('user') == user.id and 
#                     membership.get('tenant_slug') == tenant_slug and
#                     membership.get('status') == 'ACTIVE'):
#                     return membership
#         return None
#     except Exception as e:
#         print(f"Error getting user membership: {e}")
#         return None


def get_user_tenant_membership(user, tenant_slug):
    """
    Get user's tenant membership - handles both centralized and isolated modes
    """
    try:
        # First check tenant's data residency preference
        tenant_response = requests.get(
            f'{settings.SERVICE2_URL}/api/v2/internal/tenants/{tenant_slug}/residency/',
            headers={'X-Internal-Token': settings.SERVICE_TO_SERVICE_TOKEN},
            timeout=5
        )
        
        if tenant_response.status_code == 200:
            residency = tenant_response.json().get('user_data_residency', 'CENTRALIZED')
            
            if residency == 'ISOLATED':
                # Check in tenant database
                return get_isolated_user_membership(user, tenant_slug)
            else:
                # Check in central database via Service 2
                return get_centralized_user_membership(user, tenant_slug)
        
        return None
    except Exception as e:
        print(f"Error getting user membership: {e}")
        return None

# def get_centralized_user_membership(user, tenant_slug):
    """Check membership in central database via Service 2"""
    try:
        response = requests.get(
            f'{settings.SERVICE2_URL}/api/v2/internal/users/{user.id}/tenants/{tenant_slug}/membership/',
            headers={'X-Internal-Token': settings.SERVICE_TO_SERVICE_TOKEN},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('has_membership'):
                return data.get('membership')
        return None
    except Exception as e:
        print(f"Error getting centralized membership: {e}")
        return None
def get_centralized_user_membership(user, tenant_slug):
    """Check membership in central database via Service 2"""
    try:
        response = requests.get(
            f'{settings.SERVICE2_URL}/api/v2/internal/users/{user.id}/tenants/{tenant_slug}/membership/',
            headers={'X-Internal-Token': settings.SERVICE_TO_SERVICE_TOKEN},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('has_membership'):
                # Register tenant database connection
                register_tenant_database_connection(tenant_slug)
                return data.get('membership')
        return None
    except Exception as e:
        print(f"Error getting centralized membership: {e}")
        return None

def register_tenant_database_connection(tenant_slug):
    """Register tenant database connection with Service 1"""
    from django.db import connections
    
    # Check if connection already exists
    connection_name = f"{tenant_slug}_compliance_db"
    if connection_name in connections.databases:
        return connection_name
    
    try:
        # Get database credentials from Service 2
        response = requests.get(
            f'{settings.SERVICE2_URL}/api/v2/internal/tenants/{tenant_slug}/db-info/',
            headers={'X-Internal-Token': settings.SERVICE_TO_SERVICE_TOKEN},
            timeout=5
        )
        
        if response.status_code == 200:
            credentials = response.json()
            
            # Register the database connection
            connections.databases[connection_name] = {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': credentials['database_name'],
                'USER': credentials['database_user'],
                'PASSWORD': credentials['database_password'],
                'HOST': credentials['database_host'],
                'PORT': credentials['database_port'],
                'CONN_MAX_AGE': 60,
                'AUTOCOMMIT': True,
                'ATOMIC_REQUESTS': False,
                'TIME_ZONE': getattr(settings, 'TIME_ZONE', None),  
                'CONN_HEALTH_CHECKS': True,
                'OPTIONS': {'connect_timeout': 5},
            }
            
            print(f"Registered database connection for tenant: {tenant_slug}")
            return connection_name
    except Exception as e:
        print(f"Failed to register database connection for {tenant_slug}: {e}")
        return None
    
def get_isolated_user_membership(user, tenant_slug):
    """Check membership in tenant database"""
    try:
        from .models import TenantUser
        from template_service.database_router import set_current_tenant, clear_current_tenant
        
        # Switch to tenant database context
        set_current_tenant(tenant_slug)
        
        tenant_user = TenantUser.objects.filter(username=user.username, is_active=True).first()
        
        # Clear tenant context
        clear_current_tenant()
        
        if tenant_user:
            return {
                'role': tenant_user.role,
                'status': 'ACTIVE',
                'is_admin': tenant_user.role in ['TENANT_ADMIN', 'COMPLIANCE_MANAGER'],
                'can_assign_controls': tenant_user.role in ['TENANT_ADMIN', 'COMPLIANCE_MANAGER'],
                'can_manage_users': tenant_user.role == 'TENANT_ADMIN'
            }
        return None
    except Exception as e:
        print(f"Error getting isolated membership: {e}")
        return None


def get_service2_token():
    """
    Get JWT token for Service 2 API calls
    In production, this should use service-to-service authentication
    """
    # For now, return None - we'll implement proper service auth later
    return None


class IsTenantMember(BasePermission):
    """
    Permission that ensures user is a member of the current tenant
    Checks with Service 2 for user membership
    """
    
    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusers can access everything
        if request.user.is_superuser:
            return True
        
        # Get current tenant from middleware
        current_tenant = get_current_tenant()
        if not current_tenant:
            # Try to get from request headers as fallback
            current_tenant = request.META.get('HTTP_X_TENANT_SLUG')
        
        if not current_tenant:
            return False
        
        # Check membership with Service 2
        membership = get_user_tenant_membership(request.user, current_tenant)
        if membership:
            # Store membership in request for later use
            request.tenant_membership = membership
            return True
        
        return False



class CanCreateUsers(BasePermission):
    """Permission to create users in tenant"""
    
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True  # Platform Super Admin can create anywhere
        
        if hasattr(request, 'tenant_membership'):
            membership = request.tenant_membership
            return membership and membership.get('role') == 'TENANT_ADMIN'
        
        return False

class IsPlatformSuperAdmin(BasePermission):
    """Permission for platform-level operations"""
    
    def has_permission(self, request, view):
        return request.user.is_superuser

def validate_role_creation(creator_role, target_role):
    """Validate if creator can assign target role"""
    if creator_role == 'PLATFORM_SUPER_ADMIN':
        return True
    
    if creator_role == 'TENANT_ADMIN':
        # Tenant admins cannot create other tenant admins
        allowed_roles = ['COMPLIANCE_MANAGER', 'AUDITOR', 'EMPLOYEE']
        return target_role in allowed_roles
    
    return False

class IsTenantAdmin(BasePermission):
    """
    Permission for tenant admin operations
    """
    
    def has_permission(self, request, view):
        # First check if user is tenant member
        if not IsTenantMember().has_permission(request, view):
            return False
        
        # Check if user has admin role
        if hasattr(request, 'tenant_membership'):
            role = request.tenant_membership.get('role')
            return role in ['TENANT_ADMIN', 'COMPLIANCE_MANAGER']
        
        return False


class CanAssignControls(BasePermission):
    """
    Permission for users who can assign controls to employees
    """
    
    def has_permission(self, request, view):
        if not IsTenantMember().has_permission(request, view):
            return False
        
        if hasattr(request, 'tenant_membership'):
            role = request.tenant_membership.get('role')
            return role in ['TENANT_ADMIN', 'COMPLIANCE_MANAGER']
        
        return False


class IsOwnerOrTenantAdmin(BasePermission):
    """
    Object-level permission to only allow owners or tenant admins to edit
    """
    
    def has_object_permission(self, request, view, obj):
        # Superusers can do anything
        if request.user.is_superuser:
            return True
        
        # Check if user is tenant admin
        if hasattr(request, 'tenant_membership'):
            role = request.tenant_membership.get('role')
            if role in ['TENANT_ADMIN', 'COMPLIANCE_MANAGER']:
                return True
        
        # Check if user owns the object (for assignments, responses, etc.)
        if hasattr(obj, 'assigned_to_employee_id'):
            return obj.assigned_to_employee_id == request.user.id
        
        if hasattr(obj, 'answered_by_employee_id'):
            return obj.answered_by_employee_id == request.user.id
        
        if hasattr(obj, 'uploaded_by_employee_id'):
            return obj.uploaded_by_employee_id == request.user.id
        
        return False