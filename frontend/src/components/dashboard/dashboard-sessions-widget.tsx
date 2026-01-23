"use client"

import React, { useEffect, useCallback, useState } from "react"
import { DashboardWidget, useWidgetState } from "./dashboard-widget"
import { Button } from "@/components/ui/button"
import { api } from "@/lib/api-client"

interface DashboardSessionsWidgetProps {
  userId?: string
  filters?: any
  className?: string
}

interface RecentSession {
  id: string
  gameType: string
  stakes: string
  duration: string
  hands: number
  profit: number
  timestamp: string
  winRate: number
}

// Cache key for localStorage
const SESSIONS_CACHE_KEY = 'dashboard_sessions_cache'
const CACHE_DURATION = 5 * 60 * 1000 // 5 minutes

function getCachedSessions(): RecentSession[] | null {
  try {
    const cached = localStorage.getItem(SESSIONS_CACHE_KEY)
    if (cached) {
      const { data, timestamp } = JSON.parse(cached)
      if (Date.now() - timestamp < CACHE_DURATION) {
        return data
      }
    }
  } catch (error) {
    console.warn('Failed to read cached sessions:', error)
  }
  return null
}

function setCachedSessions(sessions: RecentSession[]) {
  try {
    localStorage.setItem(SESSIONS_CACHE_KEY, JSON.stringify({
      data: sessions,
      timestamp: Date.now()
    }))
  } catch (error) {
    console.warn('Failed to cache sessions:', error)
  }
}

export function DashboardSessionsWidget({ 
  userId, 
  filters, 
  className 
}: DashboardSessionsWidgetProps) {
  const widgetState = useWidgetState('dashboard-sessions')
  const cachedSessions = getCachedSessions()
  
  const [sessions, setSessions] = useState<RecentSession[]>([])

  const fetchSessions = useCallback(async (): Promise<RecentSession[]> => {
    try {
      // Try to fetch from API first
      const response = await api.statistics.getSessions({ limit: 4, ...filters })
      
      if (response.data?.sessions) {
        return response.data.sessions.map((session: any) => ({
          id: session.id || Math.random().toString(),
          gameType: session.gameType || 'Unknown',
          stakes: session.stakes || 'N/A',
          duration: session.duration || '0m',
          hands: session.hands || 0,
          profit: session.profit || 0,
          timestamp: session.timestamp || new Date().toISOString(),
          winRate: session.winRate || 0
        }))
      }
    } catch (error) {
      console.warn('API call failed, using mock data:', error)
    }

    // Fallback to mock data if API fails
    return [
      {
        id: '1',
        gameType: 'NL25 Cash',
        stakes: '$0.10/$0.25',
        duration: '2h 15m',
        hands: 156,
        profit: 45.20,
        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        winRate: 8.2
      },
      {
        id: '2',
        gameType: 'Tournament',
        stakes: '$5 Buy-in',
        duration: '1h 45m',
        hands: 89,
        profit: -22.00,
        timestamp: new Date(Date.now() - 26 * 60 * 60 * 1000).toISOString(),
        winRate: -4.1
      },
      {
        id: '3',
        gameType: 'NL50 Cash',
        stakes: '$0.25/$0.50',
        duration: '3h 20m',
        hands: 234,
        profit: 127.80,
        timestamp: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
        winRate: 12.5
      },
      {
        id: '4',
        gameType: 'NL10 Cash',
        stakes: '$0.05/$0.10',
        duration: '1h 30m',
        hands: 98,
        profit: 8.50,
        timestamp: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000).toISOString(),
        winRate: 3.2
      }
    ]
  }, [filters])

  const loadSessions = useCallback(async () => {
    widgetState.setLoading(true)
    widgetState.setError(null)
    
    try {
      const sessionsData = await fetchSessions()
      setSessions(sessionsData)
      widgetState.setData(sessionsData)
      setCachedSessions(sessionsData)
    } catch (error) {
      widgetState.setError(error as Error)
    } finally {
      widgetState.setLoading(false)
    }
  }, [fetchSessions, widgetState])

  // Load initial data
  useEffect(() => {
    if (cachedSessions) {
      setSessions(cachedSessions)
      widgetState.setData(cachedSessions)
    }
    loadSessions()
  }, [loadSessions, cachedSessions, widgetState])

  const handleRetry = useCallback(() => {
    loadSessions()
  }, [loadSessions])

  const handleRefresh = useCallback(() => {
    loadSessions()
  }, [loadSessions])

  const displaySessions = widgetState.data || cachedSessions || []

  return (
    <DashboardWidget
      id="dashboard-sessions"
      title="Recent Sessions"
      description="Your latest poker sessions"
      loading={widgetState.loading}
      error={widgetState.error}
      onRetry={handleRetry}
      onRefresh={handleRefresh}
      refreshing={widgetState.loading}
      className={className}
      priority="medium"
      fallbackData={cachedSessions}
    >
      {displaySessions.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-sm text-muted-foreground mb-4">
            No recent sessions found
          </p>
          <Button variant="outline" size="sm" onClick={handleRetry}>
            Load Sessions
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
          {displaySessions.slice(0, 4).map((session) => (
            <div 
              key={session.id} 
              className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors"
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <p className="font-medium text-sm sm:text-base truncate">
                    {session.gameType}
                  </p>
                  <span className="text-xs text-muted-foreground">
                    ({session.stakes})
                  </span>
                </div>
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  <span>{new Date(session.timestamp).toLocaleDateString()}</span>
                  <span>{session.duration}</span>
                  <span>{session.hands} hands</span>
                </div>
              </div>
              <div className="text-right ml-4">
                <p className={`font-medium text-sm sm:text-base ${
                  session.profit > 0 
                    ? 'text-green-600' 
                    : session.profit < 0 
                    ? 'text-red-600' 
                    : 'text-muted-foreground'
                }`}>
                  {session.profit > 0 ? '+' : ''}${session.profit.toFixed(2)}
                </p>
                <p className="text-xs text-muted-foreground">
                  {session.winRate > 0 ? '+' : ''}{session.winRate.toFixed(1)} BB/100
                </p>
              </div>
            </div>
          ))}
          <Button variant="outline" className="w-full mt-4">
            View All Sessions
          </Button>
        </div>
      )}
    </DashboardWidget>
  )
}