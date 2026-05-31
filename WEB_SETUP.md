# 🌐 Web Application Setup Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
pip install -r web_requirements.txt
```

### 2. Setup API Keys (One-time)

Edit `.env` file:
```env
# Your YouTube API Key (shared)
YOUTUBE_API_KEY=AIzaSyXXXXXXXXXXXX

# Your TikTok App Credentials
TIKTOK_CLIENT_KEY=awXXXXXXXXXXXX
TIKTOK_CLIENT_SECRET=XXXXXXXXXXXXXXX

# Flask Secret Key (generate random string)
FLASK_SECRET_KEY=your-random-secret-key-here
```

### 3. Run Web Application
```bash
python web_app.py
```

Application will start at: **http://localhost:5000**

---

## Client Usage (Super Simple!)

### First Time Setup:
1. Open website: `http://localhost:5000`
2. Click "Connect TikTok Account"
3. Login to TikTok and allow permissions
4. Done! (This is one-time only)

### Daily Usage:
1. Open website
2. Paste YouTube URL
3. Click "Convert & Upload"
4. Wait 1-2 minutes
5. Video automatically uploaded to TikTok!

---

## Deployment Options

### Option 1: Local Server (Your Computer)
```bash
# Run on your computer
python web_app.py

# Share with client using ngrok
ngrok http 5000
# Give client the ngrok URL
```

### Option 2: Heroku (Free/Paid Cloud)
```bash
# Install Heroku CLI
heroku login
heroku create your-app-name

# Add buildpack for FFmpeg
heroku buildpacks:add --index 1 https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git

# Deploy
git push heroku main

# Set environment variables
heroku config:set YOUTUBE_API_KEY=xxx
heroku config:set TIKTOK_CLIENT_KEY=xxx
heroku config:set TIKTOK_CLIENT_SECRET=xxx
```

### Option 3: DigitalOcean Droplet ($5/month)
```bash
# Create Ubuntu droplet
# SSH into server
ssh root@your-server-ip

# Install dependencies
apt update
apt install python3-pip ffmpeg nginx

# Clone your code
git clone your-repo-url
cd your-repo

# Install Python packages
pip3 install -r requirements.txt
pip3 install -r web_requirements.txt

# Setup systemd service
nano /etc/systemd/system/yt2tik.service
```

**Service file:**
```ini
[Unit]
Description=YouTube to TikTok Converter
After=network.target

[Service]
User=root
WorkingDirectory=/root/tiktok-video-uploader
Environment="PATH=/usr/local/bin"
ExecStart=/usr/bin/python3 web_app.py

[Install]
WantedBy=multi-user.target
```

```bash
# Start service
systemctl start yt2tik
systemctl enable yt2tik

# Setup Nginx reverse proxy
nano /etc/nginx/sites-available/yt2tik
```

**Nginx config:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# Enable site
ln -s /etc/nginx/sites-available/yt2tik /etc/nginx/sites-enabled/
systemctl restart nginx
```

---

## Features

✅ **Beautiful Web Interface** - No technical knowledge needed  
✅ **One-time TikTok Connection** - Client connects once, works forever  
✅ **Auto-detect Best Segment** - AI finds the most engaging part  
✅ **Real-time Progress** - Shows download/convert/upload progress  
✅ **Auto Caption Generation** - Creates engaging captions automatically  
✅ **Mobile Friendly** - Works on phones and tablets  
✅ **Error Handling** - Clear error messages if something fails  

---

## Security Notes

1. **Never share your .env file** - Contains sensitive API keys
2. **Use HTTPS in production** - Get free SSL from Let's Encrypt
3. **Add authentication** - If multiple clients, add login system
4. **Rate limiting** - Prevent abuse with Flask-Limiter
5. **Backup tokens** - Store TikTok tokens in database for production

---

## Troubleshooting

**Port already in use:**
```bash
# Change port in web_app.py
app.run(debug=True, host='0.0.0.0', port=8000)
```

**FFmpeg not found:**
```bash
# Install FFmpeg
# Windows: Download from ffmpeg.org
# Mac: brew install ffmpeg
# Linux: sudo apt install ffmpeg
```

**TikTok OAuth fails:**
- Check redirect URI matches exactly
- Verify client key/secret are correct
- Make sure app is approved by TikTok

---

## Cost Breakdown

**Free Option:**
- Your computer + ngrok = $0/month
- YouTube API = Free (10,000 units/day)
- TikTok API = Free

**Paid Option:**
- DigitalOcean Droplet = $5/month
- Domain name = $10/year
- SSL Certificate = Free (Let's Encrypt)

**Total: ~$5-10/month for professional setup**

---

## Client Billing

You can charge your client:
- **One-time setup**: $200-500
- **Monthly maintenance**: $50-100/month
- **Per video**: $2-5 per conversion

---

Need help with deployment? Let me know! 🚀
