#!/usr/bin/env node

/**
 * Lighthouse audit script for performance monitoring
 * Run with: node scripts/lighthouse-audit.js
 */

const lighthouse = require('lighthouse');
const chromeLauncher = require('chrome-launcher');
const fs = require('fs');
const path = require('path');

const config = {
  extends: 'lighthouse:default',
  settings: {
    onlyAudits: [
      'first-contentful-paint',
      'largest-contentful-paint',
      'first-meaningful-paint',
      'speed-index',
      'interactive',
      'cumulative-layout-shift',
      'total-blocking-time',
      'accessibility',
      'best-practices',
      'seo',
      'pwa',
    ],
  },
};

const urls = [
  'http://localhost:3000',
  'http://localhost:3000/dashboard',
  'http://localhost:3000/analysis',
  'http://localhost:3000/statistics',
  'http://localhost:3000/education',
];

async function runLighthouse(url) {
  const chrome = await chromeLauncher.launch({ chromeFlags: ['--headless'] });
  const options = {
    logLevel: 'info',
    output: 'json',
    onlyCategories: ['performance', 'accessibility', 'best-practices', 'seo', 'pwa'],
    port: chrome.port,
  };

  const runnerResult = await lighthouse(url, options, config);
  await chrome.kill();

  return runnerResult;
}

async function auditSite() {
  console.log('🚀 Starting Lighthouse audit...\n');
  
  const results = [];
  
  for (const url of urls) {
    console.log(`📊 Auditing: ${url}`);
    
    try {
      const result = await runLighthouse(url);
      const { lhr } = result;
      
      const scores = {
        url,
        performance: Math.round(lhr.categories.performance.score * 100),
        accessibility: Math.round(lhr.categories.accessibility.score * 100),
        bestPractices: Math.round(lhr.categories['best-practices'].score * 100),
        seo: Math.round(lhr.categories.seo.score * 100),
        pwa: Math.round(lhr.categories.pwa.score * 100),
      };
      
      results.push(scores);
      
      console.log(`  Performance: ${scores.performance}/100`);
      console.log(`  Accessibility: ${scores.accessibility}/100`);
      console.log(`  Best Practices: ${scores.bestPractices}/100`);
      console.log(`  SEO: ${scores.seo}/100`);
      console.log(`  PWA: ${scores.pwa}/100\n`);
      
      // Save detailed report
      const reportPath = path.join(__dirname, '..', 'lighthouse-reports', `${url.replace(/[^a-zA-Z0-9]/g, '_')}.json`);
      fs.mkdirSync(path.dirname(reportPath), { recursive: true });
      fs.writeFileSync(reportPath, JSON.stringify(lhr, null, 2));
      
    } catch (error) {
      console.error(`❌ Error auditing ${url}:`, error.message);
    }
  }
  
  // Generate summary report
  const summary = {
    timestamp: new Date().toISOString(),
    results,
    averages: {
      performance: Math.round(results.reduce((sum, r) => sum + r.performance, 0) / results.length),
      accessibility: Math.round(results.reduce((sum, r) => sum + r.accessibility, 0) / results.length),
      bestPractices: Math.round(results.reduce((sum, r) => sum + r.bestPractices, 0) / results.length),
      seo: Math.round(results.reduce((sum, r) => sum + r.seo, 0) / results.length),
      pwa: Math.round(results.reduce((sum, r) => sum + r.pwa, 0) / results.length),
    },
  };
  
  // Save summary
  const summaryPath = path.join(__dirname, '..', 'lighthouse-reports', 'summary.json');
  fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2));
  
  console.log('📈 Audit Summary:');
  console.log(`  Average Performance: ${summary.averages.performance}/100`);
  console.log(`  Average Accessibility: ${summary.averages.accessibility}/100`);
  console.log(`  Average Best Practices: ${summary.averages.bestPractices}/100`);
  console.log(`  Average SEO: ${summary.averages.seo}/100`);
  console.log(`  Average PWA: ${summary.averages.pwa}/100`);
  
  // Check if targets are met
  const targets = {
    performance: 90,
    accessibility: 90,
    bestPractices: 90,
    seo: 90,
    pwa: 80,
  };
  
  const failed = [];
  Object.entries(targets).forEach(([category, target]) => {
    if (summary.averages[category] < target) {
      failed.push(`${category}: ${summary.averages[category]}/100 (target: ${target})`);
    }
  });
  
  if (failed.length > 0) {
    console.log('\n❌ Failed to meet targets:');
    failed.forEach(failure => console.log(`  ${failure}`));
    process.exit(1);
  } else {
    console.log('\n✅ All Lighthouse targets met!');
  }
}

// Run the audit
auditSite().catch(console.error);