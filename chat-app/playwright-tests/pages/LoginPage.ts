import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * Login Page Object Model
 * Handles all interactions with the login page
 */
export class LoginPage extends BasePage {
  // Locators
  readonly userIdInput: Locator;
  readonly startChattingButton: Locator;
  readonly pageTitle: Locator;
  readonly pageSubtitle: Locator;
  readonly browserInfoSection: Locator;
  readonly browserName: Locator;
  readonly deviceInfo: Locator;
  readonly languageInfo: Locator;
  readonly timezoneInfo: Locator;
  readonly validationMessage: Locator;

  constructor(page: Page) {
    super(page, '/');
    
    // Initialize locators
    this.userIdInput = page.getByRole('textbox', { name: /User ID/i });
    this.startChattingButton = page.getByRole('button', { name: /Start Chatting/i });
    this.pageTitle = page.getByRole('heading', { name: 'AI FinBot' });
    this.pageSubtitle = page.getByText('Enter your User ID to start chatting');
    this.browserInfoSection = page.getByText('Browser Information Collected');
    this.browserName = page.locator('strong').first();
    this.deviceInfo = page.getByText(/Device:/);
    this.languageInfo = page.getByText(/Language:/);
    this.timezoneInfo = page.getByText(/Timezone:/);
    this.validationMessage = page.locator('.text-danger, .error-message, [role="alert"]');
  }

  /**
   * Navigate to login page
   */
  async goto(): Promise<void> {
    await this.page.goto('/');
    await this.waitForPageLoad();
  }

  /**
   * Verify login page is loaded
   */
  async verifyPageLoaded(): Promise<void> {
    await expect(this.pageTitle).toBeVisible();
    await expect(this.pageSubtitle).toBeVisible();
    await expect(this.userIdInput).toBeVisible();
    await expect(this.startChattingButton).toBeVisible();
  }

  /**
   * Enter user ID
   */
  async enterUserId(userId: string): Promise<void> {
    await this.fillInput(this.userIdInput, userId);
  }

  /**
   * Click start chatting button
   */
  async clickStartChatting(): Promise<void> {
    await this.clickElement(this.startChattingButton);
  }

  /**
   * Perform login with user ID
   */
  async login(userId: string): Promise<void> {
    await this.enterUserId(userId);
    await this.clickStartChatting();
  }

  /**
   * Verify browser information is collected
   */
  async verifyBrowserInfoCollected(): Promise<void> {
    await expect(this.browserInfoSection).toBeVisible();
    await expect(this.browserName).toBeVisible();
    await expect(this.deviceInfo).toBeVisible();
    await expect(this.languageInfo).toBeVisible();
    await expect(this.timezoneInfo).toBeVisible();
  }

  /**
   * Get browser information
   */
  async getBrowserInfo(): Promise<{
    browser: string;
    device: string;
    language: string;
    timezone: string;
  }> {
    await this.verifyBrowserInfoCollected();
    
    const browserText = await this.getElementText(this.browserName);
    const deviceText = await this.getElementText(this.deviceInfo);
    const languageText = await this.getElementText(this.languageInfo);
    const timezoneText = await this.getElementText(this.timezoneInfo);

    return {
      browser: browserText,
      device: deviceText,
      language: languageText,
      timezone: timezoneText
    };
  }

  /**
   * Verify validation message appears
   */
  async verifyValidationMessage(expectedMessage: string): Promise<void> {
    await expect(this.validationMessage).toBeVisible();
    await expect(this.validationMessage).toContainText(expectedMessage);
  }

  /**
   * Verify validation message does not appear
   */
  async verifyNoValidationMessage(): Promise<void> {
    await expect(this.validationMessage).not.toBeVisible();
  }

  /**
   * Test invalid user ID format
   */
  async testInvalidUserIdFormat(invalidUserId: string): Promise<void> {
    await this.enterUserId(invalidUserId);
    await this.clickStartChatting();
    // Should remain on login page
    await expect(this.pageTitle).toBeVisible();
  }

  /**
   * Test empty user ID
   */
  async testEmptyUserId(): Promise<void> {
    await this.enterUserId('');
    await this.clickStartChatting();
    // Should remain on login page
    await expect(this.pageTitle).toBeVisible();
  }

  /**
   * Test user ID length validation
   */
  async testUserIdLength(userId: string, shouldShowError: boolean = false): Promise<void> {
    await this.enterUserId(userId);
    await this.clickStartChatting();
    
    if (shouldShowError) {
      await this.verifyValidationMessage('User ID must be between 2 and 50 characters');
    }
  }

  /**
   * Clear user ID field
   */
  async clearUserId(): Promise<void> {
    await this.userIdInput.clear();
  }

  /**
   * Get user ID value
   */
  async getUserIdValue(): Promise<string> {
    return await this.userIdInput.inputValue();
  }

  /**
   * Check if start chatting button is enabled
   */
  async isStartChattingEnabled(): Promise<boolean> {
    return await this.startChattingButton.isEnabled();
  }

  /**
   * Verify page title
   */
  async verifyPageTitle(expectedTitle: string): Promise<void> {
    await expect(this.page).toHaveTitle(expectedTitle);
  }
}