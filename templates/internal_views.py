"""
Internal APIs for Service 1 - Handles requests from Service 2
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from django.core.management import call_command
from django.db import connections
from django.conf import settings as django_settings

import requests
from template_service.tenant_utils import copy_framework_templates_to_tenant


class InternalMigrateTenantView(APIView):
    """Run migrations on tenant database"""
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        # Verify internal token
        internal_token = request.headers.get('X-Internal-Token')
        expected = getattr(django_settings, 'INTERNAL_REGISTER_DB_TOKEN', None)
        if not expected or internal_token != expected:
            return Response({'error': 'Unauthorized - Internal API only'}, status=status.HTTP_401_UNAUTHORIZED)

        tenant_slug = request.data.get('tenant_slug')
        connection_name = request.data.get('connection_name')
        if not tenant_slug or not connection_name:
            return Response({'error': 'tenant_slug and connection_name required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get tenant database credentials from Service 2
            response = requests.get(
                f'http://localhost:8001/api/v2/internal/tenants/{tenant_slug}/credentials/',
                headers={'X-Internal-Token': django_settings.INTERNAL_REGISTER_DB_TOKEN},
                timeout=10
            )
            if response.status_code != 200:
                return Response({'error': 'Could not get tenant credentials from Service 2'}, status=status.HTTP_400_BAD_REQUEST)

            creds = response.json()['credentials']

            # Register database alias dynamically
            db_config = {
                **django_settings.DATABASES['default'],
                'NAME': creds['database_name'],
                'USER': creds['database_user'],
                'PASSWORD': creds['database_password'],
                'HOST': creds['database_host'],
                'PORT': creds['database_port'],
            }
            connections.databases[connection_name] = db_config

            # Run migrations
            call_command('migrate', 'company_compliance', database=connection_name, verbosity=1, interactive=False)

            return Response({
                'success': True,
                'tenant_slug': tenant_slug,
                'connection_name': connection_name,
                'message': 'Migrations completed successfully'
            })
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InternalDistributeTemplatesView(APIView):
    """Distribute framework templates to tenant database"""
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        # Verify internal token
        internal_token = request.headers.get('X-Internal-Token')
        expected = getattr(django_settings, 'INTERNAL_REGISTER_DB_TOKEN', None)
        if not expected or internal_token != expected:
            return Response({'error': 'Unauthorized - Internal API only'}, status=status.HTTP_401_UNAUTHORIZED)

        tenant_slug = request.data.get('tenant_slug')
        framework_ids = request.data.get('framework_ids')
        if not tenant_slug:
            return Response({'error': 'tenant_slug required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get tenant database credentials from Service 2
            response = requests.get(
                f'http://localhost:8001/api/v2/internal/tenants/{tenant_slug}/credentials/',
                headers={'X-Internal-Token': django_settings.INTERNAL_REGISTER_DB_TOKEN},
                timeout=10
            )
            if response.status_code != 200:
                return Response({'error': 'Could not get tenant credentials from Service 2'}, status=status.HTTP_400_BAD_REQUEST)

            creds = response.json()['credentials']
            connection_name = creds['connection_name']

            # Register database alias dynamically
            db_config = {
                **django_settings.DATABASES['default'],
                'NAME': creds['database_name'],
                'USER': creds['database_user'],
                'PASSWORD': creds['database_password'],
                'HOST': creds['database_host'],
                'PORT': creds['database_port'],
            }
            connections.databases[connection_name] = db_config

            # Copy framework templates
            result = copy_framework_templates_to_tenant(tenant_slug=tenant_slug, framework_ids=framework_ids)

            return Response({
                'success': True,
                'tenant_slug': tenant_slug,
                'frameworks_copied': len(result),
                'details': [{'name': fw['framework'].name, 'controls': fw['controls_copied']} for fw in result]
            })
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
