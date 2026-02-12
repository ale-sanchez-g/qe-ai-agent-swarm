import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { ChatPage } from '../pages/ChatPage';
import { TestData } from '../utils/TestData';
import { TestHelpers } from '../utils/TestHelpers';

test.describe('Authentication Tests - @auth @regression', () => {
  let loginPage: LoginPage;
  let chatPage: ChatPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    chatPage = new ChatPage(page);
    await loginPage.goto();
  });

  test('TC_001: Valid User Login - @smoke', async ({ page }) => {
    // Test valid user login functionality
    await test.step('Verify login page is loaded', async () => {
      await loginPage.verifyPageLoaded();
      await loginPage.verifyPageTitle(TestData.PAGE_TITLES.LOGIN);
    });

    await test.step('Verify browser information is collected', async () => {
      await loginPage.verifyBrowserInfoCollected();
      const browserInfo = await loginPage.getBrowserInfo();
      expect(browserInfo.browser).toBeTruthy();
      expect(browserInfo.device).toBeTruthy();
    });

    await test.step('Login with valid user ID', async () => {
      await loginPage.login(TestData.VALID_USERS.STANDARD);
      await chatPage.verifyChatPageLoaded();
    });

    await test.step('Verify successful login', async () => {
      await chatPage.verifyUserLoggedIn(TestData.VALID_USERS.STANDARD);
      await chatPage.verifyWelcomeMessage(TestData.VALID_USERS.STANDARD);
      await expect(page).toHaveTitle(TestData.PAGE_TITLES.CHAT);
    });

    await test.step('Verify health check is displayed', async () => {
      await chatPage.verifyHealthCheckResults();
    });
  });

  test('TC_002: Invalid User ID Format', async ({ page }) => {
    // Test invalid user ID format validation
    await test.step('Test invalid characters in user ID', async () => {
      await loginPage.testInvalidUserIdFormat(TestData.INVALID_USERS.WITH_SPECIAL_CHARS);
      await expect(page).toHaveTitle(TestData.PAGE_TITLES.LOGIN);
    });

    await test.step('Test user ID with spaces', async () => {
      await loginPage.testInvalidUserIdFormat(TestData.INVALID_USERS.WITH_SPACES);
      await expect(page).toHaveTitle(TestData.PAGE_TITLES.LOGIN);
    });

    await test.step('Test SQL injection attempt', async () => {
      await loginPage.testInvalidUserIdFormat(TestData.INVALID_USERS.SQL_INJECTION);
      await expect(page).toHaveTitle(TestData.PAGE_TITLES.LOGIN);
    });
  });

  test('TC_003: Empty User ID Validation', async ({ page }) => {
    // Test empty user ID validation
    await test.step('Attempt login with empty user ID', async () => {
      await loginPage.testEmptyUserId();
      await expect(page).toHaveTitle(TestData.PAGE_TITLES.LOGIN);
    });

    await test.step('Verify no session is created', async () => {
      await loginPage.verifyPageLoaded();
    });
  });

  test('TC_004: User ID Length Validation', async ({ page }) => {
    // Test user ID length limits
    await test.step('Test user ID too short', async () => {
      await loginPage.testUserIdLength(TestData.INVALID_USERS.TOO_SHORT, true);
      await loginPage.verifyValidationMessage(TestData.VALIDATION_MESSAGES.USER_ID_LENGTH);
    });

    await test.step('Test user ID too long', async () => {
      await loginPage.clearUserId();
      await loginPage.testUserIdLength(TestData.INVALID_USERS.TOO_LONG);
      // Note: Long usernames may be accepted but truncated
    });

    await test.step('Test valid length user ID', async () => {
      await loginPage.clearUserId();
      await loginPage.login(TestData.VALID_USERS.STANDARD);
      await chatPage.verifyChatPageLoaded();
    });
  });

  test('TC_006: Logout Functionality - @smoke', async ({ page }) => {
    // Test logout functionality
    await test.step('Login first', async () => {
      await loginPage.login(TestData.VALID_USERS.STANDARD);
      await chatPage.verifyChatPageLoaded();
    });

    await test.step('Open settings and verify logout option', async () => {
      await chatPage.verifySettingsDropdownContent();
    });

    await test.step('Perform logout', async () => {
      await chatPage.logout();
      await loginPage.verifyPageLoaded();
    });

    await test.step('Verify redirect to login page', async () => {
      await expect(page).toHaveTitle(TestData.PAGE_TITLES.LOGIN);
    });
  });

  test('TC_005: Browser Context Collection', async ({ page }) => {
    // Test browser context data collection
    await test.step('Verify browser information display', async () => {
      await loginPage.verifyBrowserInfoCollected();
    });

    await test.step('Validate browser information properties', async () => {
      const browserInfo = await loginPage.getBrowserInfo();
      
      // Verify browser information contains expected data
      expect(browserInfo.browser).toMatch(/Chrome|Firefox|Safari|Edge/);
      expect(browserInfo.device).toContain('Desktop');
      expect(browserInfo.language).toBeTruthy();
      expect(browserInfo.timezone).toBeTruthy();
    });

    await test.step('Login and verify context is preserved', async () => {
      await loginPage.login(TestData.VALID_USERS.STANDARD);
      await chatPage.verifyChatPageLoaded();
      await chatPage.verifyUserLoggedIn(TestData.VALID_USERS.STANDARD);
    });
  });

  test.afterEach(async ({ page }) => {
    // Clean up: logout if logged in
    try {
      const currentUrl = page.url();
      if (!currentUrl.includes('login')) {
        await chatPage.logout();
      }
    } catch (error) {
      // Ignore errors during cleanup
      console.log('Cleanup error (ignored):', error);
    }
    
    await TestHelpers.takeScreenshot(page, 'auth-test-cleanup');
  });
});