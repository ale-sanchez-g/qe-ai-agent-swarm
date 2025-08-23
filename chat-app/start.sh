#!/bin/bash

# Start script for AI Chat Application

echo "🚀 Starting AI Chat Application..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check for environment file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Please create one based on .env.example"
    echo "📝 Copying .env.example to .env..."
    cp .env.example .env
    echo "🔑 Please edit .env file with your actual credentials before running the app"
    exit 1
fi

# Load environment variables
echo "🔐 Loading environment variables..."
export $(cat .env | xargs)

# Start the application
echo "🌐 Starting Flask application on http://localhost:5001"
python app.py