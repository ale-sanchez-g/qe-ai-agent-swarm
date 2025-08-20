import uuid
import logging
import os
import random
import ldclient
from ldclient import Context
from ldclient.config import Config
from ldai.client import LDAIClient, AIConfig, ModelConfig, ProviderConfig, LDMessage
from ldobserve import ObservabilityConfig, ObservabilityPlugin, observe
import boto3

# Generate a session trace ID
SESSION_TRACE_ID = str(uuid.uuid4())

# Use a specific profile or session with proper credentials
# Note: Make sure the region supports Bedrock - using us-east-1 where Bedrock is available
session = boto3.Session(profile_name='qbe-split-poc', region_name='us-east-1')
client = session.client("bedrock-runtime", region_name="us-east-1")

# Test AWS credentials before proceeding
try:
    # Test with STS to verify credentials work
    sts_client = session.client('sts', region_name='us-east-1')
    identity = sts_client.get_caller_identity()
    print(f"--- AWS credentials valid. Account: {identity.get('Account')}, User: {identity.get('Arn')}")
except Exception as e:
    print(f"--- AWS credentials test failed: {e}")
    print("--- Please check your AWS credentials in the qbe-split-poc profile")
    exit(1)

# Set sdk_key to your LaunchDarkly SDK key.
sdk_key = os.getenv('LAUNCHDARKLY_SDK_KEY')

# Set config_key to the AI Config key you want to evaluate.
ai_config_key = 'ld-demo'

def main():


    print("--- Initializing LaunchDarkly SDK...")
    if not sdk_key:
        print("--- Please set the LAUNCHDARKLY_SDK_KEY env first")
        exit()
    if not ai_config_key:
        print("--- Please set the LAUNCHDARKLY_AI_CONFIG_KEY env first")
        exit()

    ldclient.set_config(Config(
    sdk_key,
    plugins=[
        ObservabilityPlugin(
            ObservabilityConfig(
                service_name="demo-ai-app",
                service_version="1.0.1"
            )
        )
    ]
))

    if not ldclient.get().is_initialized():
        print("--- SDK failed to initialize. Please check your internet connection and SDK credential for any typo.")
        exit()

    aiclient = LDAIClient(ldclient.get())
    # print(f"--- SDK successfully initialized : {ai_config_key}")
    observe.record_log(f"--- SDK successfully initialized", logging.INFO, {"customID": SESSION_TRACE_ID})


    # Set up the evaluation context. This context should appear on your
    # create a random user context in the LaunchDarkly contexts dashboard soon after you run the demo.
    # random string based on random 20 array
    array = ["user-1", "user-2", "user-3", "user-4", "user-5", "user-6", "user-7", "user-8", "user-9", "user-10",
             "user-11", "user-12", "user-13", "user-14", "user-15", "user-16", "user-17", "user-18", "user-19", "user-20"]
    random_string = random.choice(array)
    # print(f"--- Using random user context: {random_string} : SDK {sdk_key}")
    context = (
        Context
        .builder(f"user-key-{random_string}")
        .kind('user')
        .name(random_string)
        .build()
    )

    DEFAULT_SYSTEM_MESSAGE = "As an AI bot you MUST ONLY respond with 'OUT OF OFFICE'."

    # Set a fallback AIConfig to use if a config is not found or your application is not able to connect to LaunchDarkly.
    # Using a valid Bedrock model ID - Claude 3 Haiku (common and cost-effective)
    # Alternative models you can try:
    # - anthropic.claude-3-haiku-20240307-v1:0 (more capable but more expensive)
    # - meta.llama3-8b-instruct-v1:0 (Meta example)
    # - amazon.titan-text-lite-v1 (Amazon's model - ERROR simulation)
    default_value = AIConfig(
        enabled=True,
        model=ModelConfig(name='meta.llama3-8b-instruct-v1:0', parameters={}),
        provider=ProviderConfig(name='bedrock'),
        messages=[LDMessage(role='system', content=DEFAULT_SYSTEM_MESSAGE)],
    )

    # Optionally, you can use a disabled AIConfig
    # default_value = AIConfig(
    #     enabled=False
    # )

    config_value, tracker = aiclient.config(
        ai_config_key,
        context,
        default_value,
        {'myUserVariable': "Testing Variable"}
    )

    if not config_value.enabled:
        observe.record_log(f"--- AI Config is disabled", logging.INFO, {"customID": SESSION_TRACE_ID})
        return

    observe.record_log(f"--- AI Prompts: {config_value.messages[0].content}", logging.INFO, {"customID": SESSION_TRACE_ID})

    # Add the user input to the conversation
    USER_INPUT = "What can you help me with?"
    observe.record_log(f"--- User Input: {USER_INPUT}", logging.INFO, {"customID": SESSION_TRACE_ID})

    # Add user message to the config messages
    config_value.messages.append(LDMessage(role='user', content=USER_INPUT))

    observe.record_log(f"--- Using model: {config_value.model.name}", logging.INFO, {"customID": SESSION_TRACE_ID})
    observe.record_log(f"--- Total messages: {len(config_value.messages)}", logging.INFO, {"customID": SESSION_TRACE_ID})

    # Print all messages for debugging
    for i, msg in enumerate(config_value.messages):
        observe.record_log(f"--- Message {i}: {msg.role} - {msg.content}", logging.INFO, {"customID": SESSION_TRACE_ID})

    try:
        # Use LD's approach - pass the messages directly to the tracker
        converse = tracker.track_bedrock_converse_metrics(
            client.converse(
                modelId=config_value.model.name,
                messages=[{'role': msg.role, 'content': [{'text': msg.content}]} for msg in config_value.messages if msg.role != 'system'],
                system=[{'text': msg.content} for msg in config_value.messages if msg.role == 'system'],
            )
        )
        # Append the AI response to the conversation history
        observe.record_log(f"--- AI Response: {converse['output']['message']['content'][0]['text']}", logging.INFO, {"customID": SESSION_TRACE_ID})
        observe.record_log(f"--- AI Configuration", logging.INFO, {
            "customID": SESSION_TRACE_ID,
            "model": config_value.model.name,
            "provider": config_value.provider.name,
            "messages": [msg.content for msg in config_value.messages]
            })
    
    except Exception as e:
        tracker.track_error()
        observe.record_log(f"--- Error calling Bedrock: {e}", logging.ERROR, {"customID": SESSION_TRACE_ID})
        # print(f"--- Error calling Bedrock: {e}")
        # print(f"--- Model ID used: {config_value.model.name}")        
        # raise


    # Continue the conversation by adding user input to the messages list and invoking the LLM again.
    print("Success.")

    # Close the client to flush events and close the connection.
    ldclient.get().close()