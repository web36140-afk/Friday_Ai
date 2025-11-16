#!/bin/bash

# JARVIS - Netlify Deployment Script
# Run this to deploy frontend to Netlify

echo "🚀 Deploying JARVIS to Netlify..."

# Check if backend URL is set
if [ -z "$VITE_API_URL" ]; then
    echo "⚠️  Warning: VITE_API_URL not set"
    echo "Please set your backend URL:"
    echo "export VITE_API_URL=https://your-backend-url.com"
    echo ""
    read -p "Enter backend URL (or press Enter to use localhost): " BACKEND_URL
    if [ ! -z "$BACKEND_URL" ]; then
        export VITE_API_URL=$BACKEND_URL
    fi
fi

# Navigate to frontend
cd frontend/tauri-app

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Build for production
echo "🔨 Building for production..."
npm run build

# Check if Netlify CLI is installed
if ! command -v netlify &> /dev/null; then
    echo "📥 Installing Netlify CLI..."
    npm install -g netlify-cli
fi

# Deploy
echo "🌐 Deploying to Netlify..."
netlify deploy --prod --dir=dist

echo "✅ Deployment complete!"
echo ""
echo "🎉 Your JARVIS is now live!"
echo ""
echo "Next steps:"
echo "1. Note your Netlify URL"
echo "2. Update VITE_API_URL in Netlify dashboard if needed"
echo "3. Test on mobile and desktop"
echo ""

