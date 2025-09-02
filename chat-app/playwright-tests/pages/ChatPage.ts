import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * Chat Page Object Model
 * Handles all interactions with the main chat interface
 */
export class ChatPage extends BasePage {
  // Header elements
  readonly pageTitle: Locator;
  readonly userDisplay: Locator;
  readonly clearChatButton: Locator;
  readonly settingsButton: Locator;
  readonly settingsDropdown: Locator;
  readonly logoutButton: Locator;

  // Chat area elements
  readonly chatContainer: Locator;
  readonly welcomeMessage: Locator;
  readonly messageInput: Locator;
  readonly sendButton: Locator;
  readonly userMessages: Locator;
  readonly assistantMessages: Locator;
  readonly typingIndicator: Locator;

  // Settings dropdown elements
  readonly integrationsSection: Locator;
  readonly launchDarklyConfig: Locator;
  readonly awsBedrockRuntime: Locator;
  readonly observabilityPlugin: Locator;

  // Alert/Toast elements
  readonly successAlert: Locator;
  readonly errorAlert: Locator;
  readonly healthCheckResults: Locator;

  constructor(page: Page) {
    super(page, '/');
    
    // Header elements
    this.pageTitle = page.getByRole('heading', { name: /FinBot Chat Assistant/i });
    this.userDisplay = page.locator('strong').filter({ hasText: /testuser|user/i });
    this.clearChatButton = page.getByRole('button', { name: /Clear Chat/i });
    this.settingsButton = page.getByRole('button', { name: /Settings/i });
    this.settingsDropdown = page.locator('.dropdown-menu, [role="menu"]');
    this.logoutButton = page.getByRole('button', { name: /Logout/i });

    // Chat area elements
    this.chatContainer = page.getByRole('log', { name: /Chat conversation/i });
    this.welcomeMessage = page.getByText(/Welcome to your FinBot AI Assistant/i);
    this.messageInput = page.getByRole('textbox', { name: /Message input/i });
    this.sendButton = page.getByRole('button', { name: /Send message/i });
    this.userMessages = page.locator('.user-message, [data-role="user"]');
    this.assistantMessages = page.locator('.assistant-message, [data-role="assistant"]');
    this.typingIndicator = page.locator('.typing-indicator');

    // Settings dropdown elements
    this.integrationsSection = page.getByText('Integrations');
    this.launchDarklyConfig = page.getByText('LaunchDarkly AI Config');
    this.awsBedrockRuntime = page.getByText('AWS Bedrock Runtime');
    this.observabilityPlugin = page.getByText('Observability Plugin');

    // Alert elements
    this.successAlert = page.locator('.alert-success, [role="alert"]').filter({ hasText: /Success/i });
    this.errorAlert = page.locator('.alert-danger, .alert-error');
    this.healthCheckResults = page.getByText(/System Health Check Results/i);
  }

  /**
   * Verify chat page is loaded
   */
  async verifyChatPageLoaded(): Promise<void> {
    await expect(this.pageTitle).toBeVisible();
    await expect(this.messageInput).toBeVisible();
    await expect(this.sendButton).toBeVisible();
    await expect(this.chatContainer).toBeVisible();
  }

  /**
   * Verify user is logged in
   */
  async verifyUserLoggedIn(expectedUserId: string): Promise<void> {
    await expect(this.userDisplay).toBeVisible();
    await expect(this.userDisplay).toContainText(expectedUserId);
  }

  /**
   * Verify welcome message
   */
  async verifyWelcomeMessage(userId: string): Promise<void> {
    await expect(this.welcomeMessage).toBeVisible();
    await expect(this.welcomeMessage).toContainText(userId);
  }

  /**
   * Send a chat message
   */
  async sendMessage(message: string): Promise<void> {
    await this.fillInput(this.messageInput, message);
    await this.clickElement(this.sendButton);
  }

  /**
   * Send message and wait for response
   */
  async sendMessageAndWaitForResponse(message: string, timeout: number = 10000): Promise<void> {
    const initialMessageCount = await this.assistantMessages.count();
    await this.sendMessage(message);
    
    // Wait for new assistant message to appear
    await expect(this.assistantMessages).toHaveCount(initialMessageCount + 1, { timeout });
  }

  /**
   * Get last user message
   */
  async getLastUserMessage(): Promise<string> {
    const userMessageCount = await this.userMessages.count();
    if (userMessageCount === 0) return '';
    
    const lastMessage = this.userMessages.nth(userMessageCount - 1);
    return await this.getElementText(lastMessage);
  }

  /**
   * Get last assistant message
   */
  async getLastAssistantMessage(): Promise<string> {
    const assistantMessageCount = await this.assistantMessages.count();
    if (assistantMessageCount === 0) return '';
    
    const lastMessage = this.assistantMessages.nth(assistantMessageCount - 1);
    return await this.getElementText(lastMessage);
  }

  /**
   * Clear chat history
   */
  async clearChatHistory(): Promise<void> {
    await this.handleDialog('accept');
    await this.clickElement(this.clearChatButton);
    await this.waitForNavigation();
  }

  /**
   * Open settings dropdown
   */
  async openSettingsDropdown(): Promise<void> {
    await this.clickElement(this.settingsButton);
    await expect(this.settingsDropdown).toBeVisible();
  }

  /**
   * Verify settings dropdown content
   */
  async verifySettingsDropdownContent(): Promise<void> {
    await this.openSettingsDropdown();
    await expect(this.integrationsSection).toBeVisible();
    await expect(this.launchDarklyConfig).toBeVisible();
    await expect(this.awsBedrockRuntime).toBeVisible();
    await expect(this.observabilityPlugin).toBeVisible();
    await expect(this.logoutButton).toBeVisible();
  }

  /**
   * Logout from the application
   */
  async logout(): Promise<void> {
    await this.openSettingsDropdown();
    await this.handleDialog('accept');
    await this.clickElement(this.logoutButton);
    await this.waitForNavigation();
  }

  /**
   * Verify success alert is displayed
   */
  async verifySuccessAlert(expectedMessage?: string): Promise<void> {
    await expect(this.successAlert).toBeVisible();
    if (expectedMessage) {
      await expect(this.successAlert).toContainText(expectedMessage);
    }
  }

  /**
   * Verify health check results
   */
  async verifyHealthCheckResults(): Promise<void> {
    await expect(this.healthCheckResults).toBeVisible();
    await expect(this.page.getByText(/Overall Status: healthy/i)).toBeVisible();
    await expect(this.page.getByText(/AWS Bedrock: Connected/i)).toBeVisible();
    await expect(this.page.getByText(/LaunchDarkly: Connected/i)).toBeVisible();
  }

  /**
   * Test empty message validation
   */
  async testEmptyMessage(): Promise<void> {
    const initialMessageCount = await this.userMessages.count();
    await this.clickElement(this.sendButton);
    
    // Verify no new message was sent
    await expect(this.userMessages).toHaveCount(initialMessageCount);
  }

  /**
   * Test long message processing
   */
  async testLongMessage(longMessage: string): Promise<void> {
    await this.sendMessageAndWaitForResponse(longMessage);
    const lastUserMessage = await this.getLastUserMessage();
    expect(lastUserMessage).toContain(longMessage.substring(0, 100)); // Verify at least part of the message
  }

  /**
   * Get chat message count
   */
  async getChatMessageCount(): Promise<{ user: number; assistant: number }> {
    const userCount = await this.userMessages.count();
    const assistantCount = await this.assistantMessages.count();
    return { user: userCount, assistant: assistantCount };
  }

  /**
   * Verify message formatting
   */
  async verifyMessageFormatting(message: string): Promise<void> {
    await this.sendMessage(message);
    const lastMessage = await this.getLastUserMessage();
    expect(lastMessage).toContain(message);
  }

  /**
   * Test keyboard navigation
   */
  async testKeyboardNavigation(): Promise<void> {
    // Focus on message input
    await this.messageInput.focus();
    
    // Tab to send button
    await this.pressKey('Tab');
    await expect(this.sendButton).toBeFocused();
    
    // Tab to other elements
    await this.pressKey('Tab');
    // Verify focus moves through interface
  }

  /**
   * Verify responsive design
   */
  async verifyResponsiveDesign(viewport: { width: number; height: number }): Promise<void> {
    await this.page.setViewportSize(viewport);
    await this.verifyChatPageLoaded();
    
    // Verify elements are still accessible
    await expect(this.messageInput).toBeVisible();
    await expect(this.sendButton).toBeVisible();
    await expect(this.settingsButton).toBeVisible();
  }

  /**
   * Get page title
   */
  async getPageTitle(): Promise<string> {
    return await this.page.title();
  }
}