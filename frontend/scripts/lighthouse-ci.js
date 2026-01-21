#!/usr/bin/env node

/**
 * Lighthouse CI Script
 * Runs Lighthouse audits in CI/CD pipeline and validates performance thresholds
 */

const lighthouse = require('lighthouse')
const chromeLauncher = require('chrome-launcher')
const fs = require('fs')
const path = require('path')

// Configuration
const CONFIG = {
  urls: [
    'http://localhost:3000',
    'http://localhost:3000/dashboard',
    'http://localhost:3000/analysis',
    'http://localhost:3000/statistics',
    'http://localhost:3000/education',
  ],
  thresholds: {
    performance: 90,
    accessibility: 90,
    'best-practices': 90,
    seo: 90,
    pwa: 80,
  },
  budgets: {
    'first-contentful-paint': 1800,
    'largest-contentful-paint': 2500,
    'speed-index': 3000,
    'interactive': 3800,
    'total-blocking-time': 200,
    'cumulative-layout-shift': 0.1,
  },
  outputDir: path.join(__dirname, '..', 'lighthouse-reports'),
  retries: 3,
  timeout: 60000,
}

class LighthouseCI {
  constructor(config = CONFIG) {
    this.config = config
    this.results = []
    this.errors = []
  }

  async run() {
    console.log('🚀 Starting Lighthouse CI audit...\n')
    
    // Ensure output directory exists
    if (!fs.existsSync(this.config.outputDir)) {
      fs.mkdirSync(this.config.outputDir, { recursive: true })
    }

    // Wait for server to be ready
    await this.waitForServer()

    // Run audits for all URLs
    for (const url of this.config.urls) {
      await this.auditUrl(url)
    }

    // Generate reports
    await this.generateReports()

    // Validate results
    const passed = this.validateResults()

    if (passed) {
      console.log('\n✅ All Lighthouse audits passed!')
      process.exit(0)
    } else {
      console.log('\n❌ Some Lighthouse audits failed!')
      process.exit(1)
    }
  }

  async waitForServer(maxAttempts = 30) {
    console.log('⏳ Waiting for server to be ready...')
    
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        const response = await fetch(this.config.urls[0])
        if (response.ok) {
          console.log('✅ Server is ready\n')
          return
        }
      } catch (error) {
        if (attempt === maxAttempts) {
          throw new Error(`Server not ready after ${maxAttempts} attempts`)
        }
        await new Promise(resolve => setTimeout(resolve, 2000))
      }
    }
  }

  async auditUrl(url) {
    console.log(`📊 Auditing: ${url}`)
    
    let lastError
    for (let attempt = 1; attempt <= this.config.retries; attempt++) {
      try {
        const result = await this.runLighthouse(url)
        this.results.push(result)
        this.logResult(result)
        return
      } catch (error) {
        lastError = error
        console.log(`  ⚠️  Attempt ${attempt} failed: ${error.message}`)
        if (attempt < this.config.retries) {
          console.log(`  🔄 Retrying in 5 seconds...`)
          await new Promise(resolve => setTimeout(resolve, 5000))
        }
      }
    }

    // All retries failed
    const failedResult = {
      url,
      scores: { performance: 0, accessibility: 0, 'best-practices': 0, seo: 0, pwa: 0 },
      audits: {},
      error: lastError.message,
    }
    this.results.push(failedResult)
    this.errors.push(`Failed to audit ${url}: ${lastError.message}`)
  }

  async runLighthouse(url) {
    const chrome = await chromeLauncher.launch({
      chromeFlags: ['--headless', '--no-sandbox', '--disable-dev-shm-usage'],
    })

    try {
      const options = {
        logLevel: 'info',
        output: 'json',
        onlyCategories: ['performance', 'accessibility', 'best-practices', 'seo', 'pwa'],
        port: chrome.port,
        throttling: 'simulated3G',
        emulatedFormFactor: 'mobile',
      }

      const runnerResult = await lighthouse(url, options)
      
      if (!runnerResult || !runnerResult.lhr) {
        throw new Error('Failed to get Lighthouse results')
      }

      const { lhr } = runnerResult
      
      // Extract scores
      const scores = {}
      Object.keys(this.config.thresholds).forEach(category => {
        scores[category] = Math.round((lhr.categories[category]?.score || 0) * 100)
      })

      // Save detailed report
      const reportPath = path.join(
        this.config.outputDir,
        `${url.replace(/[^a-zA-Z0-9]/g, '_')}_${Date.now()}.json`
      )
      fs.writeFileSync(reportPath, JSON.stringify(lhr, null, 2))

      return {
        url,
        scores,
        audits: lhr.audits,
        reportPath,
      }
    } finally {
      await chrome.kill()
    }
  }

  logResult(result) {
    Object.entries(result.scores).forEach(([category, score]) => {
      const threshold = this.config.thresholds[category]
      const status = score >= threshold ? '✅' : '❌'
      console.log(`  ${status} ${category}: ${score}/100 (threshold: ${threshold})`)
    })
    console.log()
  }

  async generateReports() {
    console.log('📈 Generating reports...\n')

    // Calculate averages
    const averages = {}
    Object.keys(this.config.thresholds).forEach(category => {
      const validResults = this.results.filter(r => !r.error)
      const sum = validResults.reduce((acc, r) => acc + r.scores[category], 0)
      averages[category] = validResults.length > 0 ? Math.round(sum / validResults.length) : 0
    })

    // Generate summary
    const summary = {
      timestamp: new Date().toISOString(),
      totalUrls: this.config.urls.length,
      successfulAudits: this.results.filter(r => !r.error).length,
      failedAudits: this.results.filter(r => r.error).length,
      averageScores: averages,
      thresholds: this.config.thresholds,
      results: this.results.map(r => ({
        url: r.url,
        scores: r.scores,
        error: r.error,
        passed: this.isResultPassed(r),
      })),
      errors: this.errors,
    }

    // Save summary
    const summaryPath = path.join(this.config.outputDir, 'summary.json')
    fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2))

    // Generate HTML report
    await this.generateHtmlReport(summary)

    // Generate performance budget report
    await this.generateBudgetReport()

    console.log(`📊 Reports saved to: ${this.config.outputDir}`)
    console.log(`📋 Summary: ${summaryPath}`)
  }

  async generateHtmlReport(summary) {
    const html = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lighthouse CI Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f5f5f5; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }
        .metric { background: white; border: 1px solid #ddd; padding: 15px; border-radius: 8px; text-align: center; }
        .metric h3 { margin: 0 0 10px 0; color: #333; }
        .metric .score { font-size: 2em; font-weight: bold; }
        .score.good { color: #0cce6b; }
        .score.average { color: #ffa400; }
        .score.poor { color: #ff4e42; }
        .results { margin-top: 30px; }
        .result { background: white; border: 1px solid #ddd; margin-bottom: 15px; border-radius: 8px; overflow: hidden; }
        .result-header { background: #f8f9fa; padding: 15px; font-weight: bold; }
        .result-scores { padding: 15px; display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
        .result-score { text-align: center; padding: 10px; border-radius: 4px; }
        .passed { background: #d4edda; color: #155724; }
        .failed { background: #f8d7da; color: #721c24; }
        .error { background: #fff3cd; color: #856404; padding: 15px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Lighthouse CI Report</h1>
        <p>Generated on ${new Date(summary.timestamp).toLocaleString()}</p>
        <p>Audited ${summary.totalUrls} URLs • ${summary.successfulAudits} successful • ${summary.failedAudits} failed</p>
    </div>

    <div class="summary">
        ${Object.entries(summary.averageScores).map(([category, score]) => {
          const threshold = this.config.thresholds[category]
          const status = score >= threshold ? 'good' : score >= threshold - 10 ? 'average' : 'poor'
          return `
            <div class="metric">
                <h3>${category.replace('-', ' ').toUpperCase()}</h3>
                <div class="score ${status}">${score}</div>
                <div>Threshold: ${threshold}</div>
            </div>
          `
        }).join('')}
    </div>

    <div class="results">
        <h2>Detailed Results</h2>
        ${summary.results.map(result => `
            <div class="result">
                <div class="result-header">
                    ${result.url} ${result.passed ? '✅' : '❌'}
                </div>
                ${result.error ? `
                    <div class="error">
                        <strong>Error:</strong> ${result.error}
                    </div>
                ` : `
                    <div class="result-scores">
                        ${Object.entries(result.scores).map(([category, score]) => {
                          const threshold = this.config.thresholds[category]
                          const passed = score >= threshold
                          return `
                            <div class="result-score ${passed ? 'passed' : 'failed'}">
                                <div><strong>${category}</strong></div>
                                <div>${score}/100</div>
                            </div>
                          `
                        }).join('')}
                    </div>
                `}
            </div>
        `).join('')}
    </div>

    ${summary.errors.length > 0 ? `
        <div class="results">
            <h2>Errors</h2>
            ${summary.errors.map(error => `<div class="error">${error}</div>`).join('')}
        </div>
    ` : ''}
</body>
</html>
    `

    const htmlPath = path.join(this.config.outputDir, 'report.html')
    fs.writeFileSync(htmlPath, html)
  }

  async generateBudgetReport() {
    const budgetResults = []

    this.results.forEach(result => {
      if (result.error) return

      const budgetViolations = []
      Object.entries(this.config.budgets).forEach(([auditName, threshold]) => {
        const audit = result.audits[auditName]
        if (audit && audit.numericValue > threshold) {
          budgetViolations.push({
            audit: auditName,
            value: audit.numericValue,
            threshold,
            violation: audit.numericValue - threshold,
          })
        }
      })

      budgetResults.push({
        url: result.url,
        violations: budgetViolations,
        passed: budgetViolations.length === 0,
      })
    })

    const budgetReport = {
      timestamp: new Date().toISOString(),
      budgets: this.config.budgets,
      results: budgetResults,
      summary: {
        totalUrls: budgetResults.length,
        passedUrls: budgetResults.filter(r => r.passed).length,
        failedUrls: budgetResults.filter(r => !r.passed).length,
      },
    }

    const budgetPath = path.join(this.config.outputDir, 'budget-report.json')
    fs.writeFileSync(budgetPath, JSON.stringify(budgetReport, null, 2))
  }

  validateResults() {
    let allPassed = true

    console.log('📋 Validation Summary:')
    
    // Check individual results
    this.results.forEach(result => {
      const passed = this.isResultPassed(result)
      if (!passed) allPassed = false
      
      const status = passed ? '✅' : '❌'
      console.log(`  ${status} ${result.url}`)
      
      if (result.error) {
        console.log(`    Error: ${result.error}`)
      } else {
        Object.entries(result.scores).forEach(([category, score]) => {
          const threshold = this.config.thresholds[category]
          if (score < threshold) {
            console.log(`    ❌ ${category}: ${score} < ${threshold}`)
          }
        })
      }
    })

    // Check averages
    console.log('\n📊 Average Scores:')
    const validResults = this.results.filter(r => !r.error)
    if (validResults.length > 0) {
      Object.keys(this.config.thresholds).forEach(category => {
        const sum = validResults.reduce((acc, r) => acc + r.scores[category], 0)
        const average = Math.round(sum / validResults.length)
        const threshold = this.config.thresholds[category]
        const status = average >= threshold ? '✅' : '❌'
        console.log(`  ${status} ${category}: ${average}/100 (threshold: ${threshold})`)
        
        if (average < threshold) allPassed = false
      })
    }

    return allPassed
  }

  isResultPassed(result) {
    if (result.error) return false
    
    return Object.entries(this.config.thresholds).every(([category, threshold]) => {
      return result.scores[category] >= threshold
    })
  }
}

// Run the CI if this script is executed directly
if (require.main === module) {
  const ci = new LighthouseCI()
  ci.run().catch(error => {
    console.error('❌ Lighthouse CI failed:', error)
    process.exit(1)
  })
}

module.exports = LighthouseCI