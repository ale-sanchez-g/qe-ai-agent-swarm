import { Page, expect } from '@playwright/test';

/**
 * Test helper utilities for common test operations
 */
export class TestHelpers {
  
  /**
   * Wait for element with custom timeout
   */
  static async waitForElement(page: Page, selector: string, timeout: number = 10000): Promise<void> {
    await page.waitForSelector(selector, { timeout });
  }

  /**
   * Take screenshot with timestamp
   */
  static async takeScreenshot(page: Page, name: string): Promise<void> {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    await page.screenshot({ 
      path: `test-results/screenshots/${name}_${timestamp}.png`,
      fullPage: true 
    });
  }

  /**
   * Generate unique test identifier
   */
  static generateTestId(): string {
    return `test_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Wait for network to be idle
   */
  static async waitForNetworkIdle(page: Page, timeout: number = 30000): Promise<void> {
    await page.waitForLoadState('networkidle', { timeout });
  }

  /**
   * Check if page contains error
   */
  static async hasPageError(page: Page): Promise<boolean> {
    const errorSelectors = [
      '.error',
      '.alert-danger',
      '[role="alert"]',
      '.text-danger'
    ];

    for (const selector of errorSelectors) {
      const elements = await page.locator(selector).count();
      if (elements > 0) {
        return true;
      }
    }
    return false;
  }

  /**
   * Get console errors from page
   */
  static getConsoleErrors(page: Page): string[] {
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    return errors;
  }

  /**
   * Clear all inputs on page
   */
  static async clearAllInputs(page: Page): Promise<void> {
    const inputs = await page.locator('input[type="text"], textarea').all();
    for (const input of inputs) {
      await input.clear();
    }
  }

  /**
   * Verify page accessibility
   */
  static async verifyPageAccessibility(page: Page): Promise<void> {
    // Check for basic accessibility requirements
    const headings = await page.locator('h1, h2, h3, h4, h5, h6').count();
    expect(headings).toBeGreaterThan(0);

    // Check for alt text on images
    const images = await page.locator('img').all();
    for (const img of images) {
      const alt = await img.getAttribute('alt');
      expect(alt).toBeTruthy();
    }

    // Check for form labels
    const inputs = await page.locator('input').all();
    for (const input of inputs) {
      const id = await input.getAttribute('id');
      const ariaLabel = await input.getAttribute('aria-label');
      const placeholder = await input.getAttribute('placeholder');
      
      // Should have either id with label, aria-label, or placeholder
      expect(id || ariaLabel || placeholder).toBeTruthy();
    }
  }

  /**
   * Simulate slow network
   */
  static async simulateSlowNetwork(page: Page): Promise<void> {
    const client = await page.context().newCDPSession(page);
    await client.send('Network.emulateNetworkConditions', {
      offline: false,
      downloadThroughput: 1024 * 1024, // 1 MB/s
      uploadThroughput: 512 * 1024,    // 512 KB/s
      latency: 100                      // 100ms
    });
  }

  /**
   * Reset network conditions
   */
  static async resetNetwork(page: Page): Promise<void> {
    const client = await page.context().newCDPSession(page);
    await client.send('Network.emulateNetworkConditions', {
      offline: false,
      downloadThroughput: -1,
      uploadThroughput: -1,
      latency: 0
    });
  }

  /**
   * Wait for animation to complete
   */
  static async waitForAnimation(page: Page, duration: number = 500): Promise<void> {
    await page.waitForTimeout(duration);
  }

  /**
   * Check for broken images
   */
  static async checkForBrokenImages(page: Page): Promise<string[]> {
    const brokenImages: string[] = [];
    const images = await page.locator('img').all();
    
    for (const img of images) {
      const src = await img.getAttribute('src');
      if (src) {
        const naturalWidth = await img.evaluate((el: HTMLImageElement) => el.naturalWidth);
        if (naturalWidth === 0) {
          brokenImages.push(src);
        }
      }
    }
    
    return brokenImages;
  }

  /**
   * Verify no JavaScript errors
   */
  static async verifyNoJSErrors(page: Page): Promise<void> {
    const errors = this.getConsoleErrors(page);
    expect(errors).toHaveLength(0);
  }

  /**
   * Get page performance metrics
   */
  static async getPerformanceMetrics(page: Page): Promise<any> {
    return await page.evaluate(() => {
      const perfData = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      return {
        domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
        loadComplete: perfData.loadEventEnd - perfData.loadEventStart,
        firstPaint: performance.getEntriesByType('paint')[0]?.startTime || 0,
        firstContentfulPaint: performance.getEntriesByType('paint')[1]?.startTime || 0
      };
    });
  }

  /**
   * Scroll to element smoothly
   */
  static async scrollToElement(page: Page, selector: string): Promise<void> {
    await page.locator(selector).scrollIntoViewIfNeeded();
    await this.waitForAnimation(page, 300);
  }

  /**
   * Double click on element
   */
  static async doubleClick(page: Page, selector: string): Promise<void> {
    await page.locator(selector).dblclick();
  }

  /**
   * Right click on element
   */
  static async rightClick(page: Page, selector: string): Promise<void> {
    await page.locator(selector).click({ button: 'right' });
  }

  /**
   * Verify element is in viewport
   */
  static async isElementInViewport(page: Page, selector: string): Promise<boolean> {
    return await page.locator(selector).isInViewport();
  }

  /**
   * Get element bounding box
   */
  static async getElementBounds(page: Page, selector: string): Promise<any> {
    return await page.locator(selector).boundingBox();
  }

  /**
   * Verify CSS property value
   */
  static async verifyCSSProperty(page: Page, selector: string, property: string, expectedValue: string): Promise<void> {
    const element = page.locator(selector);
    const actualValue = await element.evaluate((el, prop) => {
      return window.getComputedStyle(el).getPropertyValue(prop);
    }, property);
    expect(actualValue).toBe(expectedValue);
  }
}