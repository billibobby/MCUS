# 🚀 Railway Deployment Guide for MCUS

## Step 1: Prepare Your Project

Make sure your project has these files in the root directory:

```
MCUS/
├── web_app.py              # Main Flask application
├── requirements.txt         # Python dependencies
├── src/                    # Your Python modules
│   ├── server_manager.py
│   ├── mod_manager.py
│   └── network_manager.py
├── templates/              # HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── mods.html
│   ├── hosting.html
│   ├── players.html
│   ├── settings.html
│   ├── modrinth_search.html
│   └── popular_mods.html
├── server/                 # Minecraft server files (will be created)
├── backups/                # World backups (will be created)
└── config.json            # Configuration file (will be created)
```

## Step 2: Create Railway Account

1. **Go to** [railway.app](https://railway.app)
2. **Sign up** with your GitHub account
3. **Verify your email** if required

## Step 3: Deploy Your Project

### Option A: Deploy from GitHub (Recommended)

1. **Push your MCUS project to GitHub** (if not already done)
2. **Go to Railway Dashboard**
3. **Click "New Project"**
4. **Select "Deploy from GitHub repo"**
5. **Choose your MCUS repository**
6. **Railway will automatically detect** it's a Python app
7. **Click "Deploy"**

### Option B: Deploy from Local Files

1. **Install Railway CLI**:
   ```bash
   npm install -g @railway/cli
   ```

2. **Login to Railway**:
   ```bash
   railway login
   ```

3. **Initialize project**:
   ```bash
   railway init
   ```

4. **Deploy**:
   ```bash
   railway up
   ```

## Step 4: Configure Environment Variables

In your Railway project dashboard:

1. **Go to "Variables" tab**
2. **Add these environment variables**:

```
PORT=3000
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here-2024
```

## Step 5: Get Your Public URL

1. **Go to "Settings" tab** in your Railway project
2. **Copy the "Domain" URL** (e.g., `https://mcus-production-1234.up.railway.app`)
3. **Share this URL** with your friends!

## Step 6: Test Your Deployment

1. **Open the Railway URL** in your browser
2. **Test the features**:
   - Dashboard loads correctly
   - Can join hosting network
   - Can search for mods
   - Can manage settings

## 🔧 Troubleshooting

### Common Issues:

1. **Build fails**: Check that all files are in the correct locations
2. **Import errors**: Make sure `src/` folder contains all Python modules
3. **Template errors**: Ensure all HTML files are in `templates/` folder
4. **Port issues**: Set `PORT=3000` in environment variables

### Check Logs:

1. **Go to Railway Dashboard**
2. **Click on your project**
3. **Go to "Deployments" tab**
4. **Click on the latest deployment**
5. **Check "Logs"** for any errors

## 📱 Sharing with Friends

Once deployed, share this message with your friends:

```
🎮 MCUS - Minecraft Unified Server Management
🌐 Access: [Your Railway URL]
📱 Works on: Phone, Tablet, Computer
🔧 Features:
   • Mod management and downloads
   • Server control and monitoring
   • Player management
   • Multi-computer hosting network
   • Real-time status updates
```

## 🎯 Next Steps

1. **Test all features** with your friends
2. **Customize the design** if needed
3. **Add authentication** for security
4. **Set up automatic backups**
5. **Monitor usage** in Railway dashboard

## 💰 Cost

- **Free tier**: $5 credit monthly (plenty for MCUS)
- **No credit card required** for basic usage
- **Automatic scaling** based on usage

Your MCUS web interface will now be accessible to friends worldwide using the Railway URL! 