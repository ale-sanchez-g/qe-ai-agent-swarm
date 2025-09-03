/**
 * Test data constants and generators
 */

export class TestData {
  // Valid test users
  static readonly VALID_USERS = {
    STANDARD: 'testuser123',
    ADMIN: 'admin',
    LONG_NAME: 'verylongusernamethatisvalid',
    WITH_NUMBERS: 'user123test',
    WITH_UNDERSCORES: 'test_user_name',
    WITH_HYPHENS: 'test-user-name'
  };

  // Invalid user IDs for validation testing
  static readonly INVALID_USERS = {
    TOO_SHORT: 'a',
    TOO_LONG: 'a'.repeat(51),
    WITH_SPECIAL_CHARS: 'test@user!',
    WITH_SPACES: 'test user',
    EMPTY: '',
    WITH_SYMBOLS: 'user$name#',
    WITH_QUOTES: 'user"name',
    SQL_INJECTION: "'; DROP TABLE users; --"
  };

  // Test messages
  static readonly MESSAGES = {
    SIMPLE: 'Hello, how can you help me?',
    HOME_LOANS: 'Can you help me with home loan information?',
    WITH_FORMATTING: 'Can you help me with **home loans** and provide some *important* details about `interest rates`?',
    LONG_MESSAGE: `This is a very long message to test the system's ability to handle extended input text. 
      I'm asking about comprehensive home loan information including interest rates, loan terms, 
      eligibility criteria, documentation requirements, application process, approval timeframes, 
      and any special offers or programs that might be available for first-time home buyers or 
      investment properties. Additionally, I'd like to understand the differences between fixed 
      and variable rates, and what factors influence the approval process. Can you provide detailed 
      information about all these aspects of home loans and help me understand what options might 
      be best for my situation? I want to make sure I have all the information I need before 
      proceeding with a loan application.`,
    EMPTY: '',
    CODE_BLOCK: 'Here is some code: ```javascript\nconst message = "Hello World";\nconsole.log(message);\n```',
    MARKDOWN_LIST: `Here are my questions:
      - What are the interest rates?
      - What documents do I need?
      - How long does approval take?`,
    MULTIPLE_TOPICS: 'I need help with home loans, car loans, and personal banking services.',
    XSS_ATTEMPT: '<script>alert("XSS")</script>',
    HTML_INJECTION: '<img src="x" onerror="alert(1)">',
    EMOJI: 'Hello! 😊 Can you help me with loans? 🏠💰'
  };

  // Validation messages
  static readonly VALIDATION_MESSAGES = {
    USER_ID_LENGTH: 'User ID must be between 2 and 50 characters',
    USER_ID_REQUIRED: 'User ID is required',
    USER_ID_INVALID_CHARS: 'User ID can only contain letters, numbers, dashes, and underscores',
    MESSAGE_EMPTY: 'Message cannot be empty'
  };

  // Expected responses
  static readonly EXPECTED_RESPONSES = {
    FALLBACK: 'FinBot is not available for you at this time',
    CONTACT_EMAIL: 'help@devops1.com.au'
  };

  // Browser viewports for responsive testing
  static readonly VIEWPORTS = {
    DESKTOP: { width: 1440, height: 900 },
    LAPTOP: { width: 1024, height: 768 },
    TABLET: { width: 768, height: 1024 },
    MOBILE: { width: 375, height: 667 },
    MOBILE_LANDSCAPE: { width: 667, height: 375 },
    LARGE_DESKTOP: { width: 1920, height: 1080 }
  };

  // API endpoints
  static readonly ENDPOINTS = {
    LOGIN: '/api/login',
    CHAT: '/api/chat',
    LOGOUT: '/api/logout',
    CLEAR: '/api/clear',
    HEALTH: '/api/health',
    DEBUG: '/api/debug'
  };

  // Page titles
  static readonly PAGE_TITLES = {
    LOGIN: 'AI FinBot - Login',
    CHAT: 'AI FinBot'
  };

  /**
   * Generate random user ID
   */
  static generateRandomUserId(length: number = 10): string {
    const chars = 'abcdefghijklmnopqrstuvwxyz0123456789_-';
    let result = '';
    for (let i = 0; i < length; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  }

  /**
   * Generate timestamp for unique identifiers
   */
  static generateTimestamp(): string {
    return new Date().toISOString().replace(/[:.]/g, '-');
  }

  /**
   * Get current date formatted
   */
  static getCurrentDate(): string {
    return new Date().toLocaleDateString('en-GB');
  }

  /**
   * Generate test file name with timestamp
   */
  static generateTestFileName(prefix: string, extension: string = 'png'): string {
    return `${prefix}_${this.generateTimestamp()}.${extension}`;
  }
}

/**
 * Browser information for testing
 */
export class BrowserInfo {
  static readonly EXPECTED_PROPERTIES = [
    'browser',
    'platform', 
    'device',
    'language',
    'timezone'
  ];

  static readonly EXPECTED_BROWSERS = [
    'Chrome',
    'Firefox', 
    'Safari',
    'Edge'
  ];

  static readonly EXPECTED_PLATFORMS = [
    'MacIntel',
    'Win32',
    'Linux'
  ];
}