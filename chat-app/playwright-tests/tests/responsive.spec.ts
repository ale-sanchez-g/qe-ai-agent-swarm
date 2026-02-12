import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { ChatPage } from '../pages/ChatPage';
import { TestData } from '../utils/TestData';
import { TestHelpers } from '../utils/TestHelpers';

test.describe('Responsive Design Tests - @responsive @regression', () => {
  let loginPage: LoginPage;
  let chatPage: ChatPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    chatPage = new ChatPage(page);
  });

  test('TC_033: Mobile Device Display - @smoke', async ({ page }) => {
    // Test mobile responsive design
    await test.step('Set mobile viewport', async () => {
      await page.setViewportSize(TestData.VIEWPORTS.MOBILE);
      await loginPage.goto();
    });

    await test.step('Verify login page on mobile', async () => {
      await loginPage.verifyPageLoaded();
      
      // Verify elements are visible and accessible on mobile
      await expect(loginPage.pageTitle).toBeVisible();
      await expect(loginPage.userIdInput).toBeVisible();
      await expect(loginPage.startChattingButton).toBeVisible();
    });

    await test.step('Test login functionality on mobile', async () => {
      await loginPage.login(TestData.VALID_USERS.STANDARD);
      await chatPage.verifyChatPageLoaded();
    });

    await test.step('Verify chat interface on mobile', async () => {
      await chatPage.verifyResponsiveDesign(TestData.VIEWPORTS.MOBILE);
      
      // Test message sending on mobile
      await chatPage.sendMessage(TestData.MESSAGES.SIMPLE);
      const lastMessage = await chatPage.getLastUserMessage();
      expect(lastMessage).toContain(TestData.MESSAGES.SIMPLE);
    });

    await test.step('Verify settings dropdown on mobile', async () => {
      await chatPage.openSettingsDropdown();
      await expect(chatPage.logoutButton).toBeVisible();
    });
  });

  test('TC_034: Tablet Display Optimization', async ({ page }) => {
    // Test tablet responsive design
    await test.step('Set tablet viewport', async () => {
      await page.setViewportSize(TestData.VIEWPORTS.TABLET);
      await loginPage.goto();
    });

    await test.step('Verify login page on tablet', async () => {
      await loginPage.verifyPageLoaded();
      await loginPage.verifyBrowserInfoCollected();
    });

    await test.step('Test full workflow on tablet', async () => {
      await loginPage.login(TestData.VALID_USERS.STANDARD);
      await chatPage.verifyChatPageLoaded();
      await chatPage.verifyResponsiveDesign(TestData.VIEWPORTS.TABLET);
    });

    await test.step('Test chat functionality on tablet', async () => {
      await chatPage.sendMessageAndWaitForResponse(TestData.MESSAGES.HOME_LOANS);
      
      const messageCount = await chatPage.getChatMessageCount();
      expect(messageCount.user).toBeGreaterThan(0);
      expect(messageCount.assistant).toBeGreaterThan(0);
    });

    await test.step('Test orientation change simulation', async () => {
      // Simulate landscape orientation
      await page.setViewportSize({ 
        width: TestData.VIEWPORTS.TABLET.height, 
        height: TestData.VIEWPORTS.TABLET.width 
      });
      
      await chatPage.verifyChatPageLoaded();
      await expect(chatPage.messageInput).toBeVisible();
    });
  });

  test('TC_035: Desktop Browser Scaling', async ({ page }) => {
    // Test desktop responsive design at different scales
    await test.step('Test standard desktop resolution', async () => {
      await page.setViewportSize(TestData.VIEWPORTS.DESKTOP);
      await loginPage.goto();
      await loginPage.verifyPageLoaded();
    });

    await test.step('Test large desktop resolution', async () => {
      await page.setViewportSize(TestData.VIEWPORTS.LARGE_DESKTOP);
      await loginPage.verifyPageLoaded();
      
      // Verify content doesn't become too wide
      const loginContainer = page.locator('.container, .login-container, main').first();
      const boundingBox = await loginContainer.boundingBox();
      
      if (boundingBox) {
        // Content should have reasonable max-width
        expect(boundingBox.width).toBeLessThan(1200);
      }
    });

    await test.step('Test laptop resolution', async () => {
      await page.setViewportSize(TestData.VIEWPORTS.LAPTOP);
      await loginPage.login(TestData.VALID_USERS.STANDARD);
      await chatPage.verifyChatPageLoaded();
      await chatPage.verifyResponsiveDesign(TestData.VIEWPORTS.LAPTOP);
    });
  });

  test('TC_MOBILE_LANDSCAPE: Mobile Landscape Orientation', async ({ page }) => {
    // Test mobile landscape orientation
    await test.step('Set mobile landscape viewport', async () => {
      await page.setViewportSize(TestData.VIEWPORTS.MOBILE_LANDSCAPE);
      await loginPage.goto();
    });

    await test.step('Verify layout in landscape mode', async () => {
      await loginPage.verifyPageLoaded();
      await loginPage.login(TestData.VALID_USERS.STANDARD);
      await chatPage.verifyChatPageLoaded();
    });

    await test.step('Test chat functionality in landscape', async () => {
      await chatPage.sendMessage(TestData.MESSAGES.SIMPLE);
      
      // Verify message input is still accessible
      await expect(chatPage.messageInput).toBeVisible();
      await expect(chatPage.sendButton).toBeVisible();
    });
  });

  test('TC_ZOOM: Browser Zoom Testing', async ({ page }) => {
    // Test different zoom levels
    await test.step('Test 150% zoom level', async () => {
      await page.setViewportSize(TestData.VIEWPORTS.DESKTOP);
      await page.evaluate(() => {
        document.body.style.zoom = '1.5';
      });
      
      await loginPage.goto();
      await loginPage.verifyPageLoaded();
    });

    await test.step('Test 75% zoom level', async () => {
      await page.evaluate(() => {
        document.body.style.zoom = '0.75';
      });
      
      await loginPage.verifyPageLoaded();
      await loginPage.login(TestData.VALID_USERS.STANDARD);
      await chatPage.verifyChatPageLoaded();
    });

    await test.step('Reset zoom and verify normal operation', async () => {
      await page.evaluate(() => {
        document.body.style.zoom = '1';
      });
      
      await chatPage.sendMessage(TestData.MESSAGES.SIMPLE);
    });
  });

  test('TC_TOUCH: Touch Interactions', async ({ page }) => {
    // Test touch-specific interactions on mobile
    await test.step('Set mobile viewport for touch testing', async () => {
      await page.setViewportSize(TestData.VIEWPORTS.MOBILE);
      await loginPage.goto();
    });

    await test.step('Test touch interactions on login', async () => {
      // Simulate touch events
      await loginPage.userIdInput.tap();
      await loginPage.enterUserId(TestData.VALID_USERS.STANDARD);
      await loginPage.startChattingButton.tap();
      
      await chatPage.verifyChatPageLoaded();
    });

    await test.step('Test touch interactions in chat', async () => {
      await chatPage.messageInput.tap();
      await chatPage.sendMessage(TestData.MESSAGES.SIMPLE);
      
      // Test touch on settings button
      await chatPage.settingsButton.tap();
      await expect(chatPage.settingsDropdown).toBeVisible();
    });
  });

  test('TC_SCROLL: Scrolling Behavior', async ({ page }) => {
    // Test scrolling behavior across devices
    await test.step('Test on mobile with long content', async () => {
      await page.setViewportSize(TestData.VIEWPORTS.MOBILE);
      await loginPage.goto();
      await loginPage.login(TestData.VALID_USERS.STANDARD);
      await chatPage.verifyChatPageLoaded();
    });

    await test.step('Generate long conversation for scrolling', async () => {
      // Send multiple messages to create scrollable content
      for (let i = 0; i < 5; i++) {
        await chatPage.sendMessage(`Test message ${i + 1}: ${TestData.MESSAGES.SIMPLE}`);
        await page.waitForTimeout(500); // Small delay between messages
      }
    });

    await test.step('Test auto-scroll to bottom', async () => {
      // Verify the latest message is visible
      const messageCount = await chatPage.getChatMessageCount();
      expect(messageCount.user).toBe(5);
      
      // The message input should remain accessible
      await expect(chatPage.messageInput).toBeInViewport();
    });

    await test.step('Test manual scrolling', async () => {
      // Scroll up to see earlier messages
      await page.mouse.wheel(0, -500);
      
      // Send a new message
      await chatPage.sendMessage('New message after scroll');
      
      // Should auto-scroll to show new message
      await expect(chatPage.messageInput).toBeInViewport();
    });
  });

  test('TC_CSS: CSS Responsive Features', async ({ page }) => {
    // Test CSS-specific responsive features
    await test.step('Verify CSS media queries work', async () => {
      await loginPage.goto();
      
      // Test different breakpoints
      const breakpoints = [
        TestData.VIEWPORTS.MOBILE,
        TestData.VIEWPORTS.TABLET,
        TestData.VIEWPORTS.DESKTOP
      ];
      
      for (const viewport of breakpoints) {
        await page.setViewportSize(viewport);
        await page.waitForTimeout(100); // Allow CSS transitions
        
        // Verify layout adapts
        await expect(loginPage.pageTitle).toBeVisible();
        await expect(loginPage.userIdInput).toBeVisible();
      }
    });
  });

  test.afterEach(async ({ page }) => {
    // Reset viewport to desktop for consistent cleanup
    await page.setViewportSize(TestData.VIEWPORTS.DESKTOP);
    
    // Reset any zoom or CSS modifications
    await page.evaluate(() => {
      document.body.style.zoom = '1';
    });
    
    await TestHelpers.takeScreenshot(page, 'responsive-test-result');
    
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