# Debug Configuration Feature Flag

## Overview
The debug configuration button in the chat application can now be hidden/shown using a LaunchDarkly feature flag. This allows for controlled access to debugging functionality.

## Feature Flag Details

### Flag Key
`show-debug-config`

### Flag Type
Boolean

### Default Value
`false` (debug configuration button is hidden by default)

### Implementation

#### Backend (Flask)
- **Function**: `get_feature_flags()` in `app.py`
- **Route**: Both desktop and mobile debug buttons are controlled by this flag
- **Evaluation**: Flag is evaluated using the current user's LaunchDarkly context

#### Frontend (HTML)
- **Desktop**: Debug button in the settings dropdown menu
- **Mobile**: Debug button in the mobile offcanvas menu
- **Conditional Rendering**: Uses Jinja2 template conditionals to show/hide buttons

#### JavaScript
- **Safety**: Gracefully handles missing debug buttons when flag is disabled
- **Debug Info**: Shows feature flag status in debug configuration output

## Usage

### Setting up the Feature Flag in LaunchDarkly

1. **Create the Flag**:
   - Go to your LaunchDarkly dashboard
   - Create a new boolean feature flag with key: `show-debug-config`
   - Set the default value to `false`

2. **Configure Targeting**:
   ```json
   {
     "key": "show-debug-config",
     "name": "Show Debug Configuration Button",
     "description": "Controls visibility of the debug configuration button in the chat application",
     "kind": "boolean",
     "variations": [
       { "value": false, "name": "Hidden" },
       { "value": true, "name": "Visible" }
     ]
   }
   ```

3. **Targeting Rules Examples**:
   - **Show for specific users**: Target by user ID
   - **Show for admins**: Target by user attributes (e.g., role)
   - **Show for internal testing**: Target by platform or browser
   - **Show for development environments**: Target by environment context

### Testing the Feature Flag

#### When Flag is `false` (default):
- Debug configuration button is not visible in desktop dropdown
- Debug configuration button is not visible in mobile menu
- JavaScript safely handles missing elements
- Debug API endpoint still works if accessed directly

#### When Flag is `true`:
- Debug configuration button appears in both desktop and mobile interfaces
- Clicking the button shows comprehensive debug information
- Feature flag status is included in debug output

### Verification

1. **Check Flag Status**: Use the debug configuration endpoint to verify flag evaluation
2. **UI Testing**: Test both desktop and mobile interfaces
3. **Graceful Degradation**: Ensure application works when buttons are hidden

## Benefits

1. **Security**: Hide debugging features from end users
2. **Controlled Access**: Enable debug features only for specific users/groups
3. **Environment-Specific**: Different visibility rules for dev/staging/prod
4. **Real-time Control**: Toggle visibility without code deployment
5. **User Context**: Flag evaluation based on user attributes and session data

## Example Targeting Scenarios

### Scenario 1: Internal Users Only
```
IF user.userAgent contains "Chrome" AND user.platform = "MacOS"
THEN serve true
ELSE serve false
```

### Scenario 2: Specific User IDs
```
IF user.key in ["admin", "developer", "support"]
THEN serve true
ELSE serve false
```

### Scenario 3: Development Mode
```
IF user.sessionStart contains "dev" OR user.browserName = "Firefox"
THEN serve true
ELSE serve false
```

## Monitoring

The feature flag evaluation is logged and can be monitored through:
- LaunchDarkly dashboard analytics
- Application logs with observability integration
- Debug configuration endpoint responses

## Related Files

- `app.py`: Backend feature flag evaluation
- `templates/index.html`: Conditional UI rendering
- `static/js/chat.js`: Safe JavaScript handling
- This documentation: `DEBUG_FEATURE_FLAG.md`