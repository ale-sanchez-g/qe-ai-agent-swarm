import uuid
import logging
import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
import boto3
import ldclient
from ldclient import Context
from ldclient.config import Config
from ldai.client import LDAIClient, AIConfig, ModelConfig, ProviderConfig, LDMessage
from ldobserve import ObservabilityConfig, ObservabilityPlugin, observe
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-change-this')

# Configuration
AWS_PROFILE = os.getenv('AWS_PROFILE', 'qbe-split-poc')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
LAUNCHDARKLY_SDK_KEY = os.getenv('LAUNCHDARKLY_SDK_KEY')
AI_CONFIG_KEY = os.getenv('LAUNCHDARKLY_AI_CONFIG_KEY', 'chat-ai-config')

# Global variables
bedrock_client = None
aiclient = None

def initialize_aws():
    """Initialize AWS Bedrock client with proper credentials"""
    global bedrock_client
    
    try:
        # Create session with specified profile and region
        aws_session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
        bedrock_client = aws_session.client("bedrock-runtime", region_name=AWS_REGION)
        
        # Test credentials
        sts_client = aws_session.client('sts', region_name=AWS_REGION)
        identity = sts_client.get_caller_identity()
        
        print(f"✅ AWS credentials valid. Account: {identity.get('Account')}")
        return True
        
    except Exception as e:
        print(f"❌ AWS credentials test failed: {e}")
        print(f"❌ Please check your AWS credentials for profile: {AWS_PROFILE}")
        return False

def initialize_launchdarkly():
    """Initialize LaunchDarkly SDK with observability"""
    global aiclient
    
    if not LAUNCHDARKLY_SDK_KEY:
        print("❌ Please set the LAUNCHDARKLY_SDK_KEY environment variable")
        return False
    
    try:
        # Configure LaunchDarkly with observability plugin
        ldclient.set_config(Config(
            LAUNCHDARKLY_SDK_KEY,
            plugins=[
                ObservabilityPlugin(
                    ObservabilityConfig(
                        service_name="chat-ai-app",
                        service_version="1.0.1"
                    )
                )
            ]
        ))
        
        if not ldclient.get().is_initialized():
            print("❌ LaunchDarkly SDK failed to initialize")
            return False
        
        aiclient = LDAIClient(ldclient.get())
        print("✅ LaunchDarkly SDK successfully initialized")
        return True
        
    except Exception as e:
        print(f"❌ LaunchDarkly initialization failed: {e}")
        return False

def get_user_context():
    """Create a user context for LaunchDarkly evaluation"""
    # Use session ID as user key for consistency
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    
    return (
        Context
        .builder(session['user_id'])
        .kind('user')
        .name(f"chat-user-{session['user_id'][:8]}")
        .build()
    )

def get_ai_config(user_message):
    """Get AI configuration from LaunchDarkly"""
    context = get_user_context()
    
    # Default fallback configuration
    default_config = AIConfig(
        enabled=True,
        model=ModelConfig(name='anthropic.claude-3-haiku-20240307-v1:0', parameters={}),
        provider=ProviderConfig(name='bedrock'),
        messages=[LDMessage(
            role='system', 
            content='You are a helpful AI assistant. Be concise and friendly in your responses.'
        )],
    )
    
    try:
        print(f"🔍 Evaluating AI Config: {AI_CONFIG_KEY}")
        print(f"🔍 User context: {context.key}")
        
        config_value, tracker = aiclient.config(
            AI_CONFIG_KEY,
            context,
            default_config,
            {'userMessage': user_message}
        )
        
        print(f"🔍 AI Config enabled: {config_value.enabled}")
        
        if config_value.enabled:
            print(f"🔍 AI Config model: {config_value.model.name if config_value.model else 'None'}")
            print(f"🔍 AI Config provider: {config_value.provider.name if config_value.provider else 'None'}")
        else:
            print("🔍 AI Config is disabled - model and provider not available")
        
        return config_value, tracker
        
    except Exception as e:
        print(f"❌ Error getting AI config: {e}")
        observe.record_log(f"Error getting AI config: {e}", logging.ERROR)
        return default_config, None

@app.route('/')
def index():
    """Render the main chat interface"""
    # Initialize session chat history if not exists
    if 'chat_history' not in session:
        session['chat_history'] = []
    
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Get session trace ID for observability
        session_trace_id = session.get('trace_id', str(uuid.uuid4()))
        session['trace_id'] = session_trace_id
        
        # Log user input
        observe.record_log(
            f"User message received: {user_message}", 
            logging.INFO, 
            {"customID": session_trace_id}
        )
        
        # Get AI configuration from LaunchDarkly
        config_value, tracker = get_ai_config(user_message)
        
        if not config_value.enabled:
            observe.record_log(
                "AI Config is disabled", 
                logging.INFO, 
                {"customID": session_trace_id}
            )
            return jsonify({'response': 'AI chat is currently disabled. Please try again later.'})
        
        # Prepare messages for the API call
        messages = []
        system_messages = []
        
        # Add conversation history (last 10 messages to avoid token limit)
        chat_history = session.get('chat_history', [])[-10:]
        for msg in chat_history:
            messages.append({
                'role': 'user' if msg['type'] == 'user' else 'assistant',
                'content': [{'text': msg['content']}]
            })
        
        # Add current user message
        messages.append({
            'role': 'user',
            'content': [{'text': user_message}]
        })
        
        # Separate system messages
        for msg in config_value.messages:
            if msg.role == 'system':
                system_messages.append({'text': msg.content})
        
        # Add enhanced system message for better formatting
        enhanced_system_prompt = """You are a helpful and professional AI assistant. When responding:

1. Use clear, well-structured formatting with proper paragraphs
2. Use markdown-style formatting when appropriate:
   - **Bold** for emphasis
   - *Italic* for subtle emphasis  
   - `code` for technical terms, commands, or short code snippets
   - ```code blocks``` for longer code examples
   - Use bullet points (- or *) for lists
   - Use numbered lists (1. 2. 3.) when order matters
3. Break up long responses into digestible sections
4. Use headers (## Header) to organize complex topics
5. Be conversational but professional
6. Provide examples when explaining concepts
7. End responses with a brief summary or next steps when relevant

Always prioritize clarity and readability in your responses."""
        
        system_messages.append({'text': enhanced_system_prompt})
        
        # Call Bedrock API
        try:
            converse_params = {
                'modelId': config_value.model.name,
                'messages': messages
            }
            
            if system_messages:
                converse_params['system'] = system_messages
            
            if tracker:
                response = tracker.track_bedrock_converse_metrics(
                    bedrock_client.converse(**converse_params)
                )
            else:
                response = bedrock_client.converse(**converse_params)
            
            ai_response = response['output']['message']['content'][0]['text']
            
            # Update chat history
            if 'chat_history' not in session:
                session['chat_history'] = []
            
            session['chat_history'].append({
                'type': 'user',
                'content': user_message,
                'timestamp': datetime.now().isoformat()
            })
            
            session['chat_history'].append({
                'type': 'assistant',
                'content': ai_response,
                'timestamp': datetime.now().isoformat()
            })
            
            # Log successful response
            observe.record_log(
                f"AI response generated successfully", 
                logging.INFO, 
                {
                    "customID": session_trace_id,
                    "model": config_value.model.name,
                    "response_length": len(ai_response)
                }
            )
            
            return jsonify({'response': ai_response})
            
        except Exception as e:
            if tracker:
                tracker.track_error()
            
            observe.record_log(
                f"Bedrock API error: {e}", 
                logging.ERROR, 
                {"customID": session_trace_id}
            )
            
            return jsonify({'error': 'Failed to generate response. Please try again.'}), 500
            
    except Exception as e:
        observe.record_log(f"Chat endpoint error: {e}", logging.ERROR)
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/api/clear', methods=['POST'])
def clear_chat():
    """Clear chat history"""
    session['chat_history'] = []
    return jsonify({'status': 'success'})

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'aws_connected': bedrock_client is not None,
        'launchdarkly_connected': aiclient is not None
    })

@app.route('/api/debug', methods=['GET'])
def debug_config():
    """Debug endpoint to check LaunchDarkly config"""
    try:
        context = get_user_context()
        
        # Try to get the AI config
        default_config = AIConfig(
            enabled=True,
            model=ModelConfig(name='anthropic.claude-3-haiku-20240307-v1:0', parameters={}),
            provider=ProviderConfig(name='bedrock'),
            messages=[LDMessage(
                role='system', 
                content='You are a helpful AI assistant. Be concise and friendly in your responses.'
            )],
        )
        
        config_value, tracker = aiclient.config(
            AI_CONFIG_KEY,
            context,
            default_config,
            {}
        )
        
        return jsonify({
            'ai_config_key': AI_CONFIG_KEY,
            'user_context': {
                'key': context.key,
                'name': context.name,
                'kind': context.kind
            },
            'config_enabled': config_value.enabled,
            'config_model': config_value.model.name if config_value.model else None,
            'config_provider': config_value.provider.name if config_value.provider else None,
            'using_fallback': config_value == default_config,
            'sdk_initialized': ldclient.get().is_initialized(),
            'environment_vars': {
                'LAUNCHDARKLY_SDK_KEY': LAUNCHDARKLY_SDK_KEY[:10] + '...' if LAUNCHDARKLY_SDK_KEY else None,
                'LAUNCHDARKLY_AI_CONFIG_KEY': AI_CONFIG_KEY
            }
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'ai_config_key': AI_CONFIG_KEY,
            'sdk_initialized': ldclient.get().is_initialized() if ldclient.get() else False
        }), 500

if __name__ == '__main__':
    print("🚀 Starting AI Chat Application...")
    
    # Initialize services
    aws_ok = initialize_aws()
    ld_ok = initialize_launchdarkly()
    
    if not aws_ok or not ld_ok:
        print("❌ Failed to initialize required services. Exiting.")
        exit(1)
    
    print("✅ All services initialized successfully!")
    print(f"🌐 Starting server on http://localhost:5001")
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5001)