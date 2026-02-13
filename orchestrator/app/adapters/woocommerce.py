"""
WooCommerce store adapter implementation.
"""

import subprocess
from typing import Optional

from .base import StoreAdapter


class WooCommerceAdapter(StoreAdapter):
    def get_chart_dependency(self) -> dict:
        return {
            "name": "wordpress",
            "version": "28.x.x",
            "repository": "https://charts.bitnami.com/bitnami",
            "condition": "wordpress.enabled",
        }

    def get_default_values(self, store_name: str, host: str) -> dict:
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
                        "username": "bn_wordpress",
                    },
                    "primary": {
                        "persistence": {
                            "size": "8Gi",
                        }
                    },
                },
            },
            "ingress": {
                "enabled": True,
                "className": "nginx",
            },
        }

    def configure_platform(self, namespace: str, release_name: str) -> tuple[bool, Optional[str]]:
        pod_name = self._get_wordpress_pod(namespace, release_name)
        if not pod_name:
            return False, "WordPress pod not found"
        if not self._is_wordpress_ready(namespace, pod_name):
            return False, "WordPress core not installed"
        if not self._install_woocommerce(namespace, pod_name):
            return False, "Failed to install/activate WooCommerce"
        if not self._create_test_product(namespace, pod_name):
            return False, "Failed to create test product"
        if not self._enable_cod_payment(namespace, pod_name):
            return False, "Failed to enable COD payment"
        return True, None

    def get_admin_password(self, namespace: str, release_name: str) -> Optional[str]:
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
            import base64
            return base64.b64decode(encoded_password).decode("utf-8")
        except (subprocess.CalledProcessError, Exception):
            return None

    def get_pod_selector(self, release_name: str) -> str:
        return f"app.kubernetes.io/name=wordpress,app.kubernetes.io/instance={release_name}"

    def get_store_url_path(self) -> str:
        return "/shop/"

    def is_platform_ready(self, namespace: str, release_name: str) -> bool:
        pod_name = self._get_wordpress_pod(namespace, release_name)
        if not pod_name:
            return False
        return self._is_wordpress_ready(namespace, pod_name)

    def _get_wordpress_pod(self, namespace: str, release_name: str) -> Optional[str]:
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
            "(wp plugin is-active woocommerce --allow-root || wp plugin activate woocommerce --allow-root) && "
            "wp eval 'if (class_exists(\"WC_Install\")) { WC_Install::create_pages(); }' --allow-root",
        ]
        try:
            subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False

    def _create_test_product(self, namespace: str, pod_name: str) -> bool:
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
            "PRODUCT_IDS=$(wp post list --post_type=product --post_status=publish --format=ids --allow-root 2>/dev/null || true); "
            "if [ -z \"$PRODUCT_IDS\" ]; then "
            "PRODUCT_ID=$(wp post create --post_type=product --post_status=publish --post_title='Sample Product' --porcelain --allow-root); "
            "wp post meta set $PRODUCT_ID _regular_price '9.99' --allow-root; "
            "wp post meta set $PRODUCT_ID _price '9.99' --allow-root; "
            "wp post meta set $PRODUCT_ID _stock_status 'instock' --allow-root; "
            "wp term set product_type $PRODUCT_ID simple --allow-root || true; "
            "fi",
        ]
        try:
            subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False

    def _enable_cod_payment(self, namespace: str, pod_name: str) -> bool:
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
            "wp option update woocommerce_enable_cod yes --allow-root && "
            "wp option update woocommerce_cod_settings '{\"enabled\":\"yes\"}' --allow-root",
        ]
        try:
            subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False
