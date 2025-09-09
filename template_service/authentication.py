"""
Cross-service JWT authentication for Service 1
Validates tokens by calling Service 2's user endpoint
"""

import requests
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.models import User
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class CrossServiceJWTAuthentication(JWTAuthentication):
    """
    JWT Authentication that validates tokens via Service 2
    """


    def authenticate(self, request):
        """Authenticate user by validating JWT with Service 2"""
        print("🔍 CrossServiceJWTAuthentication.authenticate() called")
        logger.info("CrossServiceJWTAuthentication starting validation")
        
        header = self.get_header(request)
        if header is None:
            print("❌ No Authorization header found")
            return None
            
        raw_token = self.get_raw_token(header)
        if raw_token is None:
            print("❌ No token in Authorization header")
            return None

        print(f"✅ Token extracted: {str(raw_token)[:50]}...")
        
        # Always validate with Service 2 first
        user_data = self.validate_token_with_service2(raw_token.decode('utf-8'))
        if not user_data:
            print("❌ Service 2 validation failed")
            return None
            
        print(f"✅ Service 2 validated user: {user_data.get('username')}")
        
        # Get or create local user based on Service 2 response
        user = self.get_or_create_user_from_service2(user_data)
        if not user:
            print("❌ Failed to create/get local user")
            return None
            
        print(f"✅ Local user created/found: {user.username}")
        return (user, raw_token)
    
    def validate_token_with_service2(self, token):
        """Validate JWT token with Service 2"""
        print(f"🌐 Calling Service 2 validation: {settings.SERVICE2_URL}/api/v2/auth/validate-token/")
        print(f"Token being sent: {token[:50]}...")
        import jwt
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            print(f"Token payload: {decoded}")
            print(f"Token expires at: {decoded.get('exp')}")
            import time
            print(f"Current timestamp: {int(time.time())}")
        except Exception as e:
            print(f"Could not decode token: {e}")



        try:
            response = requests.get(
                f'{settings.SERVICE2_URL}/api/v2/auth/validate-token/',
                headers={'Authorization': f'Bearer {token}'},
                timeout=10
            )
            
            print(f"📡 Service 2 response: {response.status_code}")
            print(f"📡 Service 2 response body: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('valid'):
                    print("✅ Service 2 says token is valid")
                    return result.get('user')
                else:
                    print("❌ Service 2 says token is invalid")
            else:
                print(f"❌ Service 2 returned non-200: {response.status_code}")
            
            return None
                
        except Exception as e:
            print(f"💥 Exception calling Service 2: {e}")
            logger.error(f"Failed to validate token with Service 2: {e}")
            return None

    
    def get_or_create_user_from_service2(self, user_data):
        """Get or create local user based on Service 2 data"""
        if not user_data:
            return None
            
        user_id = user_data.get('id')
        username = user_data.get('username')
        email = user_data.get('email', '')
        is_superuser = user_data.get('is_superuser', False)
        
        try:
            user, created = User.objects.get_or_create(
                id=user_id,
                defaults={
                    'username': username,
                    'email': email,
                    'is_superuser': is_superuser,
                    'is_staff': is_superuser
                }
            )
            
            if not created:
                # Update existing user
                user.username = username
                user.email = email
                user.is_superuser = is_superuser
                user.is_staff = is_superuser
                user.save()
                
            return user
            
        except Exception as e:
            logger.error(f"Failed to create/update user: {e}")
            return None