# Setting up HTTPS for Job Tracker on Oracle Cloud

This guide will help you set up HTTPS for your Job Tracker application running on Oracle Cloud, which is essential for proper Google Analytics tracking.

## Why HTTPS is Important

1. **Security**: HTTPS encrypts all data between the browser and server
2. **Google Analytics**: Many browsers block analytics tracking on non-HTTPS sites
3. **Modern Browser Features**: Some advanced features require HTTPS
4. **User Trust**: HTTPS shows users that your site is secure

## Option 1: Using Oracle Cloud Load Balancer with SSL

### Prerequisites
- Your Job Tracker application running on Oracle Cloud
- A registered domain name (you can get a free domain from Freenom if needed)
- Access to your domain's DNS settings

### Step 1: Create a Load Balancer
1. Log in to your Oracle Cloud Console
2. Navigate to Networking > Load Balancers
3. Click "Create Load Balancer"
4. Choose a name, e.g., "job-tracker-lb"
5. Select your VCN and subnets
6. Choose the appropriate shape (typically "10Mbps" is sufficient for small apps)
7. Click "Create"

### Step 2: Configure Listeners
1. In your new load balancer, click "Listeners"
2. Add an HTTPS listener:
   - Name: https
   - Port: 443
   - Protocol: HTTPS
   - Leave other settings as default for now
   - Click "Add Listener"

### Step 3: Configure Backend Sets
1. Click "Backend Sets"
2. Create a new backend set:
   - Name: job-tracker-backend
   - Policy: Round Robin (or your preference)
   - Health Check Policy: HTTP (port 8501 for Streamlit)

### Step 4: Add the Backend
1. In your backend set, click "Backends"
2. Add your instance:
   - IP Address: Your instance's private IP
   - Port: 8501 (for Streamlit)
   - Weight: 1
   - Click "Add"

### Step 5: Create a Certificate
1. Click "Certificates"
2. Click "Create Certificate"
3. You have two options:
   - **Option A: Use Let's Encrypt** (Recommended)
     - Use a tool like Certbot to generate certificates
     - Then upload them to Oracle Cloud
   - **Option B: Import an existing certificate**
     - If you already have an SSL certificate

### Step 6: Configure DNS
1. Log in to your domain registrar
2. Add a new A record pointing to your load balancer's public IP address
3. Wait for DNS propagation (can take up to 24-48 hours)

## Option 2: Using Nginx with Let's Encrypt

This option uses Certbot and Let's Encrypt to set up SSL directly on your server.

### Step 1: Install Certbot
```bash
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx
```

### Step 2: Configure Nginx
Make sure your Nginx configuration includes your domain name:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### Step 3: Obtain SSL Certificate
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### Step 4: Verify Auto-Renewal
```bash
sudo certbot renew --dry-run
```

## Option 3: Using a Domain with Cloudflare (Easiest)

Cloudflare offers free SSL certificates and can proxy traffic to your Oracle Cloud instance.

### Step 1: Sign Up for Cloudflare
1. Go to [cloudflare.com](https://cloudflare.com)
2. Sign up and add your domain

### Step 2: Update DNS Records
1. Add an A record pointing to your Oracle Cloud instance's public IP
2. Make sure the "Proxy status" is set to "Proxied" (orange cloud)

### Step 3: Enable SSL
1. Go to the "SSL/TLS" section
2. Set SSL/TLS encryption mode to "Full" or "Full (strict)"

### Step 4: Update Oracle Cloud Firewall Rules
Make sure incoming traffic on ports 80 and 443 is allowed in your Oracle Cloud security list.

## Troubleshooting

### Google Analytics Issues
1. After setting up HTTPS, update your Google Analytics configuration to force HTTPS:
   ```javascript
   gtag('config', 'G-EGVJQG5M34', {
       'transport_url': 'https://www.google-analytics.com/g/collect',
       'cookie_flags': 'SameSite=None;Secure'
   });
   ```

2. Test your setup using the Analytics Debug tool at `/static/analytics_debug.html`

### SSL Certificate Issues
- If you're having issues with Let's Encrypt rate limits, you can use the staging environment for testing
- Make sure your domain's DNS records are correctly set up
- Check that your server can be reached on ports 80 and 443

### Nginx Configuration Issues
- Check Nginx error logs: `sudo tail -f /var/log/nginx/error.log`
- Verify Nginx configuration: `sudo nginx -t`
- Restart Nginx after changes: `sudo systemctl restart nginx`

## Additional Resources
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Certbot Instructions](https://certbot.eff.org/)
- [Cloudflare SSL Documentation](https://developers.cloudflare.com/ssl/)
- [Oracle Cloud Load Balancer Documentation](https://docs.oracle.com/en-us/iaas/Content/Balance/home.htm)
