"""
Example adapter implementation template.

Copy this file to create a new platform adapter.
Replace 'Example' with your platform name (e.g., Shopify, Magento, PrestaShop).
"""

import subprocess
from typing import Optional

from .base import StoreAdapter


class ExampleAdapter(StoreAdapter):
    """
    Adapter for Example e-commerce platform.
    
    TODO: Replace this docstring with your platform description.
    """
    
    def get_chart_dependency(self) -> dict:
        """
        Get the Helm chart dependency for your platform.
        
        TODO: Update with your platform's Helm chart details.
        You can either:
        1. Use an existing public Helm chart
        2. Create a custom chart in charts/store/charts/
        """
        return {
            "name": "example-platform",
            "version": "1.x.x",
            "repository": "https://charts.example.com/",
            "condition": "example.enabled"
        }
    
    def get_default_values(self, store_name: str, host: str) -> dict:
        """
        Generate platform-specific Helm values.
        
        TODO: Customize these values for your platform.
        Include all necessary configuration for:
        - Application settings
        - Database configuration
        - Ingress/networking
        - Resource limits
        """
        return {
            "store": {
                "name": store_name,
                "engine": "example",  # Update with your engine name
                "host": host,
            },
            "example": {  # Replace with your platform name
                "enabled": True,
                # Add platform-specific configuration here
                # For example:
                # "adminEmail": "admin@example.com",
                # "storeName": store_name,
            },
            # Database configuration (if needed)
            # "postgresql": {
            #     "enabled": True,
            #     "auth": {
            #         "database": "example_db",
            #         "username": "example_user"
            #     }
            # },
            "ingress": {
                "enabled": True,
                "className": "nginx",
            }
        }
    
    def configure_platform(self, namespace: str, release_name: str) -> tuple[bool, Optional[str]]:
        """
        Perform post-deployment configuration.
        
        TODO: Implement platform-specific setup steps.
        This might include:
        - Running database migrations
        - Creating admin user
        - Installing plugins/extensions
        - Seeding initial data
        - Configuring payment providers
        - Setting up themes
        
        Return (True, None) on success, or (False, error_message) on failure.
        """
        # Example: Find the application pod
        pod_name = self._get_app_pod(namespace, release_name)
        if not pod_name:
            return False, "Application pod not found"
        
        # Example: Check if platform is initialized
        if not self._is_platform_initialized(namespace, pod_name):
            return False, "Platform not initialized"
        
        # TODO: Add your platform-specific configuration commands here
        # For example, running CLI commands inside the pod:
        # success = self._run_setup_command(namespace, pod_name)
        # if not success:
        #     return False, "Setup command failed"
        
        return True, None
    
    def get_admin_password(self, namespace: str, release_name: str) -> Optional[str]:
        """
        Retrieve the admin password from Kubernetes secrets.
        
        TODO: Update the secret name and key for your platform.
        Most Helm charts store passwords in Kubernetes secrets.
        """
        try:
            cmd = [
                "kubectl",
                "get",
                "secret",
                "-n",
                namespace,
                f"{release_name}-example",  # Update secret name
                "-o",
                "jsonpath={.data.admin-password}",  # Update key name
            ]
            encoded_password = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
            
            if not encoded_password:
                return None
            
            # Decode base64
            import base64
            password = base64.b64decode(encoded_password).decode("utf-8")
            return password
        except (subprocess.CalledProcessError, Exception):
            return None
    
    def get_pod_selector(self, release_name: str) -> str:
        """
        Get the Kubernetes label selector for your platform's pods.
        
        TODO: Update with your platform's pod labels.
        Check your Helm chart's pod template to find the correct labels.
        """
        return f"app.kubernetes.io/name=example,app.kubernetes.io/instance={release_name}"
    
    def get_store_url_path(self) -> str:
        """
        Get the URL path for the store frontend.
        
        TODO: Update with your platform's store path.
        Examples:
        - "/" for root path
        - "/shop/" for WooCommerce
        - "/store/" for custom paths
        """
        return "/"
    
    def is_platform_ready(self, namespace: str, release_name: str) -> bool:
        """
        Check if the platform is fully initialized.
        
        TODO: Implement platform-specific readiness check.
        This should verify that the application is ready to use,
        not just that the pods are running.
        """
        pod_name = self._get_app_pod(namespace, release_name)
        if not pod_name:
            return False
        return self._is_platform_initialized(namespace, pod_name)
    
    # Helper methods (TODO: Implement these for your platform)
    
    def _get_app_pod(self, namespace: str, release_name: str) -> Optional[str]:
        """Find the main application pod."""
        cmd = [
            "kubectl",
            "get",
            "pods",
            "-n",
            namespace,
            "-l",
            self.get_pod_selector(release_name),
            "-o",
            "jsonpath={.items[0].metadata.name}",
        ]
        try:
            pod_name = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
            return pod_name if pod_name else None
        except subprocess.CalledProcessError:
            return None
    
    def _is_platform_initialized(self, namespace: str, pod_name: str) -> bool:
        """
        Check if the platform is initialized.
        
        TODO: Implement platform-specific initialization check.
        Examples:
        - Check if database migrations are complete
        - Check if admin user exists
        - Check if API responds to health check
        """
        # Example: Run a health check command
        cmd = [
            "kubectl",
            "exec",
            "-n",
            namespace,
            pod_name,
            "--",
            "curl",
            "-f",
            "http://localhost/health",  # Update with your health endpoint
        ]
        try:
            subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def _run_setup_command(self, namespace: str, pod_name: str, command: str) -> bool:
        """
        Run a setup command inside the pod.
        
        TODO: Customize for your platform's CLI or setup scripts.
        """
        cmd = [
            "kubectl",
            "exec",
            "-n",
            namespace,
            pod_name,
            "--",
            "bash",
            "-c",
            command,
        ]
        try:
            subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False
