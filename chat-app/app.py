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
import platform
import json
import re

# Import knowledge base modules
from knowledge_api import knowledge_bp
from product_knowledge import get_knowledge_base, format_knowledge_for_chat

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-change-this')

# Register knowledge management blueprint
app.register_blueprint(knowledge_bp)

# Configuration
AWS_PROFILE = os.getenv('AWS_PROFILE', 'qbe-split-poc')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
LAUNCHDARKLY_SDK_KEY = os.getenv('LAUNCHDARKLY_SDK_KEY')
AI_CONFIG_KEY = os.getenv('LAUNCHDARKLY_AI_CONFIG_KEY', 'chat-ai-config')

# Feature flags used in this application:
# - show-debug-config: Boolean flag to control visibility of debug configuration button

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
                        service_version="1.1.0"
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
    """Create a user context for LaunchDarkly evaluation with user ID and browser details"""
    # Check if user is authenticated
    if 'authenticated' not in session or not session['authenticated']:
        return None
    
    user_id = session.get('user_id')
    browser_details = session.get('browser_details', {})
    
    # Create context builder with user ID
    context_builder = (
        Context
        .builder(user_id)
        .kind('user')
        .name(f"chat-user-{user_id}")
    )
    
    # Add browser details as custom attributes
    if browser_details:
        # Add browser information
        if 'userAgent' in browser_details:
            context_builder.set('userAgent', browser_details['userAgent'])
        if 'platform' in browser_details:
            context_builder.set('platform', browser_details['platform'])
        if 'language' in browser_details:
            context_builder.set('language', browser_details['language'])
        if 'screenResolution' in browser_details:
            context_builder.set('screenResolution', browser_details['screenResolution'])
        if 'timezone' in browser_details:
            context_builder.set('timezone', browser_details['timezone'])
        if 'viewport' in browser_details:
            context_builder.set('viewport', browser_details['viewport'])
        if 'deviceType' in browser_details:
            context_builder.set('deviceType', browser_details['deviceType'])
        if 'browserName' in browser_details:
            context_builder.set('browserName', browser_details['browserName'])
        if 'browserVersion' in browser_details:
            context_builder.set('browserVersion', browser_details['browserVersion'])
    
    # Add session metadata
    context_builder.set('sessionStart', session.get('session_start', datetime.now().isoformat()))
    context_builder.set('serverPlatform', platform.system())
    
    return context_builder.build()

def get_feature_flags():
    """Get feature flags from LaunchDarkly for the current user"""
    context = get_user_context()
    
    if not context or not ldclient.get().is_initialized():
        return {
            'show_debug_config': False  # Default to hiding debug config
        }
    
    try:
        # Evaluate feature flags
        show_debug_config = ldclient.get().variation('show-debug-config', context, False)
        
        return {
            'show_debug_config': show_debug_config
        }
    except Exception as e:
        print(f"❌ Error evaluating feature flags: {e}")
        observe.record_log(f"Error evaluating feature flags: {e}", logging.ERROR)
        return {
            'show_debug_config': False  # Default to hiding debug config on error
        }

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
    """Render the main chat interface or login page"""
    # Check if user is authenticated
    if 'authenticated' not in session or not session['authenticated']:
        return render_template('login.html')
    
    # Initialize session chat history if not exists
    if 'chat_history' not in session:
        session['chat_history'] = []
    
    # Get feature flags for the current user
    feature_flags = get_feature_flags()
    
    return render_template('index.html', 
                         user_id=session.get('user_id', 'Unknown'),
                         feature_flags=feature_flags)

@app.route('/api/login', methods=['POST'])
def login():
    """Handle user login with user ID and browser details"""
    try:
        data = request.get_json()
        user_id = data.get('userId', '').strip()
        browser_details = data.get('browserDetails', {})
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        # Validate user ID format (alphanumeric, dashes, underscores allowed)
        if not re.match(r'^[a-zA-Z0-9_-]+$', user_id):
            return jsonify({'error': 'User ID can only contain letters, numbers, dashes, and underscores'}), 400
        
        if len(user_id) < 2 or len(user_id) > 50:
            return jsonify({'error': 'User ID must be between 2 and 50 characters'}), 400
        
        # Set session data
        session['authenticated'] = True
        session['user_id'] = user_id
        session['browser_details'] = browser_details
        session['session_start'] = datetime.now().isoformat()
        session['chat_history'] = []  # Reset chat history for new user
        
        # Log successful login
        observe.record_log(
            f"User logged in: {user_id}", 
            logging.INFO, 
            {
                "user_id": user_id,
                "browser": browser_details.get('browserName', 'Unknown'),
                "platform": browser_details.get('platform', 'Unknown')
            }
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Login successful',
            'userId': user_id
        })
        
    except Exception as e:
        observe.record_log(f"Login error: {e}", logging.ERROR)
        return jsonify({'error': 'Login failed. Please try again.'}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """Handle user logout"""
    try:
        user_id = session.get('user_id', 'Unknown')
        
        # Log logout
        observe.record_log(
            f"User logged out: {user_id}", 
            logging.INFO, 
            {"user_id": user_id}
        )
        
        # Clear session
        session.clear()
        
        return jsonify({'status': 'success', 'message': 'Logout successful'})
        
    except Exception as e:
        observe.record_log(f"Logout error: {e}", logging.ERROR)
        return jsonify({'error': 'Logout failed'}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        # Check authentication
        if 'authenticated' not in session or not session['authenticated']:
            return jsonify({'error': 'Authentication required. Please login first.'}), 401
        
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Get session trace ID for observability
        session_trace_id = session.get('trace_id', str(uuid.uuid4()))
        session['trace_id'] = session_trace_id
        
        # Log user input with enhanced context
        observe.record_log(
            f"User message received: {user_message}", 
            logging.INFO, 
            {
                "customID": session_trace_id,
                "user_id": session.get('user_id'),
                "browser": session.get('browser_details', {}).get('browserName', 'Unknown'),
                "platform": session.get('browser_details', {}).get('platform', 'Unknown')
            }
        )
        
        # Get AI configuration from LaunchDarkly
        config_value, tracker = get_ai_config(user_message)
        
        if not config_value.enabled:
            observe.record_log(
                "AI Config is disabled", 
                logging.INFO, 
                {"customID": session_trace_id, "user_id": session.get('user_id')}
            )
            return jsonify({'response': 'FinBot is not available for you at this time. Send us your question at help@devops1.com.au and one of our financial experts will get back to you shortly.'})
        # Search knowledge base for relevant product information
        knowledge_context = ""
        try:
            kb = get_knowledge_base()
            search_results = kb.search_knowledge(
                query=user_message,
                max_results=3,
                min_similarity=0.2  # Lowered threshold for better results
            )
            
            if search_results:
                knowledge_context = format_knowledge_for_chat(search_results, max_context_length=1500)
                observe.record_log(
                    f"Found {len(search_results)} relevant knowledge documents", 
                    logging.INFO, 
                    {
                        "customID": session_trace_id,
                        "user_id": session.get('user_id'),
                        "knowledge_results": len(search_results)
                    }
                )
        except Exception as e:
            observe.record_log(
                f"Knowledge base search failed: {str(e)}", 
                logging.WARNING, 
                {"customID": session_trace_id, "user_id": session.get('user_id')}
            )
        
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
        
        # Log knowledge retrieval
        observe.record_log(
            f"Knowledge context retrieved: {knowledge_context}",
            logging.INFO,
            {"customID": session_trace_id, "user_id": session.get('user_id')}
        )

        context_prompt = f"""You are a helpful and professional AI assistant specialising in financial services and loan products. 

{knowledge_context}
"""
        observe.record_log(
            f"Context prompt created: {context_prompt}",
            logging.INFO,
            {"customID": session_trace_id, "user_id": session.get('user_id')}
        )
        system_messages.append({'text': context_prompt})
        
        # Call Bedrock API
        try:
            converse_params = {
                'modelId': config_value.model.name,
                'messages': messages,
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
                    "user_id": session.get('user_id'),
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
                {"customID": session_trace_id, "user_id": session.get('user_id')}
            )
            
            return jsonify({'error': 'Failed to generate response. Please try again.'}), 500
            
    except Exception as e:
        observe.record_log(f"Chat endpoint error: {e}", logging.ERROR)
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/api/clear', methods=['POST'])
def clear_chat():
    """Clear chat history"""
    # Check authentication
    if 'authenticated' not in session or not session['authenticated']:
        return jsonify({'error': 'Authentication required'}), 401
        
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

@app.route('/admin/knowledge')
def knowledge_admin():
    """Render the knowledge base management interface"""
    # Check if user is authenticated
    if 'authenticated' not in session or not session['authenticated']:
        return render_template('login.html')
    
    return render_template('knowledge_admin.html', 
                         user_id=session.get('user_id', 'Unknown'))

@app.route('/api/debug', methods=['GET'])
def debug_config():
    """Debug endpoint to check LaunchDarkly config"""
    try:
        # Check authentication
        if 'authenticated' not in session or not session['authenticated']:
            return jsonify({'error': 'Authentication required'}), 401
            
        context = get_user_context()
        
        if not context:
            return jsonify({'error': 'Invalid user context'}), 400
        
        # Get feature flags
        feature_flags = get_feature_flags()
        
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
        
        # Extract context attributes safely
        context_attributes = {}
        browser_details = session.get('browser_details', {})
        
        # Since we know how we built the context, let's recreate the attributes view
        # by getting them from the session data that was used to build the context
        context_attributes.update(browser_details)
        context_attributes['sessionStart'] = session.get('session_start', 'Unknown')
        context_attributes['serverPlatform'] = platform.system()
        
        return jsonify({
            'ai_config_key': AI_CONFIG_KEY,
            'user_context': {
                'key': context.key,
                'name': context.name,
                'kind': context.kind,
                'attributes': context_attributes
            },
            'config_enabled': config_value.enabled,
            'config_model': config_value.model.name if config_value.model else None,
            'config_provider': config_value.provider.name if config_value.provider else None,
            'using_fallback': config_value == default_config,
            'sdk_initialized': ldclient.get().is_initialized(),
            'feature_flags': feature_flags,
            'session_info': {
                'user_id': session.get('user_id'),
                'browser_details': session.get('browser_details', {}),
                'session_start': session.get('session_start')
            },
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