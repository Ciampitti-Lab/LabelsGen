# Deployment Guide for Render

## 🚀 Deploy to Render

### Prerequisites
- GitHub repository with your code
- Render account (free tier available)

### Steps

1. **Push your code to GitHub**
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

2. **Create a new Web Service on Render**
   - Go to [render.com](https://render.com)
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Select this repository

3. **Configure the service**
   - **Name**: `ciampittilab-labels-generator`
   - **Environment**: `Docker`
   - **Plan**: `Free` (or paid for better performance)
   - **Docker Build Context**: `/` (root directory)

4. **Environment Variables** (optional)
   - Set `RENDER=1` (automatically set by the Docker ENV)

5. **Deploy**
   - Click "Deploy Web Service"
   - Wait for build and deployment (5-10 minutes)
   - Your app will be available at `https://your-service-name.onrender.com`

### 🔧 Configuration Details

**Docker**: The app uses an optimized Docker setup with:
- Non-root user for security
- Gunicorn WSGI server with 2 workers
- In-memory PDF storage (no file system dependencies)
- Health checks for reliability

**Performance**: 
- PDFs are generated in-memory and served directly
- No file system persistence (cloud-native)
- Optimized for concurrent users

### 🌐 Local Development vs Deployment

- **Local**: Files saved to `labels_pdf/` folder
- **Render**: Files served from memory, no persistence needed

### 🛠️ Troubleshooting

If deployment fails:
1. Check build logs in Render dashboard
2. Ensure all dependencies are in `requirements.txt`
3. Verify Docker builds locally: `docker build -t labels-app .`

### 🔒 Security Features

- Non-root container user
- No file system writes in production
- Environment-based configuration
- Health checks for monitoring 