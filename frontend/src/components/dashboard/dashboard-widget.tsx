"use client"

import React, { useState, useCallback, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { LoadingSpinner, Skeleton } from "@/components/loading-states"
import { ErrorBoundary } from "@/components/error-boundary"
import { RefreshCw, AlertCircle, Wifi, WifiOff } from "lucide-react"
import { cn } from "@/lib/utils"

interface DashboardWidgetProps {
  id: string
  title: string
  description?: string
  children: React.ReactNode
  loading?: boolean
  error?: Error | null
  onRetry?: () => void
  onRefresh?: () => void
  refreshing?: boolean
  className?: string
  priority?: "high" | "medium" | "low"
  fallbackData?: any
  showOfflineIndicator?: boolean
  autoRetry?: boolean
  maxRetries?: number
  retryDelay?: number
  skeletonRows?: number
}

interface WidgetState {
  hasError: boolean
  error?: Error
  retryCount: number
  lastSuccessfulLoad?: Date
  isOffline: boolean
  autoRetryTimer?: NodeJS.Timeout
  isRetrying: boolean
}

export function DashboardWidget({
  id,
  title,
  description,
  children,
  loading = false,
  error = null,
  onRetry,
  onRefresh,
  refreshing = false,
  className,
  priority = "medium",
  fallbackData,
  showOfflineIndicator = true,
  autoRetry = true,
  maxRetries = 3,
  retryDelay = 1000,
  skeletonRows = 3
}: DashboardWidgetProps) {
  const [widgetState, setWidgetState] = useState<WidgetState>({
    hasError: false,
    retryCount: 0,
    isOffline: false,
    isRetrying: false
  })

  // Monitor online/offline status
  useEffect(() => {
    const handleOnline = () => {
      setWidgetState(prev => ({ ...prev, isOffline: false }))
      // Auto-retry when coming back online if there was an error
      if (widgetState.hasError && autoRetry && onRetry) {
        handleRetry()
      }
    }
    const handleOffline = () => setWidgetState(prev => ({ ...prev, isOffline: true }))

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    // Set initial state
    setWidgetState(prev => ({ ...prev, isOffline: !navigator.onLine }))

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
      // Clear any pending retry timers
      if (widgetState.autoRetryTimer) {
        clearTimeout(widgetState.autoRetryTimer)
      }
    }
  }, [widgetState.hasError, autoRetry, onRetry])

  // Handle error state changes
  useEffect(() => {
    if (error) {
      setWidgetState(prev => ({
        ...prev,
        hasError: true,
        error,
        retryCount: prev.retryCount + 1,
        isRetrying: false
      }))
    } else if (!loading && !error) {
      setWidgetState(prev => ({
        ...prev,
        hasError: false,
        error: undefined,
        lastSuccessfulLoad: new Date(),
        retryCount: 0,
        isRetrying: false
      }))
    }
  }, [error, loading])

  const handleRetry = useCallback(() => {
    if (onRetry && !widgetState.isRetrying) {
      setWidgetState(prev => ({ 
        ...prev, 
        hasError: false, 
        error: undefined,
        isRetrying: true
      }))
      onRetry()
    }
  }, [onRetry, widgetState.isRetrying])

  const handleRefresh = useCallback(() => {
    if (onRefresh) {
      onRefresh()
    }
  }, [onRefresh])

  // Auto-retry logic with exponential backoff
  useEffect(() => {
    if (
      widgetState.hasError && 
      autoRetry && 
      widgetState.retryCount <= maxRetries && 
      !widgetState.isOffline &&
      !widgetState.isRetrying &&
      onRetry
    ) {
      const delay = Math.min(retryDelay * Math.pow(2, widgetState.retryCount - 1), 30000)
      
      const timer = setTimeout(() => {
        console.log(`Auto-retrying widget ${id}, attempt ${widgetState.retryCount}/${maxRetries}`)
        handleRetry()
      }, delay)

      setWidgetState(prev => ({ ...prev, autoRetryTimer: timer }))

      return () => {
        clearTimeout(timer)
        setWidgetState(prev => ({ ...prev, autoRetryTimer: undefined }))
      }
    }
  }, [
    widgetState.hasError, 
    widgetState.retryCount, 
    widgetState.isOffline,
    widgetState.isRetrying,
    autoRetry, 
    maxRetries, 
    retryDelay, 
    onRetry, 
    handleRetry, 
    id
  ])

  const priorityStyles = {
    high: "border-red-200 bg-red-50/30",
    medium: "border-yellow-200 bg-yellow-50/30", 
    low: "border-gray-200 bg-gray-50/30"
  }

  const showFallback = widgetState.hasError && fallbackData && !loading && !widgetState.isRetrying
  const showError = widgetState.hasError && !fallbackData && !loading && !widgetState.isRetrying
  const showLoading = loading || widgetState.isRetrying

  // Enhanced skeleton loading based on widget type
  const renderSkeleton = () => (
    <div className="space-y-3">
      {Array.from({ length: skeletonRows }).map((_, i) => (
        <div key={i} className="space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          {i === 0 && <Skeleton className="h-8 w-1/2" />}
        </div>
      ))}
    </div>
  )

  return (
    <ErrorBoundary
      fallback={({ error, reset }) => (
        <Card className={cn("min-h-[200px]", className)}>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-sm font-medium text-destructive flex items-center gap-2">
                  <AlertCircle className="h-4 w-4" />
                  Widget Crashed
                </CardTitle>
                <CardDescription className="text-xs">
                  {title} encountered a critical error
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-2">
            <div className="text-center py-8">
              <p className="text-sm text-muted-foreground mb-4">
                This widget crashed and needs to be reset.
              </p>
              <Button variant="outline" size="sm" onClick={reset}>
                Reset Widget
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    >
      <Card className={cn(
        "transition-all duration-200",
        widgetState.hasError && priorityStyles[priority],
        className
      )}>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div className="min-w-0 flex-1">
              <CardTitle className="text-sm font-medium truncate flex items-center gap-2">
                {title}
                {widgetState.isRetrying && (
                  <RefreshCw className="h-3 w-3 animate-spin text-blue-500" />
                )}
              </CardTitle>
              {description && (
                <CardDescription className="text-xs truncate">
                  {description}
                </CardDescription>
              )}
            </div>
            <div className="flex items-center gap-2 ml-2">
              {showOfflineIndicator && (
                widgetState.isOffline ? (
                  <WifiOff className="h-4 w-4 text-muted-foreground" title="Offline" />
                ) : (
                  <Wifi className="h-4 w-4 text-green-500" title="Online" />
                )
              )}
              {onRefresh && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleRefresh}
                  disabled={refreshing || loading || widgetState.isRetrying}
                  className="h-6 w-6 p-0"
                  title="Refresh widget"
                >
                  <RefreshCw className={cn(
                    "h-3 w-3",
                    (refreshing || loading) && "animate-spin"
                  )} />
                </Button>
              )}
            </div>
          </div>
          
          {/* Enhanced status indicators */}
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            {showFallback && (
              <div className="flex items-center gap-1 text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded">
                <AlertCircle className="h-3 w-3" />
                <span>Cached data</span>
              </div>
            )}
            
            {widgetState.isOffline && (
              <div className="flex items-center gap-1 text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded">
                <WifiOff className="h-3 w-3" />
                <span>Offline</span>
              </div>
            )}
            
            {widgetState.lastSuccessfulLoad && !loading && !widgetState.hasError && (
              <div className="text-xs text-muted-foreground">
                Updated {widgetState.lastSuccessfulLoad.toLocaleTimeString()}
              </div>
            )}
            
            {widgetState.retryCount > 0 && widgetState.hasError && (
              <div className="text-xs text-muted-foreground bg-red-50 px-2 py-1 rounded">
                Retry {widgetState.retryCount}/{maxRetries}
              </div>
            )}
            
            {widgetState.isRetrying && (
              <div className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
                Retrying...
              </div>
            )}
          </div>
        </CardHeader>

        <CardContent className="pt-2">
          {showLoading && (
            <div className="space-y-3">
              {renderSkeleton()}
            </div>
          )}

          {showError && (
            <div className="text-center py-8">
              <AlertCircle className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
              <p className="text-sm text-muted-foreground mb-2">
                Failed to load {title.toLowerCase()}
              </p>
              
              {widgetState.retryCount > maxRetries ? (
                <p className="text-xs text-red-600 mb-4">
                  Maximum retry attempts reached
                </p>
              ) : (
                <p className="text-xs text-muted-foreground mb-4">
                  {autoRetry ? 'Auto-retry in progress...' : 'Manual retry required'}
                </p>
              )}
              
              {onRetry && (
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={handleRetry}
                  disabled={widgetState.isRetrying || widgetState.retryCount > maxRetries}
                >
                  {widgetState.isRetrying ? 'Retrying...' : 'Try Again'}
                </Button>
              )}
            </div>
          )}

          {showFallback && (
            <div className="relative">
              <div className="absolute inset-0 bg-amber-50/80 rounded flex items-center justify-center z-10">
                <div className="text-center bg-white p-4 rounded-lg shadow-sm border">
                  <AlertCircle className="h-6 w-6 text-amber-600 mx-auto mb-2" />
                  <p className="text-xs text-amber-700 mb-2 font-medium">Showing cached data</p>
                  <p className="text-xs text-amber-600 mb-3">
                    Live data unavailable, displaying last known values
                  </p>
                  {onRetry && (
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={handleRetry}
                      disabled={widgetState.isRetrying}
                    >
                      {widgetState.isRetrying ? 'Retrying...' : 'Retry'}
                    </Button>
                  )}
                </div>
              </div>
              <div className="opacity-60 pointer-events-none">
                {children}
              </div>
            </div>
          )}

          {!showLoading && !showError && !showFallback && children}
        </CardContent>
      </Card>
    </ErrorBoundary>
  )
}

// Hook for managing widget state with enhanced features
export function useWidgetState(id: string, options: {
  autoRetry?: boolean;
  maxRetries?: number;
  retryDelay?: number;
  cacheKey?: string;
} = {}) {
  const {
    autoRetry = true,
    maxRetries = 3,
    retryDelay = 1000,
    cacheKey
  } = options;

  const [state, setState] = useState({
    loading: false,
    error: null as Error | null,
    data: null as any,
    lastFetch: null as Date | null,
    retryCount: 0,
    isRetrying: false,
    cachedData: null as any
  })

  // Load cached data on mount
  useEffect(() => {
    if (cacheKey) {
      try {
        const cached = localStorage.getItem(cacheKey)
        if (cached) {
          const { data, timestamp } = JSON.parse(cached)
          // Use cached data if it's less than 10 minutes old
          if (Date.now() - timestamp < 10 * 60 * 1000) {
            setState(prev => ({ ...prev, cachedData: data }))
          }
        }
      } catch (error) {
        console.warn(`Failed to load cached data for ${id}:`, error)
      }
    }
  }, [id, cacheKey])

  const setLoading = useCallback((loading: boolean) => {
    setState(prev => ({ ...prev, loading, isRetrying: loading && prev.retryCount > 0 }))
  }, [])

  const setError = useCallback((error: Error | null) => {
    setState(prev => ({ 
      ...prev, 
      error, 
      retryCount: error ? prev.retryCount + 1 : 0,
      isRetrying: false
    }))
  }, [])

  const setData = useCallback((data: any) => {
    setState(prev => ({ 
      ...prev, 
      data, 
      error: null, 
      lastFetch: new Date(),
      retryCount: 0,
      isRetrying: false
    }))

    // Cache the data
    if (cacheKey && data) {
      try {
        localStorage.setItem(cacheKey, JSON.stringify({
          data,
          timestamp: Date.now()
        }))
      } catch (error) {
        console.warn(`Failed to cache data for ${id}:`, error)
      }
    }
  }, [id, cacheKey])

  const reset = useCallback(() => {
    setState({
      loading: false,
      error: null,
      data: null,
      lastFetch: null,
      retryCount: 0,
      isRetrying: false,
      cachedData: null
    })
  }, [])

  const retry = useCallback(() => {
    setState(prev => ({
      ...prev,
      error: null,
      isRetrying: true,
      loading: true
    }))
  }, [])

  return {
    ...state,
    setLoading,
    setError,
    setData,
    reset,
    retry,
    // Computed properties
    hasError: !!state.error,
    hasCachedData: !!state.cachedData,
    shouldShowFallback: !!state.error && !!state.cachedData,
    canRetry: state.retryCount < maxRetries,
    displayData: state.data || state.cachedData
  }
}