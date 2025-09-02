import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { ChatPage } from '../pages/ChatPage';
import { TestData } from '../utils/TestData';
import { TestHelpers } from '../utils/TestHelpers';

test.describe('UI Components Tests - @ui @regression', () => {
  let loginPage: LoginPage;
  let chatPage: ChatPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    chatPage = new ChatPage(page);
  });

  test('TC_019: Login Page Display', async ({ page }) => {
    // Test login page UI components
    await test.step('Navigate to login page', async () => {
      await loginPage.goto();
      await loginPage.verifyPageLoaded();
    });

    await test.step('Verify page elements are visible', async () => {
      await expect(loginPage.pageTitle).toBeVisible();
      await expect(loginPage.pageSubtitle).toBeVisible();
      await expect(loginPage.userIdInput).toBeVisible();
      await expect(loginPage.startChattingButton).toBeVisible();
    });

    await test.step('Verify browser info collection display', async () => {
      await loginPage.verifyBrowserInfoCollected();
    });

    await test.step('Check accessibility', async () => {
      await TestHelpers.verifyPageAccessibility(page);
    });
  });

  test('TC_020: Login Form Validation', async ({ page }) => {
    // Test client-side form validation
    await test.step('Navigate to login page', async () => {
      await loginPage.goto();
    });

    await test.step('Test real-time validation', async () => {
      await loginPage.enterUserId(TestData.INVALID_USERS.TOO_SHORT);
      await loginPage.clickStartChatting();
      await loginPage.verifyValidationMessage(TestData.VALIDATION_MESSAGES.USER_ID_LENGTH);
    });

    await test.step('Test validation clears with valid input', async () => {
      await loginPage.clearUserId();
      await loginPage.enterUserId(TestData.VALID_USERS.STANDARD);
      await loginPage.verifyNoValidationMessage();
    });
  });

  test('TC_022: Chat Header Display', async ({ page }) => {
    // Test chat interface header
    await test.step('Login and navigate to chat', async () => {
      await loginPage.goto();
      await loginPage.login(TestData.VALID_USERS.STANDARD);
      await chatPage.verifyChatPageLoaded();
    });

    await test.step('Verify header elements', async () => {
      await expect(chatPage.pageTitle).toBeVisible();
      await expect(chatPage.userDisplay).toBeVisible();
      await expect(chatPage.clearChatButton).toBeVisible();
      await expect(chatPage.settingsButton).toBeVisible();
    });

    await test.step('Verify user context in header', async () => {
      await chatPage.verifyUserLoggedIn(TestData.VALID_USERS.STANDARD);
    });
  });

  test('TC_023: Enhanced Settings Dropdown - @smoke', async ({ page }) => {
    // Test settings dropdown functionality
    await test.step('Login and access settings', async () => {
      await loginPage.goto();
      await loginPage.login(TestData.VALID_USERS.STANDARD);
      await chatPage.verifyChatPageLoaded();
    });

    await test.step('Open and verify settings dropdown', async () => {
      await chatPage.verifySettingsDropdownContent();
    });

    await test.step('Verify all settings options', async () => {
      await chatPage.openSettingsDropdown();
      await expect(chatPage.integrationsSection).toBeVisible();
      await expect(chatPage.launchDarklyConfig).toBeVisible();
      await expect(chatPage.awsBedrockRuntime).toBeVisible();
      await expect(chatPage.observabilityPlugin).toBeVisible();
      await expect(chatPage.logoutButton).toBeVisible();
    });
  });

  test('TC_024: Enhanced Typing Indicator', async ({ page }) => {
    // Test typing and loading indicators
    await test.step('Login and prepare for message', async () => {
      await loginPage.goto();
      await loginPage.login(TestData.VALID_USERS.STANDARD);
      await chatPage.verifyChatPageLoaded();
    });

    await test.step('Send message and observe loading states', async () => {
      await chatPage.sendMessage(TestData.MESSAGES.SIMPLE);
      
      // UI should remain responsive
      await expect(chatPage.messageInput).toBeVisible();
      await expect(chatPage.sendButton).toBeVisible();
    });
  });

  test('TC_026: Login to Chat Transition', async ({ page }) => {
    // Test smooth transition from login to chat
    await test.step('Start from login page', async () => {
      await loginPage.goto();
      await loginPage.verifyPageLoaded();
    });

    await test.step('Perform login and verify transition', async () => {
      const startTime = Date.now();
      await loginPage.login(TestData.VALID_USERS.STANDARD);
      await chatPage.verifyChatPageLoaded();
      const endTime = Date.now();
      
      // Verify transition is reasonably fast (under 5 seconds)
      expect(endTime - startTime).toBeLessThan(5000);
    });

    await test.step('Verify user context is maintained', async () => {
      await chatPage.verifyUserLoggedIn(TestData.VALID_USERS.STANDARD);
      await chatPage.verifyWelcomeMessage(TestData.VALID_USERS.STANDARD);
    });
  });

  test('TC_027: Logout Flow UI', async ({ page }) => {
    // Test logout process and interface cleanup
    await test.step('Login and create some chat history', async () => {
      await loginPage.goto();
      await loginPage.login(TestData.VALID_USERS.STANDARD);
      await chatPage.verifyChatPageLoaded();
      await chatPage.sendMessage(TestData.MESSAGES.SIMPLE);
    });

    await test.step('Initiate logout process', async () => {
      await chatPage.openSettingsDropdown();
      await expect(chatPage.logoutButton).toBeVisible();
    });

    await test.step('Complete logout and verify cleanup', async () => {
      await chatPage.logout();
      await loginPage.verifyPageLoaded();
      await expect(page).toHaveTitle(TestData.PAGE_TITLES.LOGIN);
    });
  });

  test('TC_030: Debug Information Display', async ({ page }) => {
    // Test debug information accessibility
    await test.step('Login to access debug features', async () => {
      await loginPage.goto();
      await loginPage.login(TestData.VALID_USERS.STANDARD);
      await chatPage.verifyChatPageLoaded();
    });

    await test.step('Access settings to view debug info', async () => {
      await chatPage.verifySettingsDropdownContent();
    });

    await test.step('Verify health check information', async () => {
      await chatPage.verifyHealthCheckResults();
    });
  });

  test('TC_UI_PERFORMANCE: UI Performance', async ({ page }) => {
    // Test UI performance metrics
    await test.step('Measure login page performance', async () => {
      await loginPage.goto();
      const loginMetrics = await TestHelpers.getPerformanceMetrics(page);
      
      // Verify reasonable load times
      expect(loginMetrics.domContentLoaded).toBeLessThan(2000);
      expect(loginMetrics.firstContentfulPaint).toBeLessThan(1500);
    });

    await test.step('Measure chat page performance', async () => {
      await loginPage.login(TestData.VALID_USERS.STANDARD);
      await chatPage.verifyChatPageLoaded();
      
      const chatMetrics = await TestHelpers.getPerformanceMetrics(page);
      expect(chatMetrics.domContentLoaded).toBeLessThan(3000);
    });
  });

  test('TC_UI_IMAGES: Image Loading', async ({ page }) => {
    // Test image loading and accessibility
    await test.step('Check for broken images on login page', async () => {
      await loginPage.goto();
      const brokenImages = await TestHelpers.checkForBrokenImages(page);
      expect(brokenImages).toHaveLength(0);
    });

    await test.step('Check for broken images on chat page', async () => {
      await loginPage.login(TestData.VALID_USERS.STANDARD);
      await chatPage.verifyChatPageLoaded();
      
      const brokenImages = await TestHelpers.checkForBrokenImages(page);
      expect(brokenImages).toHaveLength(0);
    });
  });

  test.afterEach(async ({ page }) => {
    await TestHelpers.takeScreenshot(page, 'ui-test-result');
    
    // Clean up: logout if logged in
    try {
      const currentUrl = page.url();
      if (!currentUrl.includes('login')) {
        await chatPage.logout();
      }
    } catch (error) {
      console.log('Cleanup error (ignored):', error);
    }
  });
});