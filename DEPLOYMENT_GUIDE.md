# MCUS Deployment Guide

## 🌐 Hosting Options for Friends to Access

### Option 1: Railway (Recommended - Free)
1. **Sign up** at [railway.app](https://railway.app)
2. **Connect your GitHub** repository
3. **Deploy** your MCUS project
4. **Get a public URL** like `https://your-mcus-app.railway.app`
5. **Share the URL** with your friends

### Option 2: Render (Free)
1. **Sign up** at [render.com](https://render.com)
2. **Create a new Web Service**
3. **Connect your GitHub** repository
4. **Set build command**: `pip install -r requirements.txt`
5. **Set start command**: `python web_app.py`
6. **Deploy** and get a public URL

### Option 3: Heroku (Free tier discontinued)
1. **Sign up** at [heroku.com](https://heroku.com)
2. **Install Heroku CLI**
3. **Create app**: `heroku create your-mcus-app`
4. **Deploy**: `git push heroku main`
5. **Get URL**: `https://your-mcus-app.herokuapp.com`

### Option 4: Vercel (Free)
1. **Sign up** at [vercel.com](https://vercel.com)
2. **Import your GitHub** repository
3. **Deploy** automatically
4. **Get URL**: `https://your-mcus-app.vercel.app`

## 🚀 Quick Setup for Railway (Easiest)

### Step 1: Prepare Your Project
```bash
# Make sure you have these files in your project:
# - web_app.py
# - requirements.txt
# - src/ (folder with all your Python modules)
# - templates/ (folder with all HTML templates)
```

### Step 2: Create Railway Account
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"

### Step 3: Deploy
1. **Select your MCUS repository**
2. **Railway will automatically detect** it's a Python app
3. **Set environment variables** (if needed):
   - `PORT`: 3000
4. **Deploy** and wait for build to complete

### Step 4: Get Your URL
- Railway will give you a URL like: `https://mcus-production-1234.up.railway.app`
- **Share this URL** with your friends!

## 🔧 Local Development vs Production

### Local Development
```bash
python web_app.py
# Access at: http://localhost:3000
```

### Production (Railway/Render/etc.)
- **Automatic deployment** from GitHub
- **Public URL** for friends to access
- **No need to expose your IP**

## 📝 Required Files for Deployment

Make sure your project has these files:

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
├── server/                 # Minecraft server files
├── backups/                # World backups
└── config.json            # Configuration file
```

## 🌍 Environment Variables

For production deployment, you might want to set these:

```bash
# Railway/Render Environment Variables
PORT=3000
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
```

## 🔒 Security Considerations

1. **Change the secret key** in `web_app.py`
2. **Use HTTPS** (automatic with Railway/Render)
3. **Set up authentication** if needed
4. **Limit access** to trusted friends

## 📱 Sharing with Friends

Once deployed, share the URL with your friends:

```
🎮 MCUS Server Management
🌐 Access: https://your-mcus-app.railway.app
📱 Works on: Phone, Tablet, Computer
🔧 Features: Mod management, server control, player management
```

## 🆘 Troubleshooting

### Common Issues:
1. **Import errors**: Make sure all files are in the correct folders
2. **Port issues**: Set `PORT` environment variable to 3000
3. **Template errors**: Ensure all HTML files are in `templates/` folder
4. **Build failures**: Check `requirements.txt` has all dependencies

### Getting Help:
- Check the deployment platform's logs
- Ensure all Python files are properly formatted
- Verify all required files are present

## 🎯 Next Steps

1. **Deploy to Railway** (recommended for beginners)
2. **Test the web interface** with your friends
3. **Customize the design** if needed
4. **Add more features** like user authentication
5. **Set up automatic backups** for your Minecraft world

Your friends will be able to access the MCUS interface from anywhere in the world using the public URL! 