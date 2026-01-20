'use client'

import { useEffect } from 'react'
import { PerformanceMonitor } from '@/lib/performance'

interface WebVitalsMetric {
  id: string
  name: string
  value: number
  delta: number
  entries: PerformanceEntry[]
}

export function PerformanceMonitorComponent() {
  useEffect(() => {
    // Initialize performance monitoring
    const monitor = PerformanceMonitor.getInstance()
    
    // Monitor Core Web Vitals
    if (typeof window !== 'undefined' && 'web-vitals' in window) {
      import('web-vitals').then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
        const reportMetric = (metric: WebVitalsMetric) => {
          // Log to console in development
          if (process.env.NODE_ENV === 'development') {
            console.log(`${metric.name}: ${metric.value}`)
          }
          
          // Send to analytics in production
          if (process.env.NODE_ENV === 'production') {
            // Send to your analytics service
            fetch('/api/v1/monitoring/web-vitals', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                name: metric.name,
                value: metric.value,
                delta: metric.delta,
                id: metric.id,
                timestamp: Date.now(),
                url: window.location.href,
              }),
            }).catch(console.error)
          }
        }

        getCLS(reportMetric)
        getFID(reportMetric)
        getFCP(reportMetric)
        getLCP(reportMetric)
        getTTFB(reportMetric)
      }).catch(console.error)
    }

    // Monitor long tasks
    if ('PerformanceObserver' in window) {
      try {
        const longTaskObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.duration > 50) {
              console.warn(`Long task detected: ${entry.duration}ms`)
              
              // Report long tasks in production
              if (process.env.NODE_ENV === 'production') {
                fetch('/api/v1/monitoring/long-tasks', {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json',
                  },
                  body: JSON.stringify({
                    duration: entry.duration,
                    startTime: entry.startTime,
                    name: entry.name,
                    timestamp: Date.now(),
                    url: window.location.href,
                  }),
                }).catch(console.error)
              }
            }
          }
        })

        longTaskObserver.observe({ entryTypes: ['longtask'] })

        return () => {
          longTaskObserver.disconnect()
        }
      } catch (error) {
        console.warn('Long task monitoring not supported:', error)
      }
    }

    // Monitor memory usage (if available)
    if ('memory' in performance) {
      const checkMemory = () => {
        const memory = (performance as any).memory
        if (memory) {
          const memoryInfo = {
            usedJSHeapSize: memory.usedJSHeapSize,
            totalJSHeapSize: memory.totalJSHeapSize,
            jsHeapSizeLimit: memory.jsHeapSizeLimit,
          }
          
          // Warn if memory usage is high
          const usagePercent = (memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100
          if (usagePercent > 80) {
            console.warn(`High memory usage: ${usagePercent.toFixed(1)}%`)
          }
          
          // Log memory info in development
          if (process.env.NODE_ENV === 'development') {
            console.log('Memory usage:', memoryInfo)
          }
        }
      }

      // Check memory every 30 seconds
      const memoryInterval = setInterval(checkMemory, 30000)
      
      return () => {
        clearInterval(memoryInterval)
      }
    }
  }, [])

  // This component doesn't render anything
  return null
}

// Hook for measuring component render times
export function usePerformanceMeasure(componentName: string) {
  useEffect(() => {
    const monitor = PerformanceMonitor.getInstance()
    monitor.startTiming(`${componentName}_mount`)
    
    return () => {
      monitor.endTiming(`${componentName}_mount`)
    }
  }, [componentName])
}

// Hook for measuring API call performance
export function useApiPerformance() {
  const measureApiCall = (endpoint: string, startTime: number, endTime: number, success: boolean) => {
    const duration = endTime - startTime
    
    // Log slow API calls
    if (duration > 1000) {
      console.warn(`Slow API call: ${endpoint} took ${duration}ms`)
    }
    
    // Send metrics to monitoring endpoint
    if (process.env.NODE_ENV === 'production') {
      fetch('/api/v1/monitoring/api-performance', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          endpoint,
          duration,
          success,
          timestamp: Date.now(),
        }),
      }).catch(console.error)
    }
  }

  return { measureApiCall }
}