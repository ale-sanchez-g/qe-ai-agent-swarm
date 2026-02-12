# AI Chat Application

A web-based chat application with LaunchDarkly feature management, AI configuration, and AWS Bedrock integration.

## Features

- **Web UI Chat Interface**: Modern, responsive chat interface built with Flask and Bootstrap
- **LaunchDarkly Integration**: 
  - Feature flags for enabling/disabling chat functionality
  - Dynamic AI model configuration
  - Real-time observability and metrics
- **AWS Bedrock Connection**: Support for various LLM models through AWS Bedrock
- **Knowledge Base Management**: Upload and manage AI assistant knowledge content (admin access required)
- **Feature Flag Access Control**: 
  - `show-debug-config`: Controls visibility of debug configuration features
  - `admin-knowledge-base`: Controls access to knowledge base management page
- **Session Management**: Maintains chat history during user sessions
- **Responsive Design**: Works on desktop and mobile devices

## Setup Instructions

### Prerequisites

- Python 3.9 or higher
- AWS CLI configured with appropriate credentials
- LaunchDarkly SDK key
- Access to AWS Bedrock service

### Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set environment variables:
   ```bash
   export LAUNCHDARKLY_SDK_KEY="your-sdk-key"
   export AWS_PROFILE="your-aws-profile"  # Optional, defaults to default profile
   export AWS_REGION="us-east-1"  # Optional, defaults to us-east-1
   ```

3. Run the application:
   ```bash
   python app.py
   ```

4. Open your browser and navigate to `http://localhost:5000`

## Configuration

### LaunchDarkly AI Config

The application expects an AI Config with the key `chat-ai-config` in your LaunchDarkly project. This config should include:

- **Model Configuration**: Specify the Bedrock model to use
- **System Messages**: Define the AI assistant's behavior
- **Provider Settings**: Configure Bedrock-specific parameters

### AWS Credentials

Ensure your AWS credentials are properly configured and have access to Amazon Bedrock. The application will test credentials on startup.

### Feature Flags

The application uses LaunchDarkly feature flags to control access to various features:

#### `show-debug-config` (Boolean)
- **Purpose**: Controls visibility of debug configuration features
- **Default**: `false` (debug features hidden)
- **When enabled**: Shows debug buttons in settings menu for troubleshooting
- **Documentation**: See `DEBUG_FEATURE_FLAG.md`

#### `admin-knowledge-base` (Boolean)  
- **Purpose**: Controls access to knowledge base management page
- **Default**: `false` (knowledge admin restricted)
- **When enabled**: Shows "Knowledge Base Admin" links and grants access to `/admin/knowledge`
- **Security**: Unauthorized access attempts are logged
- **Documentation**: See `ADMIN_KNOWLEDGE_BASE_FEATURE_FLAG.md`

**Targeting Examples**:
```javascript
// Admin users only
IF user.key in ["admin", "knowledge-manager"]
THEN serve true

// Role-based access  
IF user.role = "admin" OR user.team = "ai-operations"
THEN serve true
```

## Usage

1. Open the web application in your browser
2. Start typing messages in the chat interface
3. The AI will respond based on your LaunchDarkly configuration
4. Use LaunchDarkly's dashboard to modify AI behavior in real-time

## Architecture

```
chat-app/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── static/            # CSS, JS, and other static files
│   ├── css/
│   ├── js/
│   └── img/
└── templates/         # HTML templates
    └── index.html     # Main chat interface
```