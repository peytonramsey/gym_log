# GymLog Deployment Guide

## Deploying to Render

### 1. Prepare Your Code

First, install python-dotenv locally:
```bash
pip install python-dotenv
```

### 2. Push to GitHub

Initialize git and push your code:
```bash
git init
git add .
git commit -m "Initial commit - GymLog fitness tracker"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/gymlog.git
git push -u origin main
```

### 3. Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up with GitHub account
3. Authorize Render to access your repositories

### 4. Create PostgreSQL Database

1. Click **New** → **PostgreSQL**
2. Settings:
   - **Name**: gymlog-db
   - **Database**: gymlog
   - **User**: (auto-generated)
   - **Region**: Choose closest to you
   - **Plan**: Free
3. Click **Create Database**
4. Wait for database to be created (~2 minutes)
5. Copy the **Internal Database URL** (starts with `postgres://`)

### 5. Create Web Service

1. Click **New** → **Web Service**
2. Connect your GitHub repository
3. Settings:
   - **Name**: gymlog
   - **Region**: Same as database
   - **Branch**: main
   - **Root Directory**: (leave empty)
   - **Runtime**: Python 3
   - **Build Command**: `chmod +x build.sh && ./build.sh`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Free

### 6. Add Environment Variables

In the **Environment** section, add:

- **DATABASE_URL**: Paste the Internal Database URL from step 4
- **SECRET_KEY**: Generate a random string (e.g., `openssl rand -hex 32`)
- **PYTHON_VERSION**: `3.11.7`

### 7. Deploy

1. Click **Create Web Service**
2. Render will automatically:
   - Install dependencies
   - Run build script
   - Initialize database
   - Start your app
3. Wait 3-5 minutes for first deployment
4. Your app will be live at: `https://gymlog.onrender.com`

### 8. Access Your App

- **URL**: Click the link at the top of your Render dashboard
- **Mobile**: The URL works on any device - no need to have your computer on!

## Important Notes

### Free Tier Limitations

- **Sleep Mode**: App sleeps after 15 minutes of inactivity
- **Wake Time**: First request after sleep takes ~30 seconds
- **Database**: 90 days expiration on free PostgreSQL
- **Storage**: All data persists between restarts

### Keeping Your App Awake (Optional)

Use a free service like [UptimeRobot](https://uptimerobot.com):
1. Sign up at uptimerobot.com
2. Add your Render URL as a monitor
3. Ping every 5 minutes to keep it awake

### Database Backup

To backup your data:
```bash
# From Render dashboard, go to your database
# Click "Connect" → Copy external connection string
# Use pg_dump to backup:
pg_dump YOUR_EXTERNAL_URL > backup.sql
```

### Local Development

Your app still works locally with SQLite:
```bash
python app.py
```

The `DATABASE_URL` environment variable switches between SQLite (local) and PostgreSQL (production).

## Troubleshooting

### Build Failed
- Check the build logs in Render dashboard
- Verify all files are pushed to GitHub
- Ensure requirements.txt has all dependencies

### App Not Loading
- Check application logs in Render dashboard
- Verify DATABASE_URL is set correctly
- Ensure database is in "Available" status

### Database Connection Error
- Verify you used the **Internal** database URL
- Check that database and web service are in same region
- Ensure database URL starts with `postgresql://` in logs

## Support

If you encounter issues:
1. Check Render logs (Logs tab in dashboard)
2. Verify environment variables are set
3. Ensure database is running
4. Check GitHub repository has all files
