"use client"

import React, { useEffect, useCallback, useState } from "react"
import { DashboardWidget, useWidgetState } from "./dashboard-widget"
import { PokerLineChart, PokerAreaChart, PokerBarChart, CHART_COLORS } from "@/components/ui/chart"
import { useStatisticsTrends, usePositionalStatistics } from "@/hooks/api-hooks"

interface DashboardChartsWidgetProps {
  userId?: string
  filters?: any
  className?: string
}

interface PerformanceTrend {
  name: string
  value: number
  hands: number
  sessions: number
  profit: number
  date: string
}

interface VolumeData {
  name: string
  value: number
  sessions: number
  profit: number
}

interface PositionData {
  position: string
  winRate: number
  hands: number
  profit: number
}

// Cache keys for localStorage
const PERFORMANCE_CACHE_KEY = 'dashboard_performance_cache'
const VOLUME_CACHE_KEY = 'dashboard_volume_cache'
const POSITION_CACHE_KEY = 'dashboard_position_cache'
const CACHE_DURATION = 10 * 60 * 1000 // 10 minutes

function getCachedData<T>(key: string): T | null {
  try {
    const cached = localStorage.getItem(key)
    if (cached) {
      const { data, timestamp } = JSON.parse(cached)
      if (Date.now() - timestamp < CACHE_DURATION) {
        return data
      }
    }
  } catch (error) {
    console.warn(`Failed to read cached data for ${key}:`, error)
  }
  return null
}

function setCachedData<T>(key: string, data: T) {
  try {
    localStorage.setItem(key, JSON.stringify({
      data,
      timestamp: Date.now()
    }))
  } catch (error) {
    console.warn(`Failed to cache data for ${key}:`, error)
  }
}

export function DashboardChartsWidget({ 
  userId, 
  filters, 
  className 
}: DashboardChartsWidgetProps) {
  const performanceState = useWidgetState('performance-chart', {
    cacheKey: PERFORMANCE_CACHE_KEY,
    autoRetry: true,
    maxRetries: 2
  })
  const volumeState = useWidgetState('volume-chart', {
    cacheKey: VOLUME_CACHE_KEY,
    autoRetry: true,
    maxRetries: 2
  })
  const positionState = useWidgetState('position-chart', {
    cacheKey: POSITION_CACHE_KEY,
    autoRetry: true,
    maxRetries: 2
  })

  // API hooks
  const {
    data: trendsData,
    isLoading: trendsLoading,
    error: trendsError,
    refetch: refetchTrends
  } = useStatisticsTrends('14d', filters)

  const {
    data: positionData,
    isLoading: positionLoading,
    error: positionError,
    refetch: refetchPosition
  } = usePositionalStatistics(filters)

  // Mock volume data (replace with real API when available)
  const [volumeData, setVolumeData] = useState<VolumeData[]>([])
  const [volumeLoading, setVolumeLoading] = useState(false)
  const [volumeError, setVolumeError] = useState<Error | null>(null)

  const fetchVolumeData = useCallback(async () => {
    setVolumeLoading(true)
    setVolumeError(null)
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 600))
      
      const mockData = Array.from({ length: 7 }, (_, i) => ({
        name: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][i],
        value: Math.floor(Math.random() * 300) + 100,
        sessions: Math.floor(Math.random() * 5) + 1,
        profit: (Math.random() - 0.3) * 100
      }))
      
      setVolumeData(mockData)
      volumeState.setData(mockData)
    } catch (error) {
      setVolumeError(error as Error)
      volumeState.setError(error as Error)
    } finally {
      setVolumeLoading(false)
    }
  }, [volumeState])

  // Transform API data
  const transformTrendsData = useCallback((apiData: any): PerformanceTrend[] => {
    if (!apiData?.trends) return []
    
    return apiData.trends.map((item: any, index: number) => ({
      name: `Day ${index + 1}`,
      value: item.winRate || 0,
      hands: item.hands || 0,
      sessions: item.sessions || 0,
      profit: item.profit || 0,
      date: item.date || new Date().toLocaleDateString()
    }))
  }, [])

  const transformPositionData = useCallback((apiData: any): PositionData[] => {
    if (!apiData?.positions) return []
    
    return apiData.positions.map((item: any) => ({
      position: item.position || 'Unknown',
      winRate: item.winRate || 0,
      hands: item.hands || 0,
      profit: item.profit || 0
    }))
  }, [])

  // Update widget states when API data changes
  useEffect(() => {
    performanceState.setLoading(trendsLoading)
    
    if (trendsError) {
      performanceState.setError(trendsError as Error)
    } else if (trendsData) {
      const transformedData = transformTrendsData(trendsData)
      performanceState.setData(transformedData)
    }
  }, [trendsData, trendsLoading, trendsError, performanceState, transformTrendsData])

  useEffect(() => {
    positionState.setLoading(positionLoading)
    
    if (positionError) {
      positionState.setError(positionError as Error)
    } else if (positionData) {
      const transformedData = transformPositionData(positionData)
      positionState.setData(transformedData)
    }
  }, [positionData, positionLoading, positionError, positionState, transformPositionData])

  useEffect(() => {
    volumeState.setLoading(volumeLoading)
    volumeState.setError(volumeError)
    
    if (volumeData.length > 0) {
      volumeState.setData(volumeData)
    }
  }, [volumeData, volumeLoading, volumeError, volumeState])

  // Load initial volume data
  useEffect(() => {
    if (!volumeData.length && !volumeState.cachedData) {
      fetchVolumeData()
    } else if (volumeState.cachedData) {
      setVolumeData(volumeState.cachedData)
    }
  }, [fetchVolumeData, volumeData.length, volumeState.cachedData])

  const handleRetryPerformance = useCallback(() => {
    performanceState.retry()
    refetchTrends()
  }, [performanceState, refetchTrends])

  const handleRetryVolume = useCallback(() => {
    volumeState.retry()
    fetchVolumeData()
  }, [volumeState, fetchVolumeData])

  const handleRetryPosition = useCallback(() => {
    positionState.retry()
    refetchPosition()
  }, [positionState, refetchPosition])

  const handleRefreshAll = useCallback(() => {
    refetchTrends()
    fetchVolumeData()
    refetchPosition()
  }, [refetchTrends, fetchVolumeData, refetchPosition])

  const displayPerformanceData = performanceState.displayData || []
  const displayVolumeData = volumeState.displayData || []
  const displayPositionData = positionState.displayData || []

  return (
    <div className={className}>
      {/* Performance Charts Row */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 sm:gap-6 mb-6">
        {/* Performance Trend Chart */}
        <ChartErrorBoundary 
          onRetry={handleRetryPerformance}
          fallbackData={performanceState.cachedData}
        >
          <DashboardWidget
            id="performance-chart"
            title="Performance Trend"
            description="Win rate over the last 14 days"
            loading={performanceState.loading}
            error={performanceState.error}
            onRetry={handleRetryPerformance}
            onRefresh={handleRetryPerformance}
            refreshing={trendsLoading}
            priority="high"
            fallbackData={performanceState.cachedData}
            autoRetry={true}
            maxRetries={2}
            skeletonRows={2}
          >
            <PokerAreaChart
              data={displayPerformanceData}
              title=""
              subtitle=""
              loading={false}
              dataKey="value"
              xAxisKey="name"
              color={CHART_COLORS.primary}
              showGradient={true}
              animated={true}
            />
          </DashboardWidget>
        </ChartErrorBoundary>

        {/* Volume Chart */}
        <ChartErrorBoundary 
          onRetry={handleRetryVolume}
          fallbackData={volumeState.cachedData}
        >
          <DashboardWidget
            id="volume-chart"
            title="Weekly Volume"
            description="Hands played per day this week"
            loading={volumeState.loading}
            error={volumeState.error}
            onRetry={handleRetryVolume}
            onRefresh={handleRetryVolume}
            refreshing={volumeLoading}
            priority="medium"
            fallbackData={volumeState.cachedData}
            autoRetry={true}
            maxRetries={2}
            skeletonRows={2}
          >
            <PokerLineChart
              data={displayVolumeData}
              title=""
              subtitle=""
              loading={false}
              dataKey="value"
              xAxisKey="name"
              color={CHART_COLORS.secondary}
              showBrush={false}
              animated={true}
            />
          </DashboardWidget>
        </ChartErrorBoundary>
      </div>

      {/* Position Analysis */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 sm:gap-6">
        <ChartErrorBoundary 
          onRetry={handleRetryPosition}
          fallbackData={positionState.cachedData}
        >
          <DashboardWidget
            id="position-chart"
            title="Position Analysis"
            description="Win rate by table position"
            loading={positionState.loading}
            error={positionState.error}
            onRetry={handleRetryPosition}
            onRefresh={handleRetryPosition}
            refreshing={positionLoading}
            priority="medium"
            fallbackData={positionState.cachedData}
            autoRetry={true}
            maxRetries={2}
            skeletonRows={2}
          >
            <PokerBarChart
              data={displayPositionData?.map(item => ({
                name: item.position,
                value: item.winRate,
                hands: item.hands,
                profit: item.profit
              })) || []}
              title=""
              subtitle=""
              loading={false}
              dataKey="value"
              xAxisKey="name"
              color={CHART_COLORS.accent}
              showValues={true}
              animated={true}
            />
          </DashboardWidget>
        </ChartErrorBoundary>

        {/* Global refresh control */}
        <DashboardWidget
          id="chart-controls"
          title="Chart Controls"
          description="Manage chart refresh and settings"
          priority="low"
          skeletonRows={1}
        >
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Auto-refresh</span>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                <span className="text-sm text-muted-foreground">Active</span>
              </div>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Last updated</span>
              <span className="text-sm text-muted-foreground">
                {performanceState.lastFetch?.toLocaleTimeString() || 'Never'}
              </span>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Cache status</span>
              <div className="flex items-center gap-2">
                {(performanceState.hasCachedData || volumeState.hasCachedData || positionState.hasCachedData) ? (
                  <>
                    <div className="w-2 h-2 rounded-full bg-blue-500" />
                    <span className="text-sm text-muted-foreground">Available</span>
                  </>
                ) : (
                  <>
                    <div className="w-2 h-2 rounded-full bg-gray-400" />
                    <span className="text-sm text-muted-foreground">Empty</span>
                  </>
                )}
              </div>
            </div>
            
            <button
              onClick={handleRefreshAll}
              disabled={performanceState.loading || volumeState.loading || positionState.loading}
              className="w-full px-3 py-2 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {(performanceState.loading || volumeState.loading || positionState.loading) 
                ? 'Refreshing...' 
                : 'Refresh All Charts'
              }
            </button>
          </div>
        </DashboardWidget>
      </div>
    </div>
  )
}