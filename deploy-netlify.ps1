# JARVIS - Netlify Deployment Script (PowerShell)
# Run this to deploy frontend to Netlify

Write-Host "🚀 Deploying JARVIS to Netlify..." -ForegroundColor Cyan

# Check if backend URL is set
if (-not $env:VITE_API_URL) {
    Write-Host "⚠️  Warning: VITE_API_URL not set" -ForegroundColor Yellow
    Write-Host "Please set your backend URL:"
    Write-Host 'Example: $env:VITE_API_URL="https://your-backend-url.com"'
    Write-Host ""
    $backendUrl = Read-Host "Enter backend URL (or press Enter to use localhost)"
    if ($backendUrl) {
        $env:VITE_API_URL = $backendUrl
        Write-Host "✅ Backend URL set to: $backendUrl" -ForegroundColor Green
    }
}

# Navigate to frontend
Set-Location frontend/tauri-app

# Install dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
npm install

# Build for production
Write-Host "🔨 Building for production..." -ForegroundColor Yellow
npm run build

# Check if Netlify CLI is installed
$netlifyInstalled = Get-Command netlify -ErrorAction SilentlyContinue
if (-not $netlifyInstalled) {
    Write-Host "📥 Installing Netlify CLI..." -ForegroundColor Yellow
    npm install -g netlify-cli
}

# Deploy
Write-Host "🌐 Deploying to Netlify..." -ForegroundColor Yellow
netlify deploy --prod --dir=dist

Write-Host ""
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "🎉 Your JARVIS is now live!" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Note your Netlify URL"
Write-Host "2. Update VITE_API_URL in Netlify dashboard if needed"
Write-Host "3. Test on mobile and desktop"
Write-Host "4. Share with your users!"
Write-Host ""

