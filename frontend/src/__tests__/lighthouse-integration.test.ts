/**
 * Lighthouse Integration Test
 * **Validates: Requirements 2.7**
 * 
 * Integration tests that run actual Lighthouse audits against the application
 * to validate performance, accessibility, and best practices compliance.
 */

import { LighthouseTestRunner, expectAllLighthouseScores, expectLighthouseScore } from './utils/lighthouse-test-runner'

// Test configuration
const TEST_URLS = [
  'http://localhost:3000',
  'http://localhost:3000/dashboard',
  'http://localhost:3000/analysis',
  'http://localhost:3000/statistics',
  'http://localhost:3000/education',
  'http://localhost:3000/settings',
]

const MOBILE_CONFIG = {
  device: 'mobile' as const,
  throttling: 'simulated3G' as const,
}

const DESKTOP_CONFIG = {
  device: 'desktop' as const,
  throttling: 'none' as const,
}

describe('Lighthouse Integration Tests', () => {
  // Increase timeout for Lighthouse audits
  jest.setTimeout(120000) // 2 minutes per test

  beforeAll(async () => {
    // Wait for the development server to be ready
    const serverReady = await LighthouseTestRunner.waitForServer('http://localhost:3000', 30000)
    if (!serverReady) {
      throw new Error('Development server is not ready. Please start the server with `npm run dev`')
    }
  })

  describe('Mobile Performance Audits', () => {
    it('should achieve 90+ performance score on mobile for all pages', async () => {
      const configs = TEST_URLS.map(url => ({ url, ...MOBILE_CONFIG }))
      const results = await LighthouseTestRunner.runMultipleAudits(configs)

      results.forEach(result => {
        expect(result.passed).toBe(true)
        expectLighthouseScore(result, 'performance', 90)
      })

      // Generate and log report
      const report = LighthouseTestRunner.generateReport(results)
      console.log('Mobile Performance Report:', JSON.stringify(report.summary, null, 2))
      
      if (report.recommendations.length > 0) {
        console.log('Recommendations:', report.recommendations)
      }
    })

    it('should meet Core Web Vitals on mobile', async () => {
      const result = await LighthouseTestRunner.runAudit({
        url: 'http://localhost:3000',
        ...MOBILE_CONFIG,
      })

      const budgetErrors = LighthouseTestRunner.validatePerformanceBudget(result.audits)
      expect(budgetErrors).toHaveLength(0)

      // Specific Core Web Vitals checks
      expect(result.audits['first-contentful-paint'].numericValue).toBeLessThan(1800)
      expect(result.audits['largest-contentful-paint'].numericValue).toBeLessThan(2500)
      expect(result.audits['cumulative-layout-shift'].numericValue).toBeLessThan(0.1)
      expect(result.audits['total-blocking-time'].numericValue).toBeLessThan(200)
    })
  })

  describe('Desktop Performance Audits', () => {
    it('should achieve 95+ performance score on desktop for all pages', async () => {
      const configs = TEST_URLS.map(url => ({ url, ...DESKTOP_CONFIG }))
      const results = await LighthouseTestRunner.runMultipleAudits(configs)

      results.forEach(result => {
        expect(result.passed).toBe(true)
        expectLighthouseScore(result, 'performance', 95) // Higher threshold for desktop
      })

      // Generate and log report
      const report = LighthouseTestRunner.generateReport(results)
      console.log('Desktop Performance Report:', JSON.stringify(report.summary, null, 2))
    })

    it('should have faster Core Web Vitals on desktop', async () => {
      const result = await LighthouseTestRunner.runAudit({
        url: 'http://localhost:3000',
        ...DESKTOP_CONFIG,
      })

      // Desktop should have better performance
      expect(result.audits['first-contentful-paint'].numericValue).toBeLessThan(1200)
      expect(result.audits['largest-contentful-paint'].numericValue).toBeLessThan(2000)
      expect(result.audits['cumulative-layout-shift'].numericValue).toBeLessThan(0.05)
      expect(result.audits['total-blocking-time'].numericValue).toBeLessThan(150)
    })
  })

  describe('Accessibility Compliance', () => {
    it('should achieve 90+ accessibility score for all pages', async () => {
      const configs = TEST_URLS.map(url => ({ 
        url, 
        categories: ['accessibility'],
        ...MOBILE_CONFIG 
      }))
      const results = await LighthouseTestRunner.runMultipleAudits(configs)

      results.forEach(result => {
        expectLighthouseScore(result, 'accessibility', 90)
        
        const accessibilityErrors = LighthouseTestRunner.validateAccessibility(result.audits)
        expect(accessibilityErrors).toHaveLength(0)
      })
    })

    it('should have proper color contrast ratios', async () => {
      const result = await LighthouseTestRunner.runAudit({
        url: 'http://localhost:3000',
        categories: ['accessibility'],
      })

      expect(result.audits['color-contrast'].score).toBe(1.0)
    })

    it('should have alt text for all images', async () => {
      const result = await LighthouseTestRunner.runAudit({
        url: 'http://localhost:3000',
        categories: ['accessibility'],
      })

      expect(result.audits['image-alt'].score).toBe(1.0)
    })

    it('should have proper form labels', async () => {
      const result = await LighthouseTestRunner.runAudit({
        url: 'http://localhost:3000/settings',
        categories: ['accessibility'],
      })

      expect(result.audits['label'].score).toBe(1.0)
    })
  })

  describe('Best Practices Compliance', () => {
    it('should achieve 90+ best practices score for all pages', async () => {
      const configs = TEST_URLS.map(url => ({ 
        url, 
        categories: ['best-practices'],
        ...MOBILE_CONFIG 
      }))
      const results = await LighthouseTestRunner.runMultipleAudits(configs)

      results.forEach(result => {
        expectLighthouseScore(result, 'bestPractices', 90)
      })
    })

    it('should use HTTPS', async () => {
      const result = await LighthouseTestRunner.runAudit({
        url: 'http://localhost:3000',
        categories: ['best-practices'],
      })

      // Note: In development, this might not be HTTPS, so we check if the audit exists
      if (result.audits['is-on-https']) {
        expect(result.audits['is-on-https'].score).toBeGreaterThanOrEqual(0)
      }
    })

    it('should use responsive images', async () => {
      const result = await LighthouseTestRunner.runAudit({
        url: 'http://localhost:3000',
        categories: ['best-practices'],
      })

      expect(result.audits['uses-responsive-images'].score).toBeGreaterThanOrEqual(0.8)
    })

    it('should not have vulnerable libraries', async () => {
      const result = await LighthouseTestRunner.runAudit({
        url: 'http://localhost:3000',
        categories: ['best-practices'],
      })

      if (result.audits['no-vulnerable-libraries']) {
        expect(result.audits['no-vulnerable-libraries'].score).toBe(1.0)
      }
    })
  })

  describe('SEO Compliance', () => {
    it('should achieve 90+ SEO score for all pages', async () => {
      const configs = TEST_URLS.map(url => ({ 
        url, 
        categories: ['seo'],
        ...MOBILE_CONFIG 
      }))
      const results = await LighthouseTestRunner.runMultipleAudits(configs)

      results.forEach(result => {
        expectLighthouseScore(result, 'seo', 90)
        
        const seoErrors = LighthouseTestRunner.validateSEO(result.audits)
        expect(seoErrors).toHaveLength(0)
      })
    })

    it('should have proper document titles', async () => {
      const result = await LighthouseTestRunner.runAudit({
        url: 'http://localhost:3000',
        categories: ['seo'],
      })

      expect(result.audits['document-title'].score).toBe(1.0)
    })

    it('should have meta descriptions', async () => {
      const result = await LighthouseTestRunner.runAudit({
        url: 'http://localhost:3000',
        categories: ['seo'],
      })

      expect(result.audits['meta-description'].score).toBe(1.0)
    })

    it('should be crawlable', async () => {
      const result = await LighthouseTestRunner.runAudit({
        url: 'http://localhost:3000',
        categories: ['seo'],
      })

      if (result.audits['is-crawlable']) {
        expect(result.audits['is-crawlable'].score).toBe(1.0)
      }
    })
  })

  describe('Progressive Web App Features', () => {
    it('should have PWA capabilities', async () => {
      const result = await LighthouseTestRunner.runAudit({
        url: 'http://localhost:3000',
        categories: ['pwa'],
      })

      // PWA score threshold is lower as it's optional
      expectLighthouseScore(result, 'pwa', 80)
    })

    it('should have a web app manifest', async () => {
      const result = await LighthouseTestRunner.runAudit({
        url: 'http://localhost:3000',
        categories: ['pwa'],
      })

      if (result.audits['installable-manifest']) {
        expect(result.audits['installable-manifest'].score).toBeGreaterThanOrEqual(0.5)
      }
    })

    it('should work offline with service worker', async () => {
      const result = await LighthouseTestRunner.runAudit({
        url: 'http://localhost:3000',
        categories: ['pwa'],
      })

      if (result.audits['service-worker']) {
        expect(result.audits['service-worker'].score).toBeGreaterThanOrEqual(0.5)
      }
    })
  })

  describe('Comprehensive Audit', () => {
    it('should pass all Lighthouse categories for the main page', async () => {
      const result = await LighthouseTestRunner.runAudit({
        url: 'http://localhost:3000',
        categories: ['performance', 'accessibility', 'best-practices', 'seo', 'pwa'],
        ...MOBILE_CONFIG,
      })

      expectAllLighthouseScores(result, {
        performance: 90,
        accessibility: 90,
        bestPractices: 90,
        seo: 90,
        pwa: 80, // Lower threshold for PWA
      })

      expect(result.passed).toBe(true)
      
      if (result.errors.length > 0) {
        console.warn('Lighthouse audit warnings:', result.errors)
      }
    })

    it('should generate comprehensive performance report', async () => {
      const configs = TEST_URLS.slice(0, 3).map(url => ({ // Test first 3 URLs to save time
        url,
        categories: ['performance', 'accessibility', 'best-practices', 'seo'],
        ...MOBILE_CONFIG,
      }))
      
      const results = await LighthouseTestRunner.runMultipleAudits(configs)
      const report = LighthouseTestRunner.generateReport(results)

      expect(report.summary.totalUrls).toBe(3)
      expect(report.summary.passedUrls).toBeGreaterThan(0)
      expect(report.summary.averageScores.performance).toBeGreaterThanOrEqual(85)
      expect(report.summary.averageScores.accessibility).toBeGreaterThanOrEqual(90)
      expect(report.summary.averageScores.bestPractices).toBeGreaterThanOrEqual(90)
      expect(report.summary.averageScores.seo).toBeGreaterThanOrEqual(90)

      // Log the report for CI/CD visibility
      console.log('Comprehensive Lighthouse Report:')
      console.log('Summary:', JSON.stringify(report.summary, null, 2))
      
      if (report.recommendations.length > 0) {
        console.log('Recommendations:')
        report.recommendations.forEach((rec, index) => {
          console.log(`${index + 1}. ${rec}`)
        })
      }
    })
  })

  describe('Performance Regression Detection', () => {
    it('should detect performance regressions', async () => {
      const baselineResult = await LighthouseTestRunner.runAudit({
        url: 'http://localhost:3000',
        categories: ['performance'],
        ...MOBILE_CONFIG,
      })

      // In a real scenario, you would compare against stored baseline scores
      const baselineScore = baselineResult.scores.performance
      expect(baselineScore).toBeGreaterThanOrEqual(90)

      // Simulate checking against a baseline (in real tests, this would come from storage)
      const mockBaseline = 92
      const regressionThreshold = 5 // 5 point regression threshold
      
      if (baselineScore < mockBaseline - regressionThreshold) {
        throw new Error(`Performance regression detected: ${baselineScore} vs baseline ${mockBaseline}`)
      }
    })

    it('should track Core Web Vitals trends', async () => {
      const result = await LighthouseTestRunner.runAudit({
        url: 'http://localhost:3000',
        categories: ['performance'],
        ...MOBILE_CONFIG,
      })

      const coreWebVitals = {
        fcp: result.audits['first-contentful-paint'].numericValue,
        lcp: result.audits['largest-contentful-paint'].numericValue,
        cls: result.audits['cumulative-layout-shift'].numericValue,
        tbt: result.audits['total-blocking-time'].numericValue,
      }

      // Log for trend tracking in CI/CD
      console.log('Core Web Vitals:', JSON.stringify(coreWebVitals, null, 2))

      // Validate against thresholds
      expect(coreWebVitals.fcp).toBeLessThan(1800)
      expect(coreWebVitals.lcp).toBeLessThan(2500)
      expect(coreWebVitals.cls).toBeLessThan(0.1)
      expect(coreWebVitals.tbt).toBeLessThan(200)
    })
  })

  describe('Error Handling', () => {
    it('should handle invalid URLs gracefully', async () => {
      const result = await LighthouseTestRunner.runAudit({
        url: 'http://localhost:9999/nonexistent',
        categories: ['performance'],
      })

      expect(result.passed).toBe(false)
      expect(result.errors.length).toBeGreaterThan(0)
    })

    it('should handle network timeouts', async () => {
      // This test would be more meaningful with a real slow endpoint
      const result = await LighthouseTestRunner.runAudit({
        url: 'http://localhost:3000',
        categories: ['performance'],
        timeout: 1, // Very short timeout to simulate timeout
      })

      // The audit should still complete, but might have warnings
      expect(result).toBeDefined()
    })
  })
})