# Railway Deployment Guide for MCUS

This guide helps you deploy MCUS to Railway for cloud hosting.

## 🚀 Quick Deploy

### Option 1: Deploy from GitHub (Recommended)

1. **Fork the Repository**
   - Go to the MCUS GitHub repository
   - Click "Fork" to create your own copy

2. **Deploy to Railway**
   - Go to [Railway.app](https://railway.app)
   - Sign in with your GitHub account
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your forked MCUS repository
   - Click "Deploy"

3. **Configure Environment Variables** (Optional)
   - In your Railway project dashboard
   - Go to "Variables" tab
   - Add any custom environment variables if needed

4. **Access Your Deployment**
   - Railway will provide a URL like: `https://your-app-name.railway.app`
   - Click the URL to access your MCUS instance

### Option 2: Deploy from Local Files

1. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login to Railway**
   ```bash
   railway login
   ```

3. **Initialize Project**
   ```bash
   railway init
   ```

4. **Deploy**
   ```bash
   railway up
   ```

## ⚙️ Configuration Files

MCUS includes several configuration files for Railway deployment:

### Procfile
```
web: python web_app.py --port $PORT
```
- Tells Railway how to start the application
- Uses the `$PORT` environment variable provided by Railway

### railway.json
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python web_app.py --port $PORT",
    "healthcheckPath": "/",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```
- Configures Railway deployment settings
- Sets up health checks and restart policies

### nixpacks.toml
```toml
[phases.setup]
nixPkgs = ["python39", "openjdk21"]

[phases.install]
cmds = ["pip install -r requirements.txt"]

[phases.build]
cmds = ["python setup.py"]

[start]
cmd = "python web_app.py --port $PORT"
```
- Ensures Python 3.9 and Java 21 are installed
- Installs dependencies and runs setup

## 🔧 Environment Variables

You can configure MCUS using environment variables in Railway:

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Web server port | `3000` |
| `DEBUG` | Enable debug mode | `False` |
| `JAVA_MEMORY` | Java memory allocation | `4G` |
| `MINECRAFT_VERSION` | Default Minecraft version | `1.21.7` |

## 📊 Monitoring

Railway provides built-in monitoring:

1. **Logs**: View real-time application logs
2. **Metrics**: Monitor CPU, memory, and network usage
3. **Health Checks**: Automatic health monitoring
4. **Restarts**: Automatic restart on failure

## 🔄 Updates

To update your Railway deployment:

1. **Push to GitHub**: Update your forked repository
2. **Auto-Deploy**: Railway will automatically redeploy
3. **Manual Deploy**: Or trigger manual deployment from Railway dashboard

## 🚨 Important Notes

### Limitations
- **No Minecraft Server**: Railway is for the web interface only
- **No File Persistence**: Server files won't persist between deployments
- **Resource Limits**: Railway has CPU and memory limits

### Best Practices
- **Use for Web Interface**: Deploy the web interface to Railway
- **Local Server**: Run the actual Minecraft server locally
- **Backup Data**: Regularly backup your server files
- **Monitor Usage**: Keep an eye on Railway usage limits

## 🛠️ Troubleshooting

### Common Issues

1. **Build Fails**
   - Check that all files are committed to GitHub
   - Verify `requirements.txt` is correct
   - Check Railway logs for specific errors

2. **App Won't Start**
   - Verify the Procfile is correct
   - Check that `web_app.py` exists
   - Review Railway logs for startup errors

3. **Port Issues**
   - Ensure the app uses `$PORT` environment variable
   - Check that the app binds to `0.0.0.0`

4. **Dependencies Missing**
   - Verify `requirements.txt` includes all dependencies
   - Check that `nixpacks.toml` specifies required packages

### Getting Help

- **Railway Docs**: [docs.railway.app](https://docs.railway.app)
- **Railway Discord**: [discord.gg/railway](https://discord.gg/railway)
- **MCUS Issues**: GitHub repository issues

## 💰 Pricing

Railway offers:
- **Free Tier**: $5 credit monthly
- **Pro Plan**: Pay-as-you-go pricing
- **Team Plan**: Collaborative features

## 🔗 Useful Links

- [Railway Dashboard](https://railway.app/dashboard)
- [Railway Documentation](https://docs.railway.app)
- [Railway CLI](https://docs.railway.app/develop/cli)
- [MCUS GitHub Repository](https://github.com/yourusername/MCUS)

---

**Happy deploying! 🚀** 