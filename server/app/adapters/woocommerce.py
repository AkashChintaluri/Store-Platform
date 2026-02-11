"""
WooCommerce store adapter implementation.

This adapter provides WooCommerce-specific provisioning and configuration logic.
"""

import subprocess
from typing import Optional

from .base import StoreAdapter


class WooCommerceAdapter(StoreAdapter):
    """
    Adapter for WooCommerce stores (WordPress + WooCommerce plugin).
    """
    
    def get_chart_dependency(self) -> dict:
        """Get Bitnami WordPress chart dependency."""
        return {
            "name": "wordpress",
            "version": "28.x.x",
            "repository": "https://charts.bitnami.com/bitnami",
            "condition": "wordpress.enabled"
        }
    
    def get_default_values(self, store_name: str, host: str) -> dict:
        """Generate WooCommerce-specific Helm values."""
        return {
            "store": {
                "name": store_name,
                "engine": "wordpress",
                "host": host,
            },
            "wordpress": {
                "enabled": True,
                "wordpressUsername": "user",
                "wordpressEmail": "admin@example.com",
                "wordpressBlogName": store_name,
                "wordpressPlugins": "woocommerce",
                "mariadb": {
                    "enabled": True,
                    "auth": {
                        "database": "wordpress",
                        "username": "bn_wordpress"
                    },
                    "primary": {
                        "persistence": {
                            "size": "8Gi"
                        }
                    }
                }
            },
            "ingress": {
                "enabled": True,
                "className": "nginx",
            }
        }
    
    def configure_platform(self, namespace: str, release_name: str) -> tuple[bool, Optional[str]]:
        """
        Configure WooCommerce by installing and activating the plugin.
        
        This runs wp-cli commands inside the WordPress pod to:
        1. Install WooCommerce plugin
        2. Activate WooCommerce
        3. Create a test product
        4. Enable Cash on Delivery payment
        """
        # Find the WordPress pod
        pod_name = self._get_wordpress_pod(namespace, release_name)
        if not pod_name:
            return False, "WordPress pod not found"
        
        # Check if WordPress core is installed
        if not self._is_wordpress_ready(namespace, pod_name):
            return False, "WordPress core not installed"
        
        # Install/activate WooCommerce
        if not self._install_woocommerce(namespace, pod_name):
            return False, "Failed to install/activate WooCommerce"
        
        # Create test product
        if not self._create_test_product(namespace, pod_name):
            return False, "Failed to create test product"
        
        # Enable COD payment
        if not self._enable_cod_payment(namespace, pod_name):
            return False, "Failed to enable COD payment"
        
        return True, None
    
    def get_admin_password(self, namespace: str, release_name: str) -> Optional[str]:
        """Retrieve WordPress admin password from Kubernetes secret."""
        try:
            cmd = [
                "kubectl",
                "get",
                "secret",
                "-n",
                namespace,
                f"{release_name}-wordpress",
                "-o",
                "jsonpath={.data.wordpress-password}",
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
        """Get label selector for WordPress pods."""
        return f"app.kubernetes.io/name=wordpress,app.kubernetes.io/instance={release_name}"
    
    def get_store_url_path(self) -> str:
        """WooCommerce store is at /shop/ path."""
        return "/shop/"
    
    def is_platform_ready(self, namespace: str, release_name: str) -> bool:
        """Check if WordPress core is installed and ready."""
        pod_name = self._get_wordpress_pod(namespace, release_name)
        if not pod_name:
            return False
        return self._is_wordpress_ready(namespace, pod_name)
    
    # Private helper methods
    
    def _get_wordpress_pod(self, namespace: str, release_name: str) -> Optional[str]:
        """Find the WordPress pod name."""
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
    
    def _is_wordpress_ready(self, namespace: str, pod_name: str) -> bool:
        """Check if WordPress core is installed."""
        cmd = [
            "kubectl",
            "exec",
            "-n",
            namespace,
            pod_name,
            "--",
            "bash",
            "-c",
            "cd /opt/bitnami/wordpress && wp core is-installed --allow-root",
        ]
        try:
            subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def _install_woocommerce(self, namespace: str, pod_name: str) -> bool:
        """Install and activate WooCommerce plugin."""
        cmd = [
            "kubectl",
            "exec",
            "-n",
            namespace,
            pod_name,
            "--",
            "bash",
            "-c",
            "cd /opt/bitnami/wordpress && "
            "(wp plugin is-installed woocommerce --allow-root || wp plugin install woocommerce --activate --allow-root) && "
            "(wp plugin is-active woocommerce --allow-root || wp plugin activate woocommerce --allow-root)",
        ]
        try:
            subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def _create_test_product(self, namespace: str, pod_name: str) -> bool:
        """Create a test product if none exist."""
        cmd = [
            "kubectl",
            "exec",
            "-n",
            namespace,
            pod_name,
            "--",
            "bash",
            "-c",
            "cd /opt/bitnami/wordpress && "
            "PRODUCTS=$(wp post list --post_type=product --format=ids --allow-root) && "
            "[[ -z \"$PRODUCTS\" ]] && wp wc product create --name='Test Product' --type=simple --status=publish --regular_price='10.00' --user=1 --allow-root || true",
        ]
        try:
            subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def _enable_cod_payment(self, namespace: str, pod_name: str) -> bool:
        """Enable Cash on Delivery payment method."""
        cmd = [
            "kubectl",
            "exec",
            "-n",
            namespace,
            pod_name,
            "--",
            "bash",
            "-c",
            "cd /opt/bitnami/wordpress && "
            "wp wc payment_gateway update cod --enabled=true --user=1 --allow-root",
        ]
        try:
            subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False
