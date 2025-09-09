"""
Multi-Tenant Database Router
Automatically routes queries to correct tenant database based on context
"""

from django.conf import settings
import threading
import contextlib
from contextvars import ContextVar
import logging

logger = logging.getLogger(__name__)

# Use ContextVar for async-safe tenant context
_tenant_context: ContextVar[str] = ContextVar('tenant_context', default=None)

# Fallback thread-local for backwards compatibility
_thread_locals = threading.local()


def get_current_tenant():
    """Get current tenant from context (async-safe)"""
    # Try ContextVar first (async-safe)
    tenant = _tenant_context.get(None)
    if tenant:
        return tenant
    
    # Fallback to thread-local
    return getattr(_thread_locals, 'tenant', None)


def set_current_tenant(tenant_slug):
    """Set current tenant in context (async-safe)"""
    if tenant_slug:
        # Validate tenant_slug format
        import re
        if not re.match(r'^[a-z0-9-]{3,50}$', tenant_slug):
            logger.warning(f"Invalid tenant_slug format: {tenant_slug}")
            return False
        
        _tenant_context.set(tenant_slug)
        _thread_locals.tenant = tenant_slug  # Fallback
        logger.debug(f"Set tenant context: {tenant_slug}")
        return True
    return False


def clear_current_tenant():
    """Clear current tenant from context (async-safe)"""
    current = get_current_tenant()
    if current:
        logger.debug(f"Clearing tenant context: {current}")
    
    _tenant_context.set(None)
    if hasattr(_thread_locals, 'tenant'):
        delattr(_thread_locals, 'tenant')


@contextlib.contextmanager
def tenant_context(tenant_slug):
    """Context manager for safe tenant switching"""
    previous_tenant = get_current_tenant()
    if set_current_tenant(tenant_slug):
        try:
            yield tenant_slug
        finally:
            if previous_tenant:
                set_current_tenant(previous_tenant)
            else:
                clear_current_tenant()
    else:
        # Invalid tenant_slug, don't switch context
        yield None


class ComplianceRouter:
    """
    Database router for multi-tenant compliance system with context validation
    
    Routing Rules:
    - templates app models → main database (default)
    - company_compliance app models → tenant database
    - tenant management models → main database (default)
    """
    
    def db_for_read(self, model, **hints):
        """Determine which database to read from with validation"""
        
        # Templates app always uses main database
        if model._meta.app_label == 'templates':
            return 'default'
        
        # Company compliance models use tenant database
        if model._meta.app_label == 'company_compliance':
            tenant = get_current_tenant()
            if tenant:
                connection_name = f"{tenant}_compliance_db"
                
                # Validate that the database connection exists
                from django.db import connections
                if connection_name in connections.databases:
                    return connection_name
                else:
                    logger.warning(f"Tenant database {connection_name} not found, falling back to default")
                    return 'default'
            
            # No tenant context - this might be a problem
            logger.warning(f"No tenant context for company_compliance model: {model.__name__}")
            return 'default'
        
        # Everything else uses main database
        return 'default'
    
    def db_for_write(self, model, **hints):
        """Determine which database to write to"""
        return self.db_for_read(model, **hints)
    
    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations between objects in the same database"""
        db_set = {'default'}
        
        # Add current tenant database to allowed set
        tenant = get_current_tenant()
        if tenant:
            db_set.add(f"{tenant}_compliance_db")
        
        # Allow relations if both objects are in the same allowed database
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Determine which apps can migrate to which databases"""
        
        # Main database: templates app and Django built-ins
        if db == 'default':
            return app_label in ['templates', 'auth', 'contenttypes', 'sessions', 'admin', 'messages']
        
        # Tenant databases: only company_compliance app
        if db.endswith('_compliance_db'):
            return app_label == 'company_compliance'
        
        # Deny migration for unknown databases
        return False


class TenantMiddleware:
    """
    Middleware to extract tenant from request and set tenant context
    
    Supports multiple tenant detection methods:
    1. Subdomain: techcorp.compliance.com
    2. Header: X-Tenant-Slug
    3. URL path: /tenant/techcorp/api/...
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        tenant_slug = self.extract_tenant_from_request(request)
        
        if tenant_slug:
            set_current_tenant(tenant_slug)
            request.tenant = tenant_slug
        else:
            clear_current_tenant()
            request.tenant = None
        
        response = self.get_response(request)
        
        # Clear tenant context after request
        clear_current_tenant()
        
        return response
    
    def extract_tenant_from_request(self, request):
        """Extract tenant slug from request using multiple methods"""
        
        # Method 1: Subdomain detection
        host = request.get_host()
        if '.' in host:
            subdomain = host.split('.')[0]
            # Check if subdomain is a valid tenant (you might want to validate this)
            if subdomain not in ['www', 'api', 'admin']:
                return subdomain
        
        # Method 2: Custom header
        tenant_header = request.META.get('HTTP_X_TENANT_SLUG')
        if tenant_header:
            return tenant_header
        
        # Method 3: URL path parameter
        if hasattr(request, 'resolver_match') and request.resolver_match:
            if 'tenant' in request.resolver_match.kwargs:
                return request.resolver_match.kwargs['tenant']
        
        # Method 4: Query parameter (for development/testing)
        tenant_param = request.GET.get('tenant')
        if tenant_param:
            return tenant_param
        
        return None