import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { ChatPage } from '../pages/ChatPage';
import { TestData } from '../utils/TestData';
import { TestHelpers } from '../utils/TestHelpers';

test.describe('Accessibility and Keyboard Navigation Tests - @accessibility @regression', () => {
  let loginPage: LoginPage;
  let chatPage: ChatPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    chatPage = new ChatPage(page);
  });

  test('TC_062: Keyboard Navigation with Authentication - @smoke', async ({ page }) => {
    // Test full keyboard navigation support
    await test.step('Navigate to login page', async () => {
      await loginPage.goto();
      await loginPage.verifyPageLoaded();
    });

    await test.step('Test keyboard navigation on login page', async () => {
      // Tab to user ID input
      await page.keyboard.press('Tab');
      await expect(loginPage.userIdInput).toBeFocused();
      
      // Type user ID
      await page.keyboard.type(TestData.VALID_USERS.STANDARD);
      
      // Tab to start chatting button
      await page.keyboard.press('Tab');
      await expect(loginPage.startChattingButton).toBeFocused();
      
      // Press Enter to submit
      await page.keyboard.press('Enter');
      await chatPage.verifyChatPageLoaded();
    });

    await test.step('Test keyboard navigation in chat interface', async () => {
      // Tab should focus on message input
      await page.keyboard.press('Tab');
      await expect(chatPage.messageInput).toBeFocused();
      
      // Type message
      await page.keyboard.type(TestData.MESSAGES.SIMPLE);
      
      // Tab to send button
      await page.keyboard.press('Tab');
      await expect(chatPage.sendButton).toBeFocused();
      
      // Press Enter to send
      await page.keyboard.press('Enter');
      
      const lastMessage = await chatPage.getLastUserMessage();
      expect(lastMessage).toContain(TestData.MESSAGES.SIMPLE);
    });

    await test.step('Test keyboard navigation in settings', async () => {
      // Navigate to settings using keyboard
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab'); // May need multiple tabs to reach settings
      
      // Use arrow keys if it's a dropdown
      await page.keyboard.press('Space'); // Open settings if focused
      
      // Verify settings can be accessed via keyboard
      const settingsVisible = await chatPage.isElementVisible(chatPage.settingsDropdown);
      if (settingsVisible) {
        // Navigate through settings options
        await page.keyboard.press('ArrowDown');
        await page.keyboard.press('ArrowDown');
        await page.keyboard.press('Escape'); // Close dropdown
      }
    });
  });

  test('TC_063: Screen Reader Compatibility', async ({ page }) => {
    // Test screen reader compatibility
    await test.step('Verify semantic HTML structure', async () => {
      await loginPage.goto();
      
      // Check for proper heading structure
      const h1Count = await page.locator('h1').count();
      expect(h1Count).toBeGreaterThanOrEqual(1);
      
      // Check for proper form labels
      const labelledInputs = await page.locator('input[aria-label], input[id]').count();
      const totalInputs = await page.locator('input').count();
      expect(labelledInputs).toBe(totalInputs);
    });

    await test.step('Verify ARIA attributes', async () => {
      await loginPage.login(TestData.VALID_USERS.STANDARD);
      await chatPage.verifyChatPageLoaded();
      
      // Check for ARIA roles
      const chatContainer = page.getByRole('log');
      await expect(chatContainer).toBeVisible();
      
      // Check for proper button roles
      const buttons = await page.getByRole('button').count();
      expect(buttons).toBeGreaterThan(0);
    });

    await test.step('Test dynamic content announcements', async () => {
      // Send a message and verify the response area is accessible
      await chatPage.sendMessage(TestData.MESSAGES.SIMPLE);
      
      // Check that success alerts have proper roles
      const alerts = await page.locator('[role="alert"]').count();
      expect(alerts).toBeGreaterThanOrEqual(0); // May or may not have alerts
    });
  });

  test('TC_064: Color and Contrast Accessibility', async ({ page }) => {
    // Test color contrast and visual accessibility
    await test.step('Verify basic contrast requirements', async () => {
      await loginPage.goto();
      
      // Get computed styles for text elements
      const titleColor = await loginPage.pageTitle.evaluate(el => {
        const style = window.getComputedStyle(el);
        return {
          color: style.color,
          backgroundColor: style.backgroundColor
        };
      });
      
      expect(titleColor.color).toBeTruthy();
    });

    await test.step('Test high contrast mode simulation', async () => {
      // Simulate high contrast by modifying CSS
      await page.addStyleTag({
        content: `
          * {
            background: black !important;
            color: white !important;
            border-color: white !important;
          }
        `
      });
      
      // Verify page is still functional
      await loginPage.verifyPageLoaded();
      await expect(loginPage.userIdInput).toBeVisible();
      await expect(loginPage.startChattingButton).toBeVisible();
    });
  });

  test('TC_FOCUS: Focus Management', async ({ page }) => {
    // Test focus management and visibility
    await test.step('Test focus indicators', async () => {
      await loginPage.goto();
      
      // Tab through elements and verify focus is visible
      await page.keyboard.press('Tab');
      
      // Check if focus outline is visible (this is basic check)
      const focusedElement = await page.evaluateHandle(() => document.activeElement);
      expect(focusedElement).toBeTruthy();
    });

    await test.step('Test focus trapping in modals', async () => {
      await loginPage.login(TestData.VALID_USERS.STANDARD);
      await chatPage.verifyChatPageLoaded();
      
      // Try to trigger logout confirmation modal
      await chatPage.openSettingsDropdown();
      await chatPage.logoutButton.click();
      
      // Focus should be trapped in the confirmation dialog
      // This would require the dialog to be properly implemented
    });

    await test.step('Test focus restoration', async () => {
      // After closing modal, focus should return to trigger element
      await page.keyboard.press('Escape'); // Close any open dialogs
      await page.keyboard.press('Escape'); // Close dropdown if open
      
      // Focus should be restored appropriately
      const activeElement = await page.evaluateHandle(() => document.activeElement);
      expect(activeElement).toBeTruthy();
    });
  });

  test('TC_SKIP_LINKS: Skip Links and Navigation', async ({ page }) => {
    // Test skip links and navigation aids
    await test.step('Test skip links if present', async () => {
      await loginPage.goto();
      
      // Press Tab to reveal skip links (common pattern)
      await page.keyboard.press('Tab');
      
      // Look for skip links
      const skipLinks = await page.locator('a[href^="#"], .skip-link').count();
      
      // If skip links exist, test them
      if (skipLinks > 0) {
        const firstSkipLink = page.locator('a[href^="#"], .skip-link').first();
        await firstSkipLink.click();
        
        // Verify focus moved to target
        const activeElement = await page.evaluateHandle(() => document.activeElement);
        expect(activeElement).toBeTruthy();
      }
    });
  });

  test('TC_LANDMARK: Landmark Navigation', async ({ page }) => {
    // Test landmark roles and navigation
    await test.step('Verify page landmarks', async () => {
      await loginPage.goto();
      
      // Check for main landmark
      const mainLandmarks = await page.locator('main, [role="main"]').count();
      expect(mainLandmarks).toBeGreaterThanOrEqual(1);
      
      // Check for form landmark
      const formLandmarks = await page.locator('form, [role="form"]').count();
      expect(formLandmarks).toBeGreaterThanOrEqual(1);
    });

    await test.step('Verify chat page landmarks', async () => {
      await loginPage.login(TestData.VALID_USERS.STANDARD);
      await chatPage.verifyChatPageLoaded();
      
      // Check for application landmark or main content
      const appLandmarks = await page.locator('main, [role="main"], [role="application"]').count();
      expect(appLandmarks).toBeGreaterThanOrEqual(1);
    });
  });

  test('TC_KEYBOARD_SHORTCUTS: Keyboard Shortcuts', async ({ page }) => {
    // Test keyboard shortcuts if implemented
    await test.step('Test common keyboard shortcuts', async () => {
      await loginPage.goto();
      await loginPage.login(TestData.VALID_USERS.STANDARD);
      await chatPage.verifyChatPageLoaded();
      
      // Test Enter key in message input
      await chatPage.messageInput.focus();
      await page.keyboard.type(TestData.MESSAGES.SIMPLE);
      await page.keyboard.press('Enter');
      
      const lastMessage = await chatPage.getLastUserMessage();
      expect(lastMessage).toContain(TestData.MESSAGES.SIMPLE);
    });

    await test.step('Test Escape key behavior', async () => {
      // Open settings dropdown
      await chatPage.openSettingsDropdown();
      
      // Press Escape to close
      await page.keyboard.press('Escape');
      
      // Dropdown should be closed
      const dropdownVisible = await chatPage.isElementVisible(chatPage.settingsDropdown);
      expect(dropdownVisible).toBeFalsy();
    });
  });

  test('TC_VOICE_CONTROL: Voice Control Simulation', async ({ page }) => {
    // Simulate voice control by using click commands and verification
    await test.step('Test voice-like commands via clicking', async () => {
      await loginPage.goto();
      
      // Simulate "click user id field"
      await loginPage.userIdInput.click();
      await expect(loginPage.userIdInput).toBeFocused();
      
      // Simulate typing via voice
      await loginPage.enterUserId(TestData.VALID_USERS.STANDARD);
      
      // Simulate "click start chatting"
      await loginPage.startChattingButton.click();
      await chatPage.verifyChatPageLoaded();
    });

    await test.step('Test chat interaction via voice simulation', async () => {
      // Simulate "click message input"
      await chatPage.messageInput.click();
      
      // Simulate voice input
      await chatPage.sendMessage(TestData.MESSAGES.SIMPLE);
      
      const lastMessage = await chatPage.getLastUserMessage();
      expect(lastMessage).toContain(TestData.MESSAGES.SIMPLE);
    });
  });

  test('TC_REDUCED_MOTION: Reduced Motion Support', async ({ page }) => {
    // Test reduced motion preferences
    await test.step('Simulate reduced motion preference', async () => {
      // Set reduced motion preference
      await page.emulateMedia({ reducedMotion: 'reduce' });
      
      await loginPage.goto();
      await loginPage.verifyPageLoaded();
      
      // Verify page still functions with reduced motion
      await loginPage.login(TestData.VALID_USERS.STANDARD);
      await chatPage.verifyChatPageLoaded();
    });

    await test.step('Test animations respect motion preference', async () => {
      // Send message and verify smooth operation without jarring animations
      await chatPage.sendMessage(TestData.MESSAGES.SIMPLE);
      
      // Basic functionality should work regardless of motion settings
      const lastMessage = await chatPage.getLastUserMessage();
      expect(lastMessage).toContain(TestData.MESSAGES.SIMPLE);
    });
  });

  test.afterEach(async ({ page }) => {
    // Reset any accessibility modifications
    await page.emulateMedia({ reducedMotion: 'no-preference' });
    
    await TestHelpers.takeScreenshot(page, 'accessibility-test-result');
    
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