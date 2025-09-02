# AI Chat Assistant - Playwright Test Suite

A comprehensive Playwright test suite for the AI Chat Assistant application, featuring Page Object Model architecture, CI/CD integration, and extensive test coverage.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- npm or yarn
- AI Chat Assistant application running on `http://localhost:5001`

### Installation
```bash
cd chat-app/playwright-tests
npm install
npx playwright install
```

### Running Tests
```bash
# Run all tests
npm test

# Run tests with UI mode
npm run test:ui

# Run smoke tests only
npm run test:smoke

# Run specific browser
npm run test:chromium

# Run mobile tests
npm run test:mobile

# Generate and view reports
npm run report
```

## 📁 Project Structure

```
playwright-tests/
├── pages/                 # Page Object Models
│   ├── BasePage.ts       # Base page class with common functionality
│   ├── LoginPage.ts      # Login page interactions
│   └── ChatPage.ts       # Chat interface interactions
├── tests/                # Test specifications
│   ├── auth.spec.ts      # Authentication tests
│   ├── chat.spec.ts      # Chat functionality tests  
│   ├── ui-components.spec.ts # UI component tests
│   ├── responsive.spec.ts    # Responsive design tests
│   └── accessibility.spec.ts # Accessibility tests
├── utils/                # Utilities and helpers
│   ├── TestData.ts       # Test data constants
│   └── TestHelpers.ts    # Helper functions
├── playwright.config.js  # Playwright configuration
└── package.json         # Dependencies and scripts
```

## 🧪 Test Suites

### 1. Authentication Tests (`@auth`)
- **TC_001**: Valid User Login
- **TC_002**: Invalid User ID Format  
- **TC_003**: Empty User ID Validation
- **TC_004**: User ID Length Validation
- **TC_005**: Browser Context Collection
- **TC_006**: Logout Functionality

### 2. Chat Functionality Tests (`@chat`)
- **TC_010**: Valid Chat Message
- **TC_012**: Empty Chat Message Validation
- **TC_014**: Long Message Processing
- **TC_015**: Clear Chat History
- **TC_031**: Enhanced Message Formatting
- Security tests (XSS prevention)
- Emoji and special character handling

### 3. UI Components Tests (`@ui`)
- **TC_019**: Login Page Display
- **TC_020**: Login Form Validation
- **TC_022**: Chat Header Display
- **TC_023**: Enhanced Settings Dropdown
- **TC_024**: Enhanced Typing Indicator
- **TC_026**: Login to Chat Transition
- **TC_027**: Logout Flow UI
- **TC_030**: Debug Information Display
- Performance and image loading tests

### 4. Responsive Design Tests (`@responsive`)
- **TC_033**: Mobile Device Display
- **TC_034**: Tablet Display Optimization
- **TC_035**: Desktop Browser Scaling
- Mobile landscape orientation
- Browser zoom testing
- Touch interactions
- Scrolling behavior
- CSS responsive features

### 5. Accessibility Tests (`@accessibility`)
- **TC_062**: Keyboard Navigation
- **TC_063**: Screen Reader Compatibility
- **TC_064**: Color and Contrast Accessibility
- Focus management
- Skip links and navigation
- Landmark navigation
- Keyboard shortcuts
- Voice control simulation
- Reduced motion support

## 🏷️ Test Tags

Tests are tagged for easy filtering:

- `@smoke` - Critical functionality tests
- `@regression` - Full regression test suite  
- `@auth` - Authentication-related tests
- `@chat` - Chat functionality tests
- `@ui` - User interface tests
- `@responsive` - Responsive design tests
- `@accessibility` - Accessibility compliance tests

## 🛠️ Page Object Model

The test suite uses the Page Object Model pattern for maintainable and reusable test code:

### BasePage
Common functionality shared across all pages:
- Navigation and waiting
- Screenshot capture
- Element interactions
- Error handling

### LoginPage
Login page specific actions:
- User ID validation
- Browser context verification
- Form submission
- Validation message handling

### ChatPage  
Chat interface specific actions:
- Message sending/receiving
- Settings dropdown
- Chat history management
- Health check verification

## 🎯 CI/CD Integration

### GitHub Actions Workflow

The test suite includes a comprehensive GitHub Actions workflow (`.github/workflows/playwright.yml`):

- **Multi-browser testing**: Chromium, Firefox, WebKit
- **Mobile testing**: Chrome Mobile, Safari Mobile  
- **Accessibility testing**: WCAG compliance checks
- **Scheduled runs**: Daily regression tests
- **Manual triggers**: On-demand test execution
- **Artifact collection**: Reports, screenshots, videos

### Running in CI/CD

```yaml
# Trigger smoke tests
npm run test:smoke

# Trigger regression tests  
npm run test:regression

# Trigger specific test categories
npm run test:auth
npm run test:chat
npm run test:ui
```

## 📊 Test Reporting

### HTML Reports
Comprehensive HTML reports with:
- Test execution timeline
- Screenshots on failure
- Video recordings
- Trace files for debugging

### JUnit Reports
XML reports for CI/CD integration:
- Test results summary
- Failure details
- Execution times
- Trend analysis

### Custom Reporting
- Screenshot evidence collection
- Performance metrics
- Accessibility compliance scores
- Browser compatibility matrix

## 🔧 Configuration

### Browser Configuration
```javascript
// playwright.config.js
projects: [
  { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
  { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  { name: 'Mobile Chrome', use: { ...devices['Pixel 5'] } },
  { name: 'Mobile Safari', use: { ...devices['iPhone 12'] } }
]
```

### Test Data Management
Centralized test data in `utils/TestData.ts`:
- User credentials
- Test messages
- Validation messages
- Browser viewports
- API endpoints

## 🐛 Debugging

### Debug Mode
```bash
# Run tests in debug mode
npm run test:debug

# Run specific test in debug mode
npx playwright test auth.spec.ts --debug

# Run tests with headed browser
npm run test:headed
```

### Trace Viewer
```bash
# Generate traces
npx playwright test --trace on

# View traces
npx playwright show-trace trace.zip
```

## 📈 Performance Testing

### Metrics Collected
- Page load times
- First Contentful Paint
- Largest Contentful Paint
- DOM Content Loaded
- Network idle time

### Performance Thresholds
- Login page: < 3 seconds
- Chat page: < 5 seconds  
- Message response: < 10 seconds
- Navigation transitions: < 2 seconds

## ♿ Accessibility Testing

### WCAG 2.1 Compliance
- **Level AA** compliance testing
- Keyboard navigation
- Screen reader compatibility
- Color contrast validation
- Focus management
- ARIA attributes

### Tools Integration
- Built-in accessibility checks
- Keyboard navigation testing
- High contrast mode simulation
- Reduced motion preferences
- Voice control simulation

## 🔄 Extending the Framework

### Adding New Page Objects
1. Create new page class extending `BasePage`
2. Define locators and methods
3. Add to test imports

### Adding New Test Suites
1. Create new `.spec.ts` file in `tests/`
2. Import required page objects
3. Add appropriate test tags
4. Update CI/CD workflow if needed

### Adding Custom Helpers
1. Add functions to `TestHelpers.ts`
2. Import in test files
3. Document usage patterns

## 📝 Best Practices

### Test Writing
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)
- Add proper test tags
- Include step-by-step documentation
- Handle test data cleanup

### Page Objects
- Keep locators simple and reliable
- Use semantic selectors when possible
- Add waiting strategies
- Include error handling
- Document complex interactions

### Maintenance
- Regular selector updates
- Test data refresh
- Performance threshold reviews
- Accessibility standard updates
- Browser compatibility checks

## 🚨 Troubleshooting

### Common Issues

**Tests timing out**
- Increase timeout values
- Check application startup
- Verify network connectivity

**Selector not found**
- Update locators
- Check for dynamic content
- Add proper waits

**Flaky tests**
- Add explicit waits
- Handle race conditions
- Improve test isolation

**CI/CD failures**
- Check application dependencies
- Verify environment setup
- Review artifact logs

## 📞 Support

For issues with the test suite:
1. Check existing test documentation
2. Review error logs and screenshots
3. Verify application state
4. Create issue with reproduction steps

## 🏆 Test Results Summary

Based on initial test execution:
- **Total Test Cases**: 45+ comprehensive tests
- **Browser Coverage**: Chrome, Firefox, Safari, Edge
- **Mobile Coverage**: iOS Safari, Android Chrome
- **Accessibility**: WCAG 2.1 AA compliance
- **Performance**: Core Web Vitals monitoring
- **Security**: XSS and input validation testing

The test suite provides comprehensive coverage of the AI Chat Assistant application with automated regression testing, cross-browser compatibility, and accessibility compliance verification.