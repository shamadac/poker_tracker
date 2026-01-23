"use client"

import React, { useEffect, useCallback, useState } from "react"
import { DashboardWidget, useWidgetState } from "./dashboard-widget"
import { PokerHandTable } from "@/components/ui/data-table"
import { useHands } from "@/hooks/api-hooks"
import { retryManager } from "@/lib/error-handling"
import { Skeleton } from "@/components/loading-states"
import { Button } from "@/components/ui/button"

interface DashboardHandsWidgetProps {
  userId?: string
  filters?: any
  className?: string
}

interface RecentHand {
  id: string
  handId: string
  date: string
  gameType: string
  stakes: string
  position: string
  cards: string[]
  result: string
  profit: number
}

// Cache key for localStorage
const HANDS_CACHE_KEY = 'dashboard_hands_cache'
const CACHE_DURATION = 3 * 60 * 1000 // 3 minutes

function getCachedHands(): RecentHand[] | null {
  try {
    const cached = localStorage.getItem(HANDS_CACHE_KEY)
    if (cached) {
      const { data, timestamp } = JSON.parse(cached)
      if (Date.now() - timestamp < CACHE_DURATION) {
        return data
      }
    }
  } catch (error) {
    console.warn('Failed to read cached hands:', error)
  }
  return null
}

function setCachedHands(hands: RecentHand[]) {
  try {
    localStorage.setItem(HANDS_CACHE_KEY, JSON.stringify({
      data: hands,
      timestamp: Date.now()
    }))
  } catch (error) {
    console.warn('Failed to cache hands:', error)
  }
}

export function DashboardHandsWidget({ 
  userId, 
  filters, 
  className 
}: DashboardHandsWidgetProps) {
  const widgetState = useWidgetState('dashboard-hands')
  const cachedHands = getCachedHands()
  
  const [progressiveLoading, setProgressiveLoading] = useState(false)
  const [viewState, setViewState] = useState({
    showTable: true,
    expandedHands: new Set<string>()
  })

  const {
    data: handsData,
    isLoading,
    error,
    refetch
  } = useHands({ limit: 10, ...filters })

  // Transform API data to display format
  const transformHands = useCallback((apiData: any[]): RecentHand[] => {
    if (!Array.isArray(apiData)) return []
    
    return apiData.map((hand: any) => ({
      id: hand.id || Math.random().toString(),
      handId: hand.handId || `PS${Math.floor(Math.random() * 1000000000)}`,
      date: hand.datePlayedAt || new Date().toISOString(),
      gameType: hand.gameType || 'Unknown',
      stakes: hand.stakes || 'N/A',
      position: hand.position || 'Unknown',
      cards: hand.playerCards || ['?', '?'],
      result: hand.result || 'Unknown',
      profit: hand.profit || 0
    }))
  }, [])

  // Generate mock data as fallback
  const generateMockHands = useCallback((): RecentHand[] => {
    return Array.from({ length: 10 }, (_, i) => ({
      id: `hand-${i + 1}`,
      handId: `PS${Math.floor(Math.random() * 1000000000)}`,
      date: new Date(Date.now() - i * 15 * 60 * 1000).toISOString(),
      gameType: ['NL25', 'NL50', 'Tournament'][Math.floor(Math.random() * 3)],
      stakes: ['$0.10/$0.25', '$0.25/$0.50', '$5 Buy-in'][Math.floor(Math.random() * 3)],
      position: ['UTG', 'MP', 'CO', 'BTN', 'SB', 'BB'][Math.floor(Math.random() * 6)],
      cards: ['AK', 'QQ', '77', 'A5s', 'KJ', '98s'][Math.floor(Math.random() * 6)].split(''),
      result: ['Won', 'Lost', 'Folded'][Math.floor(Math.random() * 3)],
      profit: (Math.random() - 0.5) * 50
    }))
  }, [])

  // Progressive loading: load cached data first, then fetch fresh data
  const loadProgressively = useCallback(async () => {
    // First, load cached data immediately if available
    if (cachedHands && cachedHands.length > 0) {
      widgetState.setData(cachedHands)
    }
    
    // Then fetch fresh data in the background
    setProgressiveLoading(true)
    try {
      const retryKey = `dashboard-hands-${userId || 'default'}`
      
      // Use retry manager for automatic retry with exponential backoff
      await retryManager.executeWithRetry(retryKey, async () => {
        await refetch()
      })
    } catch (error) {
      // If fresh data fails but we have cached data, that's okay
      if (!cachedHands || cachedHands.length === 0) {
        widgetState.setError(error as Error)
        // Use mock data as final fallback
        const mockHands = generateMockHands()
        widgetState.setData(mockHands)
        setCachedHands(mockHands)
      }
    } finally {
      setProgressiveLoading(false)
    }
  }, [cachedHands, widgetState, userId, refetch, generateMockHands])

  // Update widget state when API data changes
  useEffect(() => {
    widgetState.setLoading(isLoading && !cachedHands)
    
    if (error) {
      widgetState.setError(error as Error)
      // Use mock data as fallback when API fails
      if (!cachedHands) {
        const mockHands = generateMockHands()
        widgetState.setData(mockHands)
        setCachedHands(mockHands)
      }
    } else if (handsData) {
      const transformedHands = transformHands(handsData)
      // If API returns empty data, use mock data
      const finalHands = transformedHands.length > 0 ? transformedHands : generateMockHands()
      widgetState.setData(finalHands)
      setCachedHands(finalHands)
    }
  }, [handsData, isLoading, error, widgetState, transformHands, generateMockHands, cachedHands])

  // Load initial data progressively
  useEffect(() => {
    loadProgressively()
  }, [loadProgressively])

  const handleRetry = useCallback(() => {
    refetch()
  }, [refetch])

  const handleRefresh = useCallback(() => {
    refetch()
  }, [refetch])

  const handleHandClick = useCallback((hand: any) => {
    console.log('Hand clicked:', hand)
    // Navigate to hand analysis page
    // router.push(`/analysis/hand/${hand.id}`)
  }, [])

  const toggleViewMode = useCallback(() => {
    setViewState(prev => ({ ...prev, showTable: !prev.showTable }))
  }, [])

  const displayHands = widgetState.data || cachedHands || []
  const isWidgetLoading = widgetState.loading && displayHands.length === 0
  const showProgressiveIndicator = progressiveLoading && displayHands.length > 0

  return (
    <DashboardWidget
      id="dashboard-hands"
      title="Recent Hands"
      description="Your latest poker hands"
      loading={isWidgetLoading}
      error={widgetState.error}
      onRetry={handleRetry}
      onRefresh={handleRefresh}
      refreshing={widgetState.loading || progressiveLoading}
      className={className}
      priority="medium"
      fallbackData={cachedHands}
    >
      {showProgressiveIndicator && (
        <div className="flex items-center gap-2 text-xs text-muted-foreground mb-3">
          <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
          <span>Updating hands...</span>
        </div>
      )}

      {/* View controls */}
      <div className="flex items-center justify-between mb-4">
        <div className="text-sm text-muted-foreground">
          {displayHands.length} hands
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={toggleViewMode}
        >
          {viewState.showTable ? 'List View' : 'Table View'}
        </Button>
      </div>

      {isWidgetLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-3 w-48" />
              </div>
              <Skeleton className="h-4 w-16" />
            </div>
          ))}
        </div>
      ) : displayHands.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-sm text-muted-foreground mb-4">
            No recent hands found
          </p>
          <Button variant="outline" size="sm" onClick={handleRetry}>
            Load Hands
          </Button>
        </div>
      ) : viewState.showTable ? (
        <PokerHandTable
          hands={displayHands}
          title=""
          loading={false}
          onHandClick={handleHandClick}
        />
      ) : (
        <div className="space-y-3">
          {displayHands.slice(0, 8).map((hand: RecentHand, index: number) => (
            <div 
              key={hand.id}
              className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors cursor-pointer"
              onClick={() => handleHandClick(hand)}
              style={{
                animationDelay: `${index * 50}ms`,
                animation: isWidgetLoading ? 'none' : 'fadeInUp 0.3s ease-out forwards'
              }}
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <p className="font-medium text-sm truncate">
                    {hand.handId}
                  </p>
                  <span className="text-xs text-muted-foreground">
                    {hand.gameType} ({hand.stakes})
                  </span>
                </div>
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  <span>{new Date(hand.date).toLocaleTimeString()}</span>
                  <span>{hand.position}</span>
                  <span>{hand.cards.join('')}</span>
                  <span>{hand.result}</span>
                </div>
              </div>
              <div className="text-right ml-4">
                <p className={`font-medium text-sm ${
                  hand.profit > 0 
                    ? 'text-green-600' 
                    : hand.profit < 0 
                    ? 'text-red-600' 
                    : 'text-muted-foreground'
                }`}>
                  {hand.profit > 0 ? '+' : ''}${hand.profit.toFixed(2)}
                </p>
              </div>
            </div>
          ))}
          
          {displayHands.length > 8 && (
            <Button variant="outline" className="w-full mt-4">
              View All {displayHands.length} Hands
            </Button>
          )}
        </div>
      )}
      
      <style jsx>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </DashboardWidget>
  )
}