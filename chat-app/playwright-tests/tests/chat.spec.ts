import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { ChatPage } from '../pages/ChatPage';
import { TestData } from '../utils/TestData';
import { TestHelpers } from '../utils/TestHelpers';

test.describe('Chat Functionality Tests - @chat @regression', () => {
  let loginPage: LoginPage;
  let chatPage: ChatPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    chatPage = new ChatPage(page);
    
    // Login before each test
    await loginPage.goto();
    await loginPage.login(TestData.VALID_USERS.STANDARD);
    await chatPage.verifyChatPageLoaded();
  });

  test('TC_010: Valid Chat Message - @smoke', async ({ page }) => {
    // Test sending valid chat messages
    await test.step('Send simple message', async () => {
      await chatPage.sendMessageAndWaitForResponse(TestData.MESSAGES.SIMPLE);
      
      const lastUserMessage = await chatPage.getLastUserMessage();
      const lastAssistantMessage = await chatPage.getLastAssistantMessage();
      
      expect(lastUserMessage).toContain(TestData.MESSAGES.SIMPLE);
      expect(lastAssistantMessage).toBeTruthy();
    });

    await test.step('Verify success alert', async () => {
      await chatPage.verifySuccessAlert();
    });
  });

  test('TC_012: Empty Chat Message Validation', async ({ page }) => {
    // Test empty message validation
    await test.step('Attempt to send empty message', async () => {
      await chatPage.testEmptyMessage();
    });

    await test.step('Verify no message was sent', async () => {
      const messageCount = await chatPage.getChatMessageCount();
      // Should only have welcome message, no user messages
      expect(messageCount.user).toBe(0);
    });
  });

  test('TC_031: Enhanced Message Formatting', async ({ page }) => {
    // Test message formatting with markdown
    await test.step('Send message with formatting', async () => {
      await chatPage.verifyMessageFormatting(TestData.MESSAGES.WITH_FORMATTING);
    });

    await test.step('Send message with code block', async () => {
      await chatPage.sendMessage(TestData.MESSAGES.CODE_BLOCK);
      const lastMessage = await chatPage.getLastUserMessage();
      expect(lastMessage).toContain('```javascript');
    });

    await test.step('Send message with markdown list', async () => {
      await chatPage.sendMessage(TestData.MESSAGES.MARKDOWN_LIST);
      const lastMessage = await chatPage.getLastUserMessage();
      expect(lastMessage).toContain('- What are the interest rates?');
    });
  });

  test('TC_014: Long Message Processing', async ({ page }) => {
    // Test handling of very long messages
    await test.step('Send very long message', async () => {
      await chatPage.testLongMessage(TestData.MESSAGES.LONG_MESSAGE);
    });

    await test.step('Verify message was processed', async () => {
      const lastUserMessage = await chatPage.getLastUserMessage();
      const lastAssistantMessage = await chatPage.getLastAssistantMessage();
      
      expect(lastUserMessage).toBeTruthy();
      expect(lastAssistantMessage).toBeTruthy();
    });

    await test.step('Verify system stability', async () => {
      await TestHelpers.verifyNoJSErrors(page);
    });
  });

  test('TC_015: Clear Chat History - @smoke', async ({ page }) => {
    // Test chat history clearing functionality
    await test.step('Send multiple messages', async () => {
      await chatPage.sendMessageAndWaitForResponse(TestData.MESSAGES.SIMPLE);
      await chatPage.sendMessageAndWaitForResponse(TestData.MESSAGES.HOME_LOANS);
    });

    await test.step('Verify messages exist', async () => {
      const messageCount = await chatPage.getChatMessageCount();
      expect(messageCount.user).toBeGreaterThan(0);
      expect(messageCount.assistant).toBeGreaterThan(0);
    });

    await test.step('Clear chat history', async () => {
      await chatPage.clearChatHistory();
    });

    await test.step('Verify chat is cleared', async () => {
      const messageCount = await chatPage.getChatMessageCount();
      expect(messageCount.user).toBe(0);
      // Welcome message should still be present
      await chatPage.verifyWelcomeMessage(TestData.VALID_USERS.STANDARD);
    });
  });

  test('TC_XSS: Security - XSS Prevention', async ({ page }) => {
    // Test XSS attack prevention
    await test.step('Attempt XSS injection in message', async () => {
      await chatPage.sendMessage(TestData.MESSAGES.XSS_ATTEMPT);
      
      // Verify the script is not executed
      const lastMessage = await chatPage.getLastUserMessage();
      expect(lastMessage).toContain('&lt;script&gt;'); // Should be escaped
    });

    await test.step('Attempt HTML injection', async () => {
      await chatPage.sendMessage(TestData.MESSAGES.HTML_INJECTION);
      
      const lastMessage = await chatPage.getLastUserMessage();
      expect(lastMessage).not.toContain('<img'); // Should be escaped
    });
  });

  test('TC_EMOJI: Emoji and Special Characters', async ({ page }) => {
    // Test emoji and special character handling
    await test.step('Send message with emojis', async () => {
      await chatPage.sendMessageAndWaitForResponse(TestData.MESSAGES.EMOJI);
      
      const lastMessage = await chatPage.getLastUserMessage();
      expect(lastMessage).toContain('😊');
      expect(lastMessage).toContain('🏠');
    });
  });

  test('TC_MULTIPLE: Multiple Topic Message', async ({ page }) => {
    // Test handling of messages with multiple topics
    await test.step('Send message about multiple services', async () => {
      await chatPage.sendMessageAndWaitForResponse(TestData.MESSAGES.MULTIPLE_TOPICS);
      
      const lastUserMessage = await chatPage.getLastUserMessage();
      const lastAssistantMessage = await chatPage.getLastAssistantMessage();
      
      expect(lastUserMessage).toContain('home loans');
      expect(lastUserMessage).toContain('car loans');
      expect(lastUserMessage).toContain('personal banking');
      expect(lastAssistantMessage).toBeTruthy();
    });
  });

  test.afterEach(async ({ page }) => {
    // Take screenshot for evidence
    await TestHelpers.takeScreenshot(page, 'chat-test-result');
    
    // Clean up: logout
    try {
      await chatPage.logout();
    } catch (error) {
      console.log('Cleanup error (ignored):', error);
    }
  });
});