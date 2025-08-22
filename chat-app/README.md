# AI Chat Application

A web-based chat application with LaunchDarkly feature management, AI configuration, and AWS Bedrock integration.

## Features

- **Web UI Chat Interface**: Modern, responsive chat interface built with Flask and Bootstrap
- **LaunchDarkly Integration**: 
  - Feature flags for enabling/disabling chat functionality
  - Dynamic AI model configuration
  - Real-time observability and metrics
- **AWS Bedrock Connection**: Support for various LLM models through AWS Bedrock
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