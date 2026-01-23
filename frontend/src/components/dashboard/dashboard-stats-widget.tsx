"use client"

import React, { useEffect, useCallback } from "react"
import { DashboardWidget, useWidgetState } from "./dashboard-widget"
import { PokerStatCard } from "@/components/ui/stat-card"
import { useBasicStatistics } from "@/hooks/api-hooks"
import { TermLinkedContent } from "@/components/ui/term-linked-content"
import { Activity, TrendingUp, Target, Users, DollarSign } from "lucide-react"

interface DashboardStatsWidgetProps {
  userId?: string
  filters?: any
  className?: string
}

interface DashboardStats {
  totalHands: number
  winRate: number
  vpip: number
  pfr: number
  profit: number
  sessions: number
  handsToday: number
  profitToday: number
}

// Cache key for localStorage
const STATS_CACHE_KEY = 'dashboard_stats_cache'
const CACHE_DURATION = 5 * 60 * 1000 // 5 minutes

function getCachedStats(): DashboardStats | null {
  try {
    const cached = localStorage.getItem(STATS_CACHE_KEY)
    if (cached) {
      const { data, timestamp } = JSON.parse(cached)
      if (Date.now() - timestamp < CACHE_DURATION) {
        return data
      }
    }
  } catch (error) {
    console.warn('Failed to read cached stats:', error)
  }
  return null
}

function setCachedStats(stats: DashboardStats) {
  try {
    localStorage.setItem(STATS_CACHE_KEY, JSON.stringify({
      data: stats,
      timestamp: Date.now()
    }))
  } catch (error) {
    console.warn('Failed to cache stats:', error)
  }
}

export function DashboardStatsWidget({ 
  userId, 
  filters, 
  className 
}: DashboardStatsWidgetProps) {
  const widgetState = useWidgetState('dashboard-stats', {
    autoRetry: true,
    maxRetries: 3,
    retryDelay: 1000,
    cacheKey: STATS_CACHE_KEY
  })
  
  const {
    data: statsData,
    isLoading,
    error,
    refetch
  } = useBasicStatistics(filters)

  // Transform API data to dashboard stats format
  const transformStats = useCallback((apiData: any): DashboardStats => {
    return {
      totalHands: apiData?.handsPlayed || 0,
      winRate: apiData?.winRate || 0,
      vpip: apiData?.vpip || 0,
      pfr: apiData?.pfr || 0,
      profit: apiData?.totalProfit || 0,
      sessions: apiData?.totalSessions || 0,
      handsToday: apiData?.handsToday || 0,
      profitToday: apiData?.profitToday || 0
    }
  }, [])

  // Update widget state when API data changes
  useEffect(() => {
    widgetState.setLoading(isLoading)
    
    if (error) {
      widgetState.setError(error as Error)
    } else if (statsData) {
      const transformedStats = transformStats(statsData)
      widgetState.setData(transformedStats)
    }
  }, [statsData, isLoading, error, widgetState, transformStats])

  const handleRetry = useCallback(() => {
    widgetState.retry()
    refetch()
  }, [widgetState, refetch])

  const handleRefresh = useCallback(() => {
    refetch()
  }, [refetch])

  const displayStats = widgetState.displayData || {
    totalHands: 0,
    winRate: 0,
    vpip: 0,
    pfr: 0,
    profit: 0,
    sessions: 0,
    handsToday: 0,
    profitToday: 0
  }

  return (
    <DashboardWidget
      id="dashboard-stats"
      title="Performance Overview"
      description={
        <TermLinkedContent 
          content="Key poker statistics and metrics including VPIP, PFR, win rate, and session data"
          context="dashboard"
          maxLinks={3}
          className="text-sm text-muted-foreground"
        />
      }
      loading={widgetState.loading}
      error={widgetState.error}
      onRetry={handleRetry}
      onRefresh={handleRefresh}
      refreshing={isLoading}
      className={className}
      priority="high"
      fallbackData={widgetState.cachedData}
      autoRetry={true}
      maxRetries={3}
      retryDelay={1000}
      skeletonRows={4}
    >
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
        <PokerStatCard
          title="Total Hands"
          value={displayStats.totalHands}
          statType="hands"
          icon={<Activity className="h-4 w-4" />}
          trend={{
            value: 20.1,
            label: "from last month",
            isPositive: true
          }}
          loading={widgetState.loading && !widgetState.cachedData}
        />

        <PokerStatCard
          title="Win Rate"
          value={displayStats.winRate}
          statType="winrate"
          icon={<TrendingUp className="h-4 w-4" />}
          trend={{
            value: 2.1,
            label: "from last month",
            isPositive: true
          }}
          loading={widgetState.loading && !widgetState.cachedData}
        />

        <PokerStatCard
          title="VPIP"
          value={displayStats.vpip}
          statType="vpip"
          icon={<Target className="h-4 w-4" />}
          trend={{
            value: 1.2,
            label: "from last month",
            isPositive: false
          }}
          loading={widgetState.loading && !widgetState.cachedData}
        />

        <PokerStatCard
          title="PFR"
          value={displayStats.pfr}
          statType="pfr"
          icon={<Users className="h-4 w-4" />}
          trend={{
            value: 0.5,
            label: "from last month",
            isPositive: true
          }}
          loading={widgetState.loading && !widgetState.cachedData}
        />
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <PokerStatCard
          title="Total Profit"
          value={displayStats.profit}
          statType="profit"
          icon={<DollarSign className="h-4 w-4" />}
          subtitle="All time earnings"
          loading={widgetState.loading && !widgetState.cachedData}
        />

        <PokerStatCard
          title="Sessions"
          value={displayStats.sessions}
          icon={<Activity className="h-4 w-4" />}
          subtitle="Total sessions played"
          loading={widgetState.loading && !widgetState.cachedData}
        />

        <PokerStatCard
          title="Today's Hands"
          value={displayStats.handsToday}
          statType="hands"
          icon={<Activity className="h-4 w-4" />}
          subtitle="Hands played today"
          loading={widgetState.loading && !widgetState.cachedData}
        />

        <PokerStatCard
          title="Today's Profit"
          value={displayStats.profitToday}
          statType="profit"
          icon={<DollarSign className="h-4 w-4" />}
          subtitle="Today's earnings"
          loading={widgetState.loading && !widgetState.cachedData}
        />
      </div>
    </DashboardWidget>
  )
}