#!/usr/bin/env bash
# ==============================================================================
# Tawreed.org - Safe VPS Deployment Script (Hostinger Ubuntu / Nginx)
# Designed to run alongside existing websites without interfering with them.
# ==============================================================================

set -e

DOMAIN="tawreed.org"
WEB_ROOT="/var/www/tawreed.org/html"
NGINX_AVAILABLE="/etc/nginx/sites-available/tawreed.org"
NGINX_ENABLED="/etc/nginx/sites-enabled/tawreed.org"
REPO_URL="https://github.com/Athulpk2005/Tawreed.org.git"

echo "=========================================================="
echo " Starting Safe Deployment for: $DOMAIN"
echo " Existing sites on this VPS will NOT be modified."
echo "=========================================================="

# 1. Verify sudo / root
if [ "$EUID" -ne 0 ]; then
  echo "[-] Please run as root or with sudo:"
  echo "    sudo bash deploy_vps.sh"
  exit 1
fi

# 2. Update package lists & install prerequisites if missing
echo "[+] Checking prerequisites (git, nginx, certbot)..."
apt-get update -y
apt-get install -y git nginx certbot python3-certbot-nginx

# 3. Create dedicated web directory
echo "[+] Setting up web directory at $WEB_ROOT..."
mkdir -p "$WEB_ROOT"

# 4. Clone or update repository
if [ -d "$WEB_ROOT/.git" ]; then
  echo "[+] Repository already exists. Pulling latest updates..."
  cd "$WEB_ROOT"
  git fetch origin main
  git reset --hard origin/main
else
  echo "[+] Cloning repository from $REPO_URL..."
  # Clean directory if empty or non-git
  rm -rf /tmp/tawreed_clone
  git clone "$REPO_URL" /tmp/tawreed_clone
  cp -r /tmp/tawreed_clone/. "$WEB_ROOT/"
  rm -rf /tmp/tawreed_clone
fi

# 5. Set proper permissions
echo "[+] Setting secure permissions for www-data..."
chown -R www-data:www-data "/var/www/tawreed.org"
find "/var/www/tawreed.org" -type d -exec chmod 755 {} \;
find "/var/www/tawreed.org" -type f -exec chmod 644 {} \;

# 6. Create dedicated Nginx Server Block (Virtual Host)
echo "[+] Creating dedicated Nginx configuration for $DOMAIN..."
cat << 'EOF' > "$NGINX_AVAILABLE"
server {
    listen 80;
    listen [::]:80;
    server_name tawreed.org www.tawreed.org;

    root /var/www/tawreed.org/html;
    index index.html;

    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml application/javascript application/json image/svg+xml;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Main routing: clean URLs (e.g. /about -> about.html)
    location / {
        try_files $uri $uri.html $uri/ =404;
    }

    # Static Assets Caching
    location ~* \.(ico|css|js|gif|jpeg|jpg|png|webp|woff|woff2|svg)$ {
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    # Deny access to hidden / sensitive files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }

    # Error pages
    error_page 404 /index.html;

    access_log /var/log/nginx/tawreed_access.log;
    error_log /var/log/nginx/tawreed_error.log;
}
EOF

# 7. Enable Nginx site
if [ ! -f "$NGINX_ENABLED" ]; then
  echo "[+] Enabling Nginx site configuration..."
  ln -s "$NGINX_AVAILABLE" "$NGINX_ENABLED"
fi

# 8. Test Nginx Configuration (Safety Check!)
echo "[+] Testing Nginx configuration syntax..."
if nginx -t; then
  echo "[+] Nginx syntax check PASSED! Safely reloading Nginx..."
  systemctl reload nginx
else
  echo "[-] ERROR: Nginx configuration test failed! Removing Tawreed symlink to protect existing sites."
  rm -f "$NGINX_ENABLED"
  nginx -t
  systemctl reload nginx
  echo "[-] Existing websites were preserved and are unaffected."
  exit 1
fi

echo ""
echo "=========================================================="
echo " Deployment Complete!"
echo "=========================================================="
echo "Next Steps:"
echo "1. In GoDaddy DNS Management for 'tawreed.org':"
echo "   - Set Type 'A', Name '@', Value: <YOUR_VPS_IP>"
echo "   - Set Type 'CNAME', Name 'www', Value: '@' (or A record to <YOUR_VPS_IP>)"
echo ""
echo "2. Once DNS is resolving, enable Free SSL (HTTPS) by running:"
echo "   sudo certbot --nginx -d tawreed.org -d www.tawreed.org"
echo "=========================================================="
