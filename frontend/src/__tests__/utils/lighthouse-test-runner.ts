/**
 * Lighthouse Test Runner Utility
 * Provides utilities for running Lighthouse audits in tests and CI/CD
 */

import lighthouse from 'lighthouse'
import chromeLauncher from 'chrome-launcher'

export interface LighthouseConfig {
  url: string
  categories?: string[]
  device?: 'mobile' | 'desktop'
  throttling?: 'simulated3G' | 'applied3G' | 'none'
  timeout?: number
}

export interface LighthouseScores {
  performance: number
  accessibility: number
  bestPractices: number
  seo: number
  pwa: number
}

export interface LighthouseAuditResult {
  url: string
  scores: LighthouseScores
  audits: Record<string, any>
  passed: boolean
  errors: string[]
}

export class LighthouseTestRunner {
  private static readonly DEFAULT_THRESHOLDS: LighthouseScores = {
    performance: 90,
    accessibility: 90,
    bestPractices: 90,
    seo: 90,
    pwa: 80,
  }

  private static readonly CRITICAL_AUDITS = {
    performance: [
      'first-contentful-paint',
      'largest-contentful-paint',
      'cumulative-layout-shift',
      'total-blocking-time',
      'interactive',
      'speed-index',
    ],
    accessibility: [
      'color-contrast',
      'image-alt',
      'label',
      'link-name',
      'button-name',
    ],
    bestPractices: [
      'is-on-https',
      'uses-responsive-images',
      'efficient-animated-content',
      'no-vulnerable-libraries',
    ],
    seo: [
      'document-title',
      'meta-description',
      'http-status-code',
      'crawlable-anchors',
    ],
  }

  /**
   * Run Lighthouse audit for a single URL
   */
  static async runAudit(config: LighthouseConfig): Promise<LighthouseAuditResult> {
    const chrome = await chromeLauncher.launch({
      chromeFlags: ['--headless', '--no-sandbox', '--disable-dev-shm-usage'],
    })

    try {
      const options = {
        logLevel: 'info' as const,
        output: 'json' as const,
        onlyCategories: config.categories || ['performance', 'accessibility', 'best-practices', 'seo', 'pwa'],
        port: chrome.port,
        throttling: config.throttling || 'simulated3G',
        emulatedFormFactor: config.device || 'mobile',
      }

      const runnerResult = await lighthouse(config.url, options)
      
      if (!runnerResult || !runnerResult.lhr) {
        throw new Error('Failed to get Lighthouse results')
      }

      const { lhr } = runnerResult
      const scores: LighthouseScores = {
        performance: Math.round((lhr.categories.performance?.score || 0) * 100),
        accessibility: Math.round((lhr.categories.accessibility?.score || 0) * 100),
        bestPractices: Math.round((lhr.categories['best-practices']?.score || 0) * 100),
        seo: Math.round((lhr.categories.seo?.score || 0) * 100),
        pwa: Math.round((lhr.categories.pwa?.score || 0) * 100),
      }

      const errors = this.validateScores(scores)
      const auditErrors = this.validateCriticalAudits(lhr.audits)
      
      return {
        url: config.url,
        scores,
        audits: lhr.audits,
        passed: errors.length === 0 && auditErrors.length === 0,
        errors: [...errors, ...auditErrors],
      }
    } finally {
      await chrome.kill()
    }
  }

  /**
   * Run Lighthouse audits for multiple URLs
   */
  static async runMultipleAudits(configs: LighthouseConfig[]): Promise<LighthouseAuditResult[]> {
    const results: LighthouseAuditResult[] = []
    
    for (const config of configs) {
      try {
        const result = await this.runAudit(config)
        results.push(result)
      } catch (error) {
        results.push({
          url: config.url,
          scores: { performance: 0, accessibility: 0, bestPractices: 0, seo: 0, pwa: 0 },
          audits: {},
          passed: false,
          errors: [`Failed to audit ${config.url}: ${error.message}`],
        })
      }
    }
    
    return results
  }

  /**
   * Validate scores against thresholds
   */
  private static validateScores(scores: LighthouseScores, thresholds = this.DEFAULT_THRESHOLDS): string[] {
    const errors: string[] = []
    
    Object.entries(thresholds).forEach(([category, threshold]) => {
      const score = scores[category as keyof LighthouseScores]
      if (score < threshold) {
        errors.push(`${category} score ${score} is below threshold ${threshold}`)
      }
    })
    
    return errors
  }

  /**
   * Validate critical audits
   */
  private static validateCriticalAudits(audits: Record<string, any>): string[] {
    const errors: string[] = []
    
    Object.entries(this.CRITICAL_AUDITS).forEach(([category, auditNames]) => {
      auditNames.forEach(auditName => {
        const audit = audits[auditName]
        if (!audit) {
          errors.push(`Missing critical audit: ${auditName}`)
          return
        }
        
        // Check if audit passed (score of 1.0 or null for informational audits)
        if (audit.score !== null && audit.score < 0.9) {
          errors.push(`Critical audit failed: ${auditName} (score: ${audit.score})`)
        }
      })
    })
    
    return errors
  }

  /**
   * Generate performance budget validation
   */
  static validatePerformanceBudget(audits: Record<string, any>): string[] {
    const errors: string[] = []
    
    const budgets = {
      'first-contentful-paint': 1800, // 1.8s
      'largest-contentful-paint': 2500, // 2.5s
      'speed-index': 3000, // 3s
      'interactive': 3800, // 3.8s
      'total-blocking-time': 200, // 200ms
      'cumulative-layout-shift': 0.1, // 0.1
    }
    
    Object.entries(budgets).forEach(([auditName, threshold]) => {
      const audit = audits[auditName]
      if (audit && audit.numericValue > threshold) {
        errors.push(`Performance budget exceeded: ${auditName} (${audit.numericValue} > ${threshold})`)
      }
    })
    
    return errors
  }

  /**
   * Generate accessibility validation
   */
  static validateAccessibility(audits: Record<string, any>): string[] {
    const errors: string[] = []
    
    const requiredAudits = [
      'color-contrast',
      'image-alt',
      'label',
      'link-name',
      'button-name',
      'document-title',
      'html-has-lang',
      'meta-viewport',
    ]
    
    requiredAudits.forEach(auditName => {
      const audit = audits[auditName]
      if (!audit || audit.score < 1.0) {
        errors.push(`Accessibility requirement failed: ${auditName}`)
      }
    })
    
    return errors
  }

  /**
   * Generate SEO validation
   */
  static validateSEO(audits: Record<string, any>): string[] {
    const errors: string[] = []
    
    const requiredAudits = [
      'document-title',
      'meta-description',
      'http-status-code',
      'crawlable-anchors',
      'is-crawlable',
    ]
    
    requiredAudits.forEach(auditName => {
      const audit = audits[auditName]
      if (!audit || audit.score < 1.0) {
        errors.push(`SEO requirement failed: ${auditName}`)
      }
    })
    
    return errors
  }

  /**
   * Generate comprehensive report
   */
  static generateReport(results: LighthouseAuditResult[]): {
    summary: {
      totalUrls: number
      passedUrls: number
      failedUrls: number
      averageScores: LighthouseScores
    }
    details: LighthouseAuditResult[]
    recommendations: string[]
  } {
    const totalUrls = results.length
    const passedUrls = results.filter(r => r.passed).length
    const failedUrls = totalUrls - passedUrls
    
    // Calculate average scores
    const averageScores: LighthouseScores = {
      performance: Math.round(results.reduce((sum, r) => sum + r.scores.performance, 0) / totalUrls),
      accessibility: Math.round(results.reduce((sum, r) => sum + r.scores.accessibility, 0) / totalUrls),
      bestPractices: Math.round(results.reduce((sum, r) => sum + r.scores.bestPractices, 0) / totalUrls),
      seo: Math.round(results.reduce((sum, r) => sum + r.scores.seo, 0) / totalUrls),
      pwa: Math.round(results.reduce((sum, r) => sum + r.scores.pwa, 0) / totalUrls),
    }
    
    // Generate recommendations
    const recommendations = this.generateRecommendations(results)
    
    return {
      summary: {
        totalUrls,
        passedUrls,
        failedUrls,
        averageScores,
      },
      details: results,
      recommendations,
    }
  }

  /**
   * Generate recommendations based on audit results
   */
  private static generateRecommendations(results: LighthouseAuditResult[]): string[] {
    const recommendations: string[] = []
    const commonIssues: Record<string, number> = {}
    
    // Count common issues
    results.forEach(result => {
      result.errors.forEach(error => {
        commonIssues[error] = (commonIssues[error] || 0) + 1
      })
    })
    
    // Generate recommendations for most common issues
    Object.entries(commonIssues)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10) // Top 10 issues
      .forEach(([issue, count]) => {
        if (count > 1) {
          recommendations.push(`Fix common issue affecting ${count} pages: ${issue}`)
        }
      })
    
    // Add general recommendations
    const avgPerformance = results.reduce((sum, r) => sum + r.scores.performance, 0) / results.length
    if (avgPerformance < 90) {
      recommendations.push('Consider implementing performance optimizations: image compression, code splitting, caching')
    }
    
    const avgAccessibility = results.reduce((sum, r) => sum + r.scores.accessibility, 0) / results.length
    if (avgAccessibility < 90) {
      recommendations.push('Improve accessibility: add alt text, improve color contrast, ensure keyboard navigation')
    }
    
    return recommendations
  }

  /**
   * Wait for server to be ready
   */
  static async waitForServer(url: string, timeout = 30000): Promise<boolean> {
    const startTime = Date.now()
    
    while (Date.now() - startTime < timeout) {
      try {
        const response = await fetch(url)
        if (response.ok) {
          return true
        }
      } catch (error) {
        // Server not ready yet
      }
      
      await new Promise(resolve => setTimeout(resolve, 1000))
    }
    
    return false
  }
}

/**
 * Jest matcher for Lighthouse scores
 */
export function expectLighthouseScore(result: LighthouseAuditResult, category: keyof LighthouseScores, threshold: number) {
  const score = result.scores[category]
  
  if (score < threshold) {
    throw new Error(
      `Expected ${category} score to be >= ${threshold}, but got ${score}\n` +
      `URL: ${result.url}\n` +
      `Errors: ${result.errors.join(', ')}`
    )
  }
  
  return true
}

/**
 * Jest matcher for all Lighthouse scores
 */
export function expectAllLighthouseScores(result: LighthouseAuditResult, thresholds?: Partial<LighthouseScores>) {
  const defaultThresholds = LighthouseTestRunner['DEFAULT_THRESHOLDS']
  const finalThresholds = { ...defaultThresholds, ...thresholds }
  
  Object.entries(finalThresholds).forEach(([category, threshold]) => {
    expectLighthouseScore(result, category as keyof LighthouseScores, threshold)
  })
  
  return true
}