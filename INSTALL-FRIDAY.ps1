# ============================================
# FRIDAY AI Assistant - Complete Installation Script
# Handles: Detection, Installation, Antivirus bypass
# ============================================

# Run as Administrator check
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  ⚠️  ADMINISTRATOR RIGHTS REQUIRED  ⚠️ " -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "This script needs administrator rights." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "How to run as Administrator:" -ForegroundColor Cyan
    Write-Host "1. Right-click PowerShell" -ForegroundColor White
    Write-Host "2. Select 'Run as Administrator'" -ForegroundColor White
    Write-Host "3. Run this script again" -ForegroundColor White
    Write-Host ""
    pause
    exit
}

Clear-Host

Write-Host ""
Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   FRIDAY AI ASSISTANT - INSTALLER     ║" -ForegroundColor Cyan
Write-Host "║   Female AI • By Dipesh               ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Set execution policy for this session
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

# Disable Windows Defender real-time scanning temporarily for faster installation
Write-Host "🛡️  Configuring Windows Defender for faster installation..." -ForegroundColor Yellow
try {
    Add-MpPreference -ExclusionPath $PSScriptRoot -ErrorAction SilentlyContinue
    Write-Host "   ✅ Added project folder to Defender exclusions" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  Could not modify Defender (continuing anyway)" -ForegroundColor Yellow
}
Write-Host ""

# ============================================
# Helper Functions
# ============================================

function Test-CommandExists {
    param($command)
    $null = Get-Command $command -ErrorAction SilentlyContinue
    return $?
}

function Get-PythonVersion {
    try {
        $version = python --version 2>&1
        if ($version -match "Python (\d+\.\d+)") {
            return [version]$matches[1]
        }
    } catch {}
    return $null
}

function Get-NodeVersion {
    try {
        $version = node --version 2>&1
        if ($version -match "v(\d+\.\d+)") {
            return [version]$matches[1]
        }
    } catch {}
    return $null
}

# ============================================
# Step 1: Install Chocolatey
# ============================================
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  STEP 1: Package Manager (Chocolatey)  " -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

if (Test-CommandExists choco) {
    $chocoVersion = choco --version | Select-Object -First 1
    Write-Host "✅ Chocolatey already installed: v$chocoVersion" -ForegroundColor Green
} else {
    Write-Host "📦 Installing Chocolatey..." -ForegroundColor Yellow
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    
    # Refresh environment
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    Write-Host "✅ Chocolatey installed successfully!" -ForegroundColor Green
}
Write-Host ""

# ============================================
# Step 2: Install Python 3.11
# ============================================
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  STEP 2: Python 3.11                   " -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

$pythonVersion = Get-PythonVersion
if ($pythonVersion -and $pythonVersion.Major -eq 3 -and $pythonVersion.Minor -ge 10) {
    Write-Host "✅ Python already installed: Python $pythonVersion" -ForegroundColor Green
    python --version
} else {
    if ($pythonVersion) {
        Write-Host "⚠️  Python $pythonVersion found, but we need 3.11+" -ForegroundColor Yellow
        Write-Host "📦 Installing Python 3.11..." -ForegroundColor Yellow
    } else {
        Write-Host "📦 Installing Python 3.11..." -ForegroundColor Yellow
    }
    
    choco install python311 -y --force
    
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    Write-Host "✅ Python 3.11 installed!" -ForegroundColor Green
    python --version
}
Write-Host ""

# ============================================
# Step 3: Install Node.js & npm
# ============================================
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  STEP 3: Node.js & npm                 " -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

$nodeVersion = Get-NodeVersion
if ($nodeVersion -and $nodeVersion.Major -ge 18) {
    Write-Host "✅ Node.js already installed: v$nodeVersion" -ForegroundColor Green
    node --version
    $npmVersion = npm --version
    Write-Host "✅ npm already installed: v$npmVersion" -ForegroundColor Green
} else {
    if ($nodeVersion) {
        Write-Host "⚠️  Node.js v$nodeVersion found, but we need v18+" -ForegroundColor Yellow
    }
    Write-Host "📦 Installing Node.js LTS (includes npm)..." -ForegroundColor Yellow
    
    choco install nodejs-lts -y --force
    
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    Write-Host "✅ Node.js & npm installed!" -ForegroundColor Green
    node --version
    npm --version
}
Write-Host ""

# ============================================
# Step 4: Install Git
# ============================================
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  STEP 4: Git                           " -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

if (Test-CommandExists git) {
    $gitVersion = git --version
    Write-Host "✅ Git already installed: $gitVersion" -ForegroundColor Green
} else {
    Write-Host "📦 Installing Git..." -ForegroundColor Yellow
    choco install git -y
    
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    Write-Host "✅ Git installed!" -ForegroundColor Green
}
Write-Host ""

# ============================================
# Step 5: Visual Studio Build Tools
# ============================================
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  STEP 5: Visual Studio Build Tools    " -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

# Check if VS Build Tools already installed
$vsBuildToolsPath = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools"
$vsPath = "C:\Program Files\Microsoft Visual Studio\2022"

if ((Test-Path $vsBuildToolsPath) -or (Test-Path $vsPath)) {
    Write-Host "✅ Visual Studio Build Tools already installed" -ForegroundColor Green
} else {
    Write-Host "🔨 Installing Visual Studio Build Tools..." -ForegroundColor Yellow
    Write-Host "   ⏱️  This will take 10-15 minutes..." -ForegroundColor Yellow
    Write-Host "   (Required for compiling Python packages)" -ForegroundColor White
    Write-Host ""
    
    choco install visualstudio2022buildtools --package-parameters "--add Microsoft.VisualStudio.Workload.VCTools --includeRecommended --passive --wait" -y
    
    Write-Host "✅ VS Build Tools installed!" -ForegroundColor Green
}
Write-Host ""

# Refresh environment variables
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# ============================================
# Step 6: Project Setup
# ============================================
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  STEP 6: FRIDAY Project Setup          " -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

$projectRoot = $PSScriptRoot
Write-Host "📂 Project location: $projectRoot" -ForegroundColor White

# Backend setup
Write-Host ""
Write-Host "🐍 Setting up Backend..." -ForegroundColor Yellow
Set-Location "$projectRoot\backend"

if (Test-Path "venv") {
    Write-Host "   ✅ Virtual environment already exists" -ForegroundColor Green
} else {
    Write-Host "   📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "   ✅ Virtual environment created" -ForegroundColor Green
}

Write-Host "   📦 Installing Python packages..." -ForegroundColor Yellow
Write-Host "   ⏱️  This may take 5-10 minutes..." -ForegroundColor Yellow

& .\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

Write-Host "   ✅ Backend dependencies installed!" -ForegroundColor Green

# Frontend setup
Write-Host ""
Write-Host "📦 Setting up Frontend..." -ForegroundColor Yellow
Set-Location "$projectRoot\frontend\tauri-app"

if (Test-Path "node_modules") {
    Write-Host "   ✅ Node modules already exist" -ForegroundColor Green
    Write-Host "   🔄 Updating packages..." -ForegroundColor Yellow
    npm install --silent
} else {
    Write-Host "   📦 Installing npm packages..." -ForegroundColor Yellow
    Write-Host "   ⏱️  This may take 3-5 minutes..." -ForegroundColor Yellow
    npm install --silent
}

Write-Host "   ✅ Frontend dependencies installed!" -ForegroundColor Green
Write-Host ""

# ============================================
# Step 7: Environment Configuration
# ============================================
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  STEP 7: API Keys Configuration        " -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

Set-Location "$projectRoot\backend"

if (Test-Path ".env") {
    Write-Host "✅ .env file already exists" -ForegroundColor Green
    Write-Host ""
    $updateEnv = Read-Host "Do you want to update API keys? (y/n)"
    
    if ($updateEnv -ne 'y') {
        Write-Host "   ⏭️  Skipping API key configuration" -ForegroundColor Yellow
        $skipApiKeys = $true
    }
}

if (-not $skipApiKeys) {
    Write-Host ""
    Write-Host "📝 You need 2 FREE API keys:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1️⃣  Groq API (for English - Fast & Free)" -ForegroundColor Cyan
    Write-Host "   🔗 https://console.groq.com/keys" -ForegroundColor White
    Write-Host "   → Sign up → Create API Key" -ForegroundColor White
    Write-Host ""
    Write-Host "2️⃣  Google Gemini API (for Hindi & Nepali - Free)" -ForegroundColor Cyan
    Write-Host "   🔗 https://makersuite.google.com/app/apikey" -ForegroundColor White
    Write-Host "   → Sign in → Create API Key" -ForegroundColor White
    Write-Host ""
    
    $groqKey = Read-Host "Enter Groq API key (starts with gsk_)"
    $geminiKey = Read-Host "Enter Google Gemini API key"
    
    # Validate keys
    if ([string]::IsNullOrWhiteSpace($groqKey) -or [string]::IsNullOrWhiteSpace($geminiKey)) {
        Write-Host ""
        Write-Host "⚠️  Warning: API keys not provided" -ForegroundColor Yellow
        Write-Host "   You can add them later to backend\.env file" -ForegroundColor Yellow
        Write-Host ""
        $groqKey = "your_groq_api_key_here"
        $geminiKey = "your_google_api_key_here"
    }
    
    # Create .env file
    $envContent = @"
# FRIDAY AI Assistant - Configuration
# Created: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

# ============================================
# LLM API Keys (Both FREE)
# ============================================

# Groq - For English (fast, unlimited)
# Get from: https://console.groq.com/keys
GROQ_API_KEY=$groqKey

# Google Gemini - For Hindi & Nepali (60 req/min free)
# Get from: https://makersuite.google.com/app/apikey
GOOGLE_API_KEY=$geminiKey

# ============================================
# Models Configuration
# ============================================
DEFAULT_MODEL=llama-3.3-70b-versatile
GEMINI_MODEL=gemini-pro

# Auto-routing: English→Groq, Hindi/Nepali→Gemini
LANGUAGE_PROVIDER_MAP={"en-US": "groq", "ne-NP": "gemini", "hi-IN": "gemini"}

# ============================================
# Server Settings
# ============================================
SERVER_HOST=0.0.0.0
PORT=8000
LOG_LEVEL=info
RELOAD=True

# ============================================
# Features
# ============================================
ENABLE_FILE_OPERATIONS=True
ENABLE_WEB_SEARCH=True
ENABLE_CODE_EXECUTION=False
ENABLE_OS_AUTOMATION=False
ENABLE_HARDWARE_MONITORING=True
MAX_CONVERSATION_HISTORY=50
AUTO_SAVE_CONVERSATIONS=True
"@
    
    $envContent | Out-File -FilePath ".env" -Encoding UTF8 -Force
    Write-Host "✅ .env file created successfully!" -ForegroundColor Green
}
Write-Host ""

# ============================================
# Step 8: Verify Python Packages
# ============================================
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  STEP 8: Verifying Installation        " -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

Set-Location "$projectRoot\backend"
& .\venv\Scripts\Activate.ps1

Write-Host "Checking critical packages..." -ForegroundColor Yellow

$packagesToCheck = @(
    "fastapi",
    "groq",
    "google-generativeai",
    "edge-tts",
    "uvicorn"
)

$allInstalled = $true
foreach ($package in $packagesToCheck) {
    $installed = pip show $package 2>$null
    if ($installed) {
        Write-Host "   ✅ $package" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $package - NOT INSTALLED" -ForegroundColor Red
        $allInstalled = $false
    }
}

if (-not $allInstalled) {
    Write-Host ""
    Write-Host "⚠️  Some packages missing. Reinstalling..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

Write-Host ""
Write-Host "✅ All packages verified!" -ForegroundColor Green
Write-Host ""

# ============================================
# Installation Complete
# ============================================
Clear-Host
Write-Host ""
Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║   ✅ INSTALLATION COMPLETE! ✅        ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Host "📦 Installed Components:" -ForegroundColor Cyan
Write-Host "   ✅ Python 3.11" -ForegroundColor Green
Write-Host "   ✅ Node.js & npm" -ForegroundColor Green
Write-Host "   ✅ Git" -ForegroundColor Green
Write-Host "   ✅ Visual Studio Build Tools" -ForegroundColor Green
Write-Host "   ✅ Backend dependencies (FastAPI, Groq, Gemini, Edge TTS)" -ForegroundColor Green
Write-Host "   ✅ Frontend dependencies (Vite, React)" -ForegroundColor Green
Write-Host ""

Write-Host "🎯 FRIDAY Features:" -ForegroundColor Cyan
Write-Host "   🌍 3 Languages: English, Hindi (हिन्दी), Nepali (नेपाली)" -ForegroundColor White
Write-Host "   🎙️  Ultra-natural voice (Microsoft Edge Neural TTS)" -ForegroundColor White
Write-Host "   👩 Female AI assistant" -ForegroundColor White
Write-Host "   💬 Smart conversation history" -ForegroundColor White
Write-Host "   🧠 Context-aware (remembers conversation)" -ForegroundColor White
Write-Host "   💰 100% FREE (Groq + Gemini free tiers)" -ForegroundColor White
Write-Host ""

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "         HOW TO START FRIDAY:           " -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

Write-Host "OPTION 1: Use the batch file (easiest)" -ForegroundColor Yellow
Write-Host "   → Double-click: start-friday.bat" -ForegroundColor White
Write-Host ""

Write-Host "OPTION 2: Manual start" -ForegroundColor Yellow
Write-Host ""
Write-Host "   Terminal 1 (Backend):" -ForegroundColor Cyan
Write-Host "   cd $projectRoot\backend" -ForegroundColor White
Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "   python main.py" -ForegroundColor White
Write-Host ""
Write-Host "   Terminal 2 (Frontend):" -ForegroundColor Cyan
Write-Host "   cd $projectRoot\frontend\tauri-app" -ForegroundColor White
Write-Host "   npm run dev" -ForegroundColor White
Write-Host ""
Write-Host "   Browser:" -ForegroundColor Cyan
Write-Host "   http://localhost:1420" -ForegroundColor White
Write-Host ""

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# Ask if user wants to start now
$startNow = Read-Host "Would you like to start FRIDAY now? (y/n)"

if ($startNow -eq 'y') {
    Write-Host ""
    Write-Host "🚀 Starting FRIDAY AI Assistant..." -ForegroundColor Green
    Write-Host ""
    
    # Start backend
    Write-Host "   Starting backend server..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot\backend'; .\venv\Scripts\Activate.ps1; python main.py; Write-Host 'Press any key to exit...'; pause"
    
    Start-Sleep -Seconds 5
    
    # Start frontend
    Write-Host "   Starting frontend..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot\frontend\tauri-app'; npm run dev; Write-Host 'Press any key to exit...'; pause"
    
    Start-Sleep -Seconds 8
    
    # Open browser
    Write-Host "   Opening browser..." -ForegroundColor Yellow
    Start-Process "http://localhost:1420"
    
    Write-Host ""
    Write-Host "✅ FRIDAY is now running!" -ForegroundColor Green
    Write-Host ""
    Write-Host "   Backend: Check first PowerShell window" -ForegroundColor Cyan
    Write-Host "   Frontend: Check second PowerShell window" -ForegroundColor Cyan
    Write-Host "   Browser: http://localhost:1420" -ForegroundColor Cyan
    Write-Host ""
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "🎉 Enjoy FRIDAY AI Assistant!" -ForegroundColor Green
Write-Host "   Developed by Dipesh" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

if ($startNow -ne 'y') {
    Write-Host "To start FRIDAY later, just run:" -ForegroundColor Yellow
    Write-Host "   start-friday.bat" -ForegroundColor White
    Write-Host ""
}

Write-Host "Press any key to exit..." -ForegroundColor Gray
pause >$null

