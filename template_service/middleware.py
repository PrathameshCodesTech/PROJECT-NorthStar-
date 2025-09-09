"""
Custom middleware for caching and performance optimization
"""

import time
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache


class PerformanceMiddleware(MiddlewareMixin):
    """Middleware to track request performance and cache headers"""
    
    def process_request(self, request):
        request._performance_start = time.time()
        return None
    
    def process_response(self, request, response):
        if hasattr(request, '_performance_start'):
            duration = time.time() - request._performance_start
            response['X-Response-Time'] = f"{duration:.3f}s"
            
            # Log slow requests
            if duration > 2.0:  # Requests taking more than 2 seconds
                print(f"SLOW REQUEST: {request.method} {request.path} took {duration:.3f}s")
        
        # Add cache headers for API responses
        if request.path.startswith('/api/'):
            if response.status_code == 200:
                response['Cache-Control'] = 'public, max-age=60'  # Cache for 1 minute
            else:
                response['Cache-Control'] = 'no-cache'
        
        return response


class TenantCacheMiddleware(MiddlewareMixin):
    """Middleware to manage tenant-specific caching"""
    
    def process_request(self, request):
        # Clear tenant-specific cache on write operations
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            tenant_slug = getattr(request, 'tenant', None)
            if tenant_slug:
                # Invalidate tenant-related cache entries
                cache_pattern = f"user_membership:*:{tenant_slug}"
                pass
        
        return None


class RateLimitMiddleware(MiddlewareMixin):
    """Rate limiting middleware for internal APIs"""
    
    def process_request(self, request):
        # Only rate limit internal APIs
        if not request.path.startswith('/api/v1/internal/'):
            return None
        
        # Get client identifier
        client_ip = self.get_client_ip(request)
        internal_token = request.headers.get('X-Internal-Token', '')
        
        # Create rate limit key
        rate_key = f"rate_limit:internal:{client_ip}:{internal_token[:8]}"
        
        # Check current request count
        current_count = cache.get(rate_key, 0)
        
        # Allow 100 requests per minute for internal APIs
        if current_count >= 100:
            from django.http import JsonResponse
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'limit': 100,
                'window': '1 minute'
            }, status=429)
        
        # Increment counter
        cache.set(rate_key, current_count + 1, 60)  # 60 seconds
        
        return None
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')