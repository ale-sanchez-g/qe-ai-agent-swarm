# Test Process

## VSCode Configuration
1. Install the Playwright extension for VSCode.
2. Select the desire *.spec.md prompt
3. Select `Agent` and `Claude Sonnet 4` for best performance
 

## Prompt

```
Execute 100% of the test cases from the prompt using the playwright MCP. 

- Ensure you can work with the playwright MCP and do not install playwright
- Do not start the application as it is already running
- Refer to the Application URL on the prompt 
- Capture Screenshots and test evidence in the chat-app/test/{timestamp} folder
- Save report with a date stamp on the file name

Log in with 4 different customers

jamesbond - no access
asanchez - AI access 1
llamauser - AI access 2
testuser - AI access 3

You can test the AI based on the replies on the messages
```