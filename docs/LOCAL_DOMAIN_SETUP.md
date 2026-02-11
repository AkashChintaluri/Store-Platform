# Local Domain Setup & Troubleshooting

## Overview

This document explains how local domain routing works for stores in the development environment, the challenges encountered, and how they were resolved.

## Architecture

### Components
1. **Kubernetes Ingress Controller** (nginx-ingress)
   - Listens on `localhost:80` and `localhost:443`
   - Routes traffic based on hostname to different store namespaces
   
2. **Store Namespaces**
   - Each store runs in its own Kubernetes namespace
   - WordPress service exposed as ClusterIP (internal only)
   
3. **Ingress Resources**
   - Created per-store to route `<store-name>.localhost` → store's WordPress service

## What I Did

### 1. Initial Setup
- Installed nginx-ingress controller in Docker Desktop Kubernetes
- Configured each store with an ingress resource
- Set hostnames using pattern: `<store-name>.localhost`

### 2. URL Configuration
- Environment variables for URL generation:
  ```
  STORE_BASE_DOMAIN=localhost
  STORE_BASE_PORT=
  ```
- Backend generates URLs: `http://<store-name>.localhost/shop/`

### 3. Helm Chart Configuration
Each store Helm release creates:
- **Namespace**: Isolated environment per store
- **WordPress deployment**: Running the store application
- **MariaDB**: Database for WordPress
- **Ingress resource**: Routes external traffic to WordPress service
- **NetworkPolicy**: Security isolation
- **ResourceQuota**: Resource limits per store

## Problems Faced & Solutions

### Problem 1: nip.io vs localhost Domain Confusion
**Issue**: Initial Helm values used `{{ .Release.Namespace }}.127.0.0.1.nip.io` for store hostnames, but URLs weren't accessible.

**Background**: 
- `nip.io` is a wildcard DNS service: `<anything>.127.0.0.1.nip.io` resolves to `127.0.0.1`
- Useful for testing with "real" DNS without configuring `/etc/hosts`
- However, ingress controller needs to match the exact hostname

**Root Cause**: 
1. Helm chart used `127.0.0.1.nip.io` pattern in values
2. The hostname pattern `my-store-2.127.0.0.1.nip.io` caused DNS resolution issues
3. **Critical Issue**: The store name ending with a number (e.g., `my-store-2`) combined with the nip.io pattern caused the DNS service to misinterpret the hostname
4. DNS resolved `my-store-2.127.0.0.1.nip.io` to `2.127.0.0` instead of `127.0.0.1`
5. The number at the end of the store name (`-2`) was being parsed as part of the IP address
6. This caused all traffic to route to the wrong IP address, making stores completely inaccessible
7. Backend generated URLs with `localhost` domain creating additional mismatch

**Additional Issue**: The numeric pattern `127.0.0.1` at the end of the domain confuses WordPress's URL normalization logic, causing redirects and canonical URL issues.

**Example of the Problem**:
```
Store name: my-store-2
Expected hostname: my-store-2.127.0.0.1.nip.io → should resolve to 127.0.0.1
Actual DNS resolution: 2.127.0.0 (nip.io parsed the trailing -2 as part of IP)
Result: Store completely inaccessible
```

**Solution**: Standardized on `localhost` everywhere:
- Helm values: `host: "{{ .Release.Namespace }}.localhost"`
- Backend: `STORE_BASE_DOMAIN=localhost`
- Ingress controller `EXTERNAL-IP: localhost` works with `.localhost` subdomains
- No external DNS dependency
- No numeric domain suffix to confuse DNS parsing
- Store names with numbers (e.g., `my-store-2.localhost`) work correctly

**Why localhost works**: Docker Desktop's ingress controller on Windows/Mac automatically handles `*.localhost` routing without DNS configuration, and WordPress treats `.localhost` as a standard domain without URL normalization issues. Most importantly, store names with trailing numbers don't cause DNS parsing conflicts.

**Alternative**: Could keep `nip.io` pattern if:
- Helm values consistently use it: `{{ .Release.Namespace }}.127.0.0.1.nip.io`
- Backend matches: `STORE_BASE_DOMAIN=127.0.0.1.nip.io`
- Requires internet connectivity for DNS lookups
- **Critical limitation**: Store names MUST NOT end with numbers (e.g., avoid `my-store-2`, use `my-store-two` or `mystore2` instead)
- Still may encounter WordPress URL handling issues with numeric suffix

### Problem 2: ResourceQuota Blocking Job Creation
**Issue**: WooCommerce automation job failed to start with error:
```
Error creating: pods "test-store-woo-ready-mc9tq" is forbidden: 
failed quota: store-quota: must specify limits.cpu for: woo-ready; 
limits.memory for: woo-ready; requests.cpu for: woo-ready; 
requests.memory for: woo-ready
```

**Root Cause**: Helm chart created a ResourceQuota for each namespace, but the job template didn't include resource requests/limits.

**Solution**: Added resource specifications to the job container:
```yaml
resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "500m"
    memory: "512Mi"
```

### Problem 3: WooCommerce Automation Job Failures
**Issue**: Kubernetes Job couldn't access WordPress installation at `/opt/bitnami/wordpress/`.

**Root Cause**: 
- Job pod only had PVC mounted at `/bitnami/wordpress` (for wp-config and wp-content)
- WordPress PHP files are in the image at `/opt/bitnami/wordpress`
- Job pod couldn't see the WordPress installation files

**Failed Approach**: Tried mounting the same PVC and setting paths, but wp-cli still couldn't find WordPress core files.

**Solution**: Pivoted from Job-based automation to backend-driven automation:
1. Removed Kubernetes Job for WooCommerce setup
2. Moved wp-cli commands to orchestrator (`provisioner.py`)
3. Backend executes commands via `kubectl exec` into the running WordPress pod
4. WordPress pod has full access to installation + persistent data

Commands now run as:
```bash
kubectl exec -n <namespace> <wordpress-pod> -- bash -c \
  "cd /opt/bitnami/wordpress && wp plugin activate woocommerce --allow-root"
```

### Problem 4: WordPress Path Confusion
**Issue**: wp-cli commands failed with "This does not seem to be a WordPress installation"

**Root Cause**: wp-cli looks for `wp-load.php` in the current directory or specified `--path`. The Bitnami WordPress image has:
- WordPress core files: `/opt/bitnami/wordpress/`
- Persistent data (wp-config, wp-content): `/bitnami/wordpress/`
- Symlinks connecting them

**Solution**: 
1. Change directory to WordPress installation first: `cd /opt/bitnami/wordpress`
2. Remove `--path` flag from wp-cli commands (uses current directory)
3. Working directory context is preserved in bash `-c` command

### Problem 5: COD Payment Gateway Configuration
**Issue**: Initial command failed with "No data exists for key 'enabled'"
```bash
wp option patch update woocommerce_cod_settings enabled yes
```

**Root Cause**: The `patch update` subcommand expects the option to already exist. Fresh WooCommerce installations don't have this option initialized.

**Solution**: Use WooCommerce CLI to update payment gateway directly:
```bash
wp wc payment_gateway update cod --enabled=true --user=1 --allow-root
```

This command:
- Works even if option doesn't exist
- Properly initializes WooCommerce payment gateway settings
- Requires `--user=1` flag for WooCommerce REST API authentication

### Problem 6: Namespace Termination Conflicts
**Issue**: Creating a store with the same name immediately after deletion fails:
```
Error: unable to create new content in namespace <name> because it is being terminated
```

**Root Cause**: Kubernetes takes 30-60 seconds to fully clean up a namespace (pods, PVCs, secrets, etc.).

**Solution**: 
- Wait for namespace deletion to complete before reusing the name
- Or use a different store name for immediate creation
- Future improvement: Backend could poll namespace status before attempting Helm install

### Problem 7: Port Confusion with Ingress
**Issue**: Initially configured URLs with port 8080, assuming port-forwarding was needed.
```
http://mystore.localhost:8080/shop/
```

**Root Cause**: Misunderstanding of how ingress works. The ingress controller exposes services on standard HTTP ports (80/443), not requiring manual port-forwarding.

**Solution**:
- Verified ingress controller service:
  ```powershell
  kubectl get svc -n ingress-nginx
  # Shows: EXTERNAL-IP: localhost, PORT(S): 80:31209/TCP,443:32085/TCP
  ```
- Removed port from URLs: `http://mystore.localhost/shop/`
- Set `STORE_BASE_PORT=` (empty) in `.env`

## Current Working Configuration

### Backend Environment (.env)
```env
STORE_BASE_DOMAIN=localhost
STORE_BASE_PORT=
```

### Helm Values (values-local.yaml)
```yaml
store:
  host: "{{ .Release.Namespace }}.localhost"

ingress:
  enabled: false  # Using top-level ingress instead

wordpress:
  service:
    type: ClusterIP
  ingress:
    enabled: false
```

### Top-Level Ingress Template
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ .Release.Name }}-store
  namespace: {{ .Release.Namespace }}
spec:
  ingressClassName: nginx
  rules:
    - host: {{ tpl .Values.store.host . | quote }}
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {{ .Release.Name }}-wordpress
                port:
                  number: 80
```

### WooCommerce Automation (provisioner.py)
```python
def configure_woocommerce(namespace: str, release_name: str) -> tuple[bool, str | None]:
    # Find WordPress pod
    # Execute wp-cli commands via kubectl exec
    # Commands:
    # 1. Check WordPress installed
    # 2. Install/activate WooCommerce
    # 3. Create test product
    # 4. Enable COD payment gateway
```

## Access Patterns

### Store Frontend
```
http://<store-name>.localhost/shop/
```

### WordPress Admin
```
http://<store-name>.localhost/wp-admin
Username: user
Password: kubectl get secret -n <namespace> <store-name>-wordpress -o jsonpath='{.data.wordpress-password}' | base64 -d
```

### How It Works
1. Browser sends request to `http://mystore.localhost/shop/`
2. Request goes to `localhost:80` (ingress controller)
3. Ingress controller reads `Host` header: `mystore.localhost`
4. Matches ingress rule for namespace `mystore`
5. Routes to `mystore-wordpress` service on port 80
6. WordPress handles the request

## Testing & Verification

### Check Ingress Controller
```powershell
kubectl get svc -n ingress-nginx
# Should show EXTERNAL-IP: localhost
```

### Check Store Ingress
```powershell
kubectl get ingress -n <store-name>
# Should show host and backend service
```

### Test Store Access
```powershell
curl -H "Host: mystore.localhost" http://localhost/
# Should return WordPress HTML
```

### Verify WooCommerce
1. Access admin: `http://mystore.localhost/wp-admin`
2. Navigate to WooCommerce → Settings → Payments
3. Verify "Cash on delivery" is enabled
4. Check Products → Add New shows WooCommerce product editor
5. Visit `/shop/` to see the test product

## Key Learnings

1. **Ingress eliminates port-forwarding**: With ingress controller on standard ports, stores are directly accessible via hostname routing.

2. **Job pods != Application pods**: Jobs with PVC mounts can't access application files in the image. Use `kubectl exec` into running pods instead.

3. **wp-cli requires WordPress context**: Commands must run from WordPress directory or use correct `--path`. Directory context is simpler.

4. **WooCommerce CLI > wp option**: Use native WooCommerce commands for payment gateway configuration rather than low-level option manipulation.

5. **Namespace lifecycle matters**: Kubernetes resource cleanup is asynchronous. Wait for termination before reusing names.

6. **Orchestrator separation**: Keep infrastructure operations (kubectl, helm, wp-cli) in the orchestrator layer, not in route handlers.

## Future Improvements

1. **Namespace cleanup detection**: Poll namespace status before Helm install to avoid termination conflicts
2. **Password retrieval API**: Add backend endpoint to fetch admin password without kubectl
3. **Health checks**: Verify WooCommerce setup completion with automated checks
4. **Custom domain support**: Allow users to specify custom domains with DNS configuration
5. **TLS/HTTPS**: Configure cert-manager for automatic SSL certificates
6. **Multi-cluster**: Support deploying stores across multiple Kubernetes clusters
