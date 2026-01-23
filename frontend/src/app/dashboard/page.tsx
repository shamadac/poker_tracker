"use client"

import React, { useEffect, useCallback, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ErrorBoundary, APIErrorBoundary, ChartErrorBoundary, WidgetErrorBoundary } from "@/components/error-boundary"
import { DashboardStatsWidget } from "@/components/dashboard/dashboard-stats-widget"
import { DashboardChartsWidget } from "@/components/dashboard/dashboard-charts-widget"
import { DashboardSessionsWidget } from "@/components/dashboard/dashboard-sessions-widget"
import { DashboardHandsWidget } from "@/components/dashboard/dashboard-hands-widget"
import { useDashboardState } from "@/hooks/use-dashboard-state"
import { LoadingSpinner, Skeleton } from "@/components/loading-states"
import { Settings, RefreshCw, Layout, Eye, EyeOff, Maximize2, Minimize2, AlertCircle, Wifi, WifiOff } from "lucide-react"
import { cn } from "@/lib/utils"

interface DashboardPageState {
  isRefreshing: boolean
  lastRefresh: Date | null
  refreshError: Error | null
  isOnline: boolean
  autoRefreshEnabled: boolean
  refreshInterval: number
}

const DASHBOARD_REFRESH_INTERVAL = 30000 // 30 seconds
const DASHBOARD_STATE_KEY = 'dashboard_page_state'

function saveDashboardState(state: Partial<DashboardPageState>) {
  try {
    const existing = localStorage.getItem(DASHBOARD_STATE_KEY)
    const currentState = existing ? JSON.parse(existing) : {}
    const newState = { ...currentState, ...state }
    localStorage.setItem(DASHBOARD_STATE_KEY, JSON.stringify(newState))
  } catch (error) {
    console.warn('Failed to save dashboard state:', error)
  }
}

function loadDashboardState(): Partial<DashboardPageState> {
  try {
    const stored = localStorage.getItem(DASHBOARD_STATE_KEY)
    return stored ? JSON.parse(stored) : {}
  } catch (error) {
    console.warn('Failed to load dashboard state:', error)
    return {}
  }
}

export default function DashboardPage() {
  const {
    viewState,
    preferences,
    isLoading: dashboardStateLoading,
    updateViewState,
    toggleWidget,
    isWidgetVisible,
    setAutoRefresh,
    markRefreshed,
    preserveViewState,
    restoreViewState
  } = useDashboardState()

  const [pageState, setPageState] = useState<DashboardPageState>({
    isRefreshing: false,
    lastRefresh: null,
    refreshError: null,
    isOnline: true,
    autoRefreshEnabled: true,
    refreshInterval: DASHBOARD_REFRESH_INTERVAL
  })

  // Monitor online/offline status
  useEffect(() => {
    const handleOnline = () => {
      setPageState(prev => ({ ...prev, isOnline: true }))
      if (pageState.autoRefreshEnabled) {
        handleRefreshAll()
      }
    }
    
    const handleOffline = () => {
      setPageState(prev => ({ ...prev, isOnline: false }))
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    // Set initial state
    setPageState(prev => ({ ...prev, isOnline: navigator.onLine }))

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [pageState.autoRefreshEnabled])

  // Load saved dashboard state on mount
  useEffect(() => {
    const savedState = loadDashboardState()
    if (savedState) {
      setPageState(prev => ({ ...prev, ...savedState }))
    }
  }, [])

  // Auto-refresh logic
  useEffect(() => {
    if (!pageState.autoRefreshEnabled || !pageState.isOnline) {
      return
    }

    const interval = setInterval(() => {
      handleRefreshAll()
    }, pageState.refreshInterval)

    return () => clearInterval(interval)
  }, [pageState.autoRefreshEnabled, pageState.isOnline, pageState.refreshInterval])

  const handleRefreshAll = useCallback(async () => {
    if (pageState.isRefreshing) return

    // Preserve view state before refresh
    preserveViewState()

    setPageState(prev => ({ ...prev, isRefreshing: true, refreshError: null }))
    
    try {
      // Trigger refresh for all visible widgets
      // This will be handled by individual widgets through their own refresh mechanisms
      
      const now = new Date()
      setPageState(prev => ({ ...prev, lastRefresh: now, refreshError: null }))
      markRefreshed()
      
      // Save state
      saveDashboardState({ lastRefresh: now })
      
    } catch (error) {
      console.error('Dashboard refresh failed:', error)
      setPageState(prev => ({ 
        ...prev, 
        refreshError: error as Error 
      }))
    } finally {
      setPageState(prev => ({ ...prev, isRefreshing: false }))
    }
  }, [pageState.isRefreshing, markRefreshed, preserveViewState])

  const toggleAutoRefresh = useCallback(() => {
    const newEnabled = !pageState.autoRefreshEnabled
    setPageState(prev => ({ ...prev, autoRefreshEnabled: newEnabled }))
    setAutoRefresh(newEnabled)
    saveDashboardState({ autoRefreshEnabled: newEnabled })
  }, [pageState.autoRefreshEnabled, setAutoRefresh])

  const handleWidgetToggle = useCallback((widgetId: string) => {
    toggleWidget(widgetId)
  }, [toggleWidget])

  // Show loading state while dashboard state is loading
  if (dashboardStateLoading) {
    return (
      <div className="container mx-auto py-4 sm:py-6 lg:py-8">
        <div className="mb-6 sm:mb-8">
          <Skeleton className="h-8 w-48 mb-2" />
          <Skeleton className="h-4 w-96" />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4 sm:gap-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-5 w-32" />
                <Skeleton className="h-4 w-48" />
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <Skeleton className="h-8 w-full" />
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-4 w-1/2" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <ErrorBoundary
      title="Dashboard Error"
      showDetails={process.env.NODE_ENV === 'development'}
    >
      <div className="container mx-auto py-4 sm:py-6 lg:py-8">
        {/* Header with controls */}
        <div className="mb-6 sm:mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold">Dashboard</h1>
              <p className="text-muted-foreground text-sm sm:text-base">
                Overview of your poker performance and statistics
              </p>
            </div>
            
            <div className="flex items-center gap-2">
              {/* Online/Offline indicator */}
              <div className="flex items-center gap-2 text-sm">
                {pageState.isOnline ? (
                  <Wifi className="h-4 w-4 text-green-500" />
                ) : (
                  <WifiOff className="h-4 w-4 text-red-500" />
                )}
                <span className={pageState.isOnline ? 'text-green-600' : 'text-red-600'}>
                  {pageState.isOnline ? 'Online' : 'Offline'}
                </span>
              </div>

              {/* Refresh controls */}
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefreshAll}
                disabled={pageState.isRefreshing || !pageState.isOnline}
                className="flex items-center gap-2"
              >
                <RefreshCw className={cn(
                  "h-4 w-4",
                  pageState.isRefreshing && "animate-spin"
                )} />
                {pageState.isRefreshing ? 'Refreshing...' : 'Refresh All'}
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={toggleAutoRefresh}
                className={cn(
                  "flex items-center gap-2",
                  pageState.autoRefreshEnabled && "bg-green-50 border-green-200"
                )}
              >
                <div className={cn(
                  "w-2 h-2 rounded-full",
                  pageState.autoRefreshEnabled ? "bg-green-500 animate-pulse" : "bg-gray-400"
                )} />
                Auto-refresh {pageState.autoRefreshEnabled ? 'On' : 'Off'}
              </Button>
            </div>
          </div>

          {/* Status indicators */}
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            {pageState.lastRefresh && (
              <span>Last updated: {pageState.lastRefresh.toLocaleTimeString()}</span>
            )}
            
            {pageState.refreshError && (
              <div className="flex items-center gap-1 text-red-600">
                <AlertCircle className="h-4 w-4" />
                <span>Refresh failed</span>
              </div>
            )}
            
            {!pageState.isOnline && (
              <div className="flex items-center gap-1 text-amber-600">
                <AlertCircle className="h-4 w-4" />
                <span>Using cached data</span>
              </div>
            )}
          </div>
        </div>

        {/* Widget visibility controls */}
        <div className="mb-6">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Layout className="h-4 w-4" />
                Widget Controls
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {Object.entries(viewState.widgetVisibility).map(([widgetId, visible]) => (
                  <Button
                    key={widgetId}
                    variant={visible ? "default" : "outline"}
                    size="sm"
                    onClick={() => handleWidgetToggle(widgetId)}
                    className="flex items-center gap-2"
                  >
                    {visible ? <Eye className="h-3 w-3" /> : <EyeOff className="h-3 w-3" />}
                    {widgetId.replace('dashboard-', '').replace('-', ' ')}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Dashboard widgets with enhanced error boundaries */}
        <div className="space-y-6">
          {/* Stats Widget */}
          {isWidgetVisible('dashboard-stats') && (
            <WidgetErrorBoundary
              widgetId="dashboard-stats"
              title="Performance Overview"
              onRetry={() => window.location.reload()}
              priority="high"
            >
              <DashboardStatsWidget 
                className="mb-6"
              />
            </WidgetErrorBoundary>
          )}

          {/* Charts Widget */}
          {isWidgetVisible('dashboard-charts') && (
            <WidgetErrorBoundary
              widgetId="dashboard-charts"
              title="Performance Charts"
              onRetry={() => window.location.reload()}
              priority="high"
            >
              <DashboardChartsWidget 
                className="mb-6"
              />
            </WidgetErrorBoundary>
          )}

          {/* Sessions and Hands widgets in grid */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 sm:gap-6">
            {isWidgetVisible('dashboard-sessions') && (
              <WidgetErrorBoundary
                widgetId="dashboard-sessions"
                title="Recent Sessions"
                onRetry={() => window.location.reload()}
                priority="medium"
              >
                <DashboardSessionsWidget />
              </WidgetErrorBoundary>
            )}

            {isWidgetVisible('dashboard-hands') && (
              <WidgetErrorBoundary
                widgetId="dashboard-hands"
                title="Recent Hands"
                onRetry={() => window.location.reload()}
                priority="medium"
              >
                <DashboardHandsWidget />
              </WidgetErrorBoundary>
            )}
          </div>
        </div>

        {/* Dashboard status footer */}
        <Card className="mt-8">
          <CardHeader>
            <CardTitle className="text-sm font-medium">Dashboard Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Layout:</span>
                <span className="ml-2 capitalize">{viewState.layout}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Visible Widgets:</span>
                <span className="ml-2">
                  {Object.values(viewState.widgetVisibility).filter(Boolean).length}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">Auto-refresh:</span>
                <span className="ml-2">
                  {pageState.autoRefreshEnabled ? 'Enabled' : 'Disabled'}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">Connection:</span>
                <span className={cn(
                  "ml-2",
                  pageState.isOnline ? "text-green-600" : "text-red-600"
                )}>
                  {pageState.isOnline ? 'Online' : 'Offline'}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </ErrorBoundary>
  )
}