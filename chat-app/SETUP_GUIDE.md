# AI Chat Application - Setup & Deployment Guide

## Quick Start

### 1. Environment Setup

1. **Copy environment template:**
   ```bash
   cd chat-app
   cp .env.example .env
   ```

2. **Edit `.env` file with your credentials:**
   ```bash
   # Required: Your LaunchDarkly SDK key
   LAUNCHDARKLY_SDK_KEY=sdk-12345678-1234-1234-1234-123456789012
   
   # Optional: AI Config key (defaults to 'chat-ai-config')
   LAUNCHDARKLY_AI_CONFIG_KEY=chat-ai-config
   
   # AWS Configuration
   AWS_PROFILE=qbe-split-poc
   AWS_REGION=us-east-1
   
   # Flask Configuration
   FLASK_SECRET_KEY=your-unique-secret-key-here
   ```

### 2. LaunchDarkly Configuration

1. **Create an AI Config** in your LaunchDarkly project:
   - Key: `chat-ai-config` (or whatever you set in `LAUNCHDARKLY_AI_CONFIG_KEY`)
   - Model: Any AWS Bedrock model (e.g., `anthropic.claude-3-haiku-20240307-v1:0`)
   - Provider: `bedrock`
   - System message: Define your AI assistant's behavior

2. **Example AI Config JSON:**
   ```json
   {
     "enabled": true,
     "model": {
       "name": "anthropic.claude-3-haiku-20240307-v1:0",
       "parameters": {}
     },
     "provider": {
       "name": "bedrock"
     },
     "messages": [
       {
         "role": "system",
         "content": "You are a helpful AI assistant. Be concise and friendly."
       }
     ]
   }
   ```

### 3. AWS Setup

1. **Configure AWS credentials** for the specified profile:
   ```bash
   aws configure --profile qbe-split-poc
   ```

2. **Verify Bedrock access:**
   ```bash
   aws bedrock list-foundation-models --region us-east-1 --profile qbe-split-poc
   ```

### 4. Running the Application

#### Option A: Using the start script (Recommended)
```bash
./start.sh
```

#### Option B: Manual setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py
```

#### Option C: Using Docker
```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build manually
docker build -t chat-app .
docker run -p 5000:5000 --env-file .env chat-app
```

### 5. Testing

1. **Open your browser** and navigate to: `http://localhost:5000`

2. **Run automated tests:**
   ```bash
   python test_app.py
   ```

3. **Check health status:**
   ```bash
   curl http://localhost:5000/api/health
   ```

## Features Overview

### 🎨 User Interface
- **Modern Chat Interface**: Clean, responsive design with Bootstrap 5
- **Real-time Messaging**: Instant message exchange with typing indicators
- **Mobile Responsive**: Works seamlessly on desktop and mobile devices
- **Dark/Light Theme**: Gradient background with glassmorphism effects

### 🚀 LaunchDarkly Integration
- **Feature Flags**: Enable/disable chat functionality dynamically
- **AI Configuration**: Real-time model and prompt management
- **Observability**: Comprehensive logging and metrics
- **A/B Testing**: Test different AI models and configurations

### ☁️ AWS Bedrock Integration
- **Multiple Models**: Support for Claude, Llama, Titan, and other models
- **Error Handling**: Graceful error handling with user-friendly messages
- **Session Management**: Maintains conversation context
- **Cost Optimization**: Efficient token usage and caching

### 🔧 Technical Features
- **Session Persistence**: Chat history maintained during user sessions
- **Health Monitoring**: Real-time system health checks
- **Security**: Input validation and XSS protection
- **Performance**: Optimized for speed and reliability

## Configuration Options

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `LAUNCHDARKLY_SDK_KEY` | Your LaunchDarkly SDK key | - | ✅ |
| `LAUNCHDARKLY_AI_CONFIG_KEY` | AI Config key in LD | `chat-ai-config` | ❌ |
| `AWS_PROFILE` | AWS credentials profile | `qbe-split-poc` | ❌ |
| `AWS_REGION` | AWS region for Bedrock | `us-east-1` | ❌ |
| `FLASK_SECRET_KEY` | Flask session secret | - | ✅ |

### LaunchDarkly AI Config Parameters

The application expects an AI Config with these components:

- **`enabled`**: Boolean to enable/disable the chat
- **`model.name`**: AWS Bedrock model ID
- **`model.parameters`**: Model-specific parameters (optional)
- **`provider.name`**: Must be `"bedrock"`
- **`messages`**: Array of system messages

### Supported Bedrock Models

| Model Family | Model ID | Description |
|--------------|----------|-------------|
| Claude 3 | `anthropic.claude-3-haiku-20240307-v1:0` | Fast, cost-effective |
| Claude 3 | `anthropic.claude-3-sonnet-20240229-v1:0` | Balanced performance |
| Llama 3 | `meta.llama3-8b-instruct-v1:0` | Open source option |
| Titan | `amazon.titan-text-lite-v1` | Amazon's model |

## Deployment

### Development
```bash
./start.sh
```

### Production with Docker
```bash
# Using production profile with Nginx
docker-compose --profile production up -d
```

### Production Manual
```bash
# Install production dependencies
pip install gunicorn

# Run with Gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
```

## Troubleshooting

### Common Issues

1. **"LaunchDarkly SDK failed to initialize"**
   - Check your `LAUNCHDARKLY_SDK_KEY`
   - Verify internet connectivity
   - Ensure the SDK key is active

2. **"AWS credentials test failed"**
   - Verify AWS profile configuration: `aws configure list --profile qbe-split-poc`
   - Check AWS region supports Bedrock
   - Ensure proper IAM permissions

3. **"AI Config is disabled"**
   - Check your AI Config in LaunchDarkly dashboard
   - Verify the config key matches `LAUNCHDARKLY_AI_CONFIG_KEY`
   - Ensure the config is enabled for your context

4. **"Bedrock API error"**
   - Verify model ID is correct and available in your region
   - Check AWS Bedrock service quotas
   - Ensure proper IAM permissions for Bedrock

### Debug Mode

To enable detailed logging, set:
```bash
export FLASK_ENV=development
```

### Health Check

The application provides a health endpoint at `/api/health` that returns:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "aws_connected": true,
  "launchdarkly_connected": true
}
```

## API Documentation

### POST `/api/chat`
Send a message to the AI assistant.

**Request:**
```json
{
  "message": "Hello, how are you?"
}
```

**Response:**
```json
{
  "response": "I'm doing well, thank you for asking! How can I help you today?"
}
```

### POST `/api/clear`
Clear the chat history for the current session.

**Response:**
```json
{
  "status": "success"
}
```

### GET `/api/health`
Check the application health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "aws_connected": true,
  "launchdarkly_connected": true
}
```

## Security Considerations

1. **Environment Variables**: Never commit `.env` files to version control
2. **AWS Credentials**: Use IAM roles in production, not access keys
3. **HTTPS**: Use HTTPS in production with proper SSL certificates
4. **Input Validation**: All user input is validated and sanitized
5. **Session Security**: Flask sessions are encrypted with secret key

## Monitoring and Observability

The application integrates with LaunchDarkly's observability features:

- **Custom Metrics**: Track chat interactions and response times
- **Error Tracking**: Automatic error logging and reporting
- **User Context**: Track user interactions for analytics
- **Performance Monitoring**: Monitor API response times and success rates

Access metrics in your LaunchDarkly dashboard under the Observability section.