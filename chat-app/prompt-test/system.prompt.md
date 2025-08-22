# Test Process

## VSCode Configuration
1. Install the Playwright extension for VSCode.
2. Select the desire *.spec.md prompt
3. Select `Agent` and `Claude Sonnet 4` for best performance
 

## Prompt

```
Execute all the test cases from the prompt using the playwright MCP. 

- Ensure you can work with the playwright MCP and do not install playwright
- Do not start the application as it is already running
- Refer to the Application URL on the prompt 
- Capture Screenshots and test evidence in the planner/test/{timestamp} folder
- Save report with a date stamp on the file name
```