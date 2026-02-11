"""
Medusa store adapter (placeholder for future implementation).

This adapter will provide Medusa-specific provisioning and configuration logic.
Currently returns NotImplementedError to indicate the platform is not yet supported.
"""

from typing import Optional

from .base import StoreAdapter


class MedusaAdapter(StoreAdapter):
    """
    Adapter for Medusa stores.
    
    This is a placeholder implementation. To add Medusa support:
    1. Add Medusa Helm chart dependency
    2. Implement platform-specific configuration
    3. Add Medusa-specific setup commands
    """
    
    def get_chart_dependency(self) -> dict:
        """
        TODO: Define Medusa Helm chart dependency.
        
        Example:
        return {
            "name": "medusa",
            "version": "1.x.x",
            "repository": "https://charts.medusa.com/",
            "condition": "medusa.enabled"
        }
        """
        raise NotImplementedError("Medusa adapter not yet implemented")
    
    def get_default_values(self, store_name: str, host: str) -> dict:
        """
        TODO: Generate Medusa-specific Helm values.
        
        Example:
        return {
            "store": {
                "name": store_name,
                "engine": "medusa",
                "host": host,
            },
            "medusa": {
                "enabled": True,
                # Medusa-specific configuration
            },
            "postgresql": {
                "enabled": True,
                # PostgreSQL configuration for Medusa
            }
        }
        """
        raise NotImplementedError("Medusa adapter not yet implemented")
    
    def configure_platform(self, namespace: str, release_name: str) -> tuple[bool, Optional[str]]:
        """
        TODO: Perform post-deployment Medusa configuration.
        
        This might include:
        - Running database migrations
        - Creating admin user
        - Seeding initial data
        - Configuring payment providers
        """
        raise NotImplementedError("Medusa adapter not yet implemented")
    
    def get_admin_password(self, namespace: str, release_name: str) -> Optional[str]:
        """
        TODO: Retrieve Medusa admin password.
        
        Implementation will depend on how Medusa stores credentials.
        """
        raise NotImplementedError("Medusa adapter not yet implemented")
    
    def get_pod_selector(self, release_name: str) -> str:
        """
        TODO: Get label selector for Medusa pods.
        
        Example:
        return f"app.kubernetes.io/name=medusa,app.kubernetes.io/instance={release_name}"
        """
        raise NotImplementedError("Medusa adapter not yet implemented")
    
    def get_store_url_path(self) -> str:
        """
        TODO: Define Medusa store URL path.
        
        Medusa typically serves the store at the root path.
        """
        return "/"
    
    def is_platform_ready(self, namespace: str, release_name: str) -> bool:
        """
        TODO: Check if Medusa is fully initialized.
        
        This might check:
        - Database migrations completed
        - Admin user created
        - API responding to health checks
        """
        raise NotImplementedError("Medusa adapter not yet implemented")
