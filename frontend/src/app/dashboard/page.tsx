"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Container } from "@/components/ui/container"
import { PokerLineChart, PokerAreaChart, PokerBarChart, CHART_COLORS } from "@/components/ui/chart"
import { PokerHandTable } from "@/components/ui/data-table"
import { PokerStatCard } from "@/components/ui/stat-card"
import { useRealTimeCharts } from "@/hooks/useRealTimeCharts"
import { useCallback, useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { TrendingUp, TrendingDown, Activity, DollarSign, Target, Users } from "lucide-react"

// Mock data interfaces
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

interface PerformanceTrend {
  name: string
  value: number
  hands: number
  sessions: number
  profit: number
  date: string
}

export default function Dashboard() {
  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null)
  const [recentSessions, setRecentSessions] = useState<RecentSession[]>([])
  const [recentHands, setRecentHands] = useState<any[]>([])

  // Mock data fetching functions
  const fetchDashboardStats = useCallback(async (): Promise<DashboardStats> => {
    await new Promise(resolve => setTimeout(resolve, 500))
    
    return {
      totalHands: 12847,
      winRate: 5.2,
      vpip: 23.4,
      pfr: 18.7,
      profit: 2847.50,
      sessions: 156,
      handsToday: 89,
      profitToday: 45.20
    }
  }, [])

  const fetchRecentSessions = useCallback(async (): Promise<RecentSession[]> => {
    await new Promise(resolve => setTimeout(resolve, 600))
    
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
  }, [])

  const fetchRecentPerformance = useCallback(async (): Promise<PerformanceTrend[]> => {
    await new Promise(resolve => setTimeout(resolve, 800))
    
    return Array.from({ length: 14 }, (_, i) => {
      const date = new Date(Date.now() - (13 - i) * 24 * 60 * 60 * 1000)
      const baseWinRate = 3 + Math.sin(i * 0.5) * 2 // Oscillating around 3 BB/100
      const variance = (Math.random() - 0.5) * 8 // Add some variance
      
      return {
        name: `Day ${i + 1}`,
        value: baseWinRate + variance,
        hands: Math.floor(Math.random() * 200) + 50,
        sessions: Math.floor(Math.random() * 4) + 1,
        profit: (baseWinRate + variance) * (Math.floor(Math.random() * 200) + 50) * 0.01,
        date: date.toLocaleDateString()
      }
    })
  }, [])

  const fetchVolumeData = useCallback(async () => {
    await new Promise(resolve => setTimeout(resolve, 600))
    
    return Array.from({ length: 7 }, (_, i) => ({
      name: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][i],
      value: Math.floor(Math.random() * 300) + 100,
      sessions: Math.floor(Math.random() * 5) + 1,
      profit: (Math.random() - 0.3) * 100
    }))
  }, [])

  const fetchPositionData = useCallback(async () => {
    await new Promise(resolve => setTimeout(resolve, 700))
    
    return [
      { position: 'UTG', winRate: 2.1, hands: 245, profit: 51.45 },
      { position: 'MP', winRate: 3.4, hands: 198, profit: 67.32 },
      { position: 'CO', winRate: 6.8, hands: 167, profit: 113.56 },
      { position: 'BTN', winRate: 8.2, hands: 156, profit: 127.92 },
      { position: 'SB', winRate: -2.1, hands: 178, profit: -37.38 },
      { position: 'BB', winRate: -1.5, hands: 189, profit: -28.35 }
    ]
  }, [])

  const fetchRecentHands = useCallback(async () => {
    await new Promise(resolve => setTimeout(resolve, 400))
    
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

  // Load initial data
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const [stats, sessions, hands] = await Promise.all([
          fetchDashboardStats(),
          fetchRecentSessions(),
          fetchRecentHands()
        ])
        
        setDashboardStats(stats)
        setRecentSessions(sessions)
        setRecentHands(hands)
      } catch (error) {
        console.error('Failed to load dashboard data:', error)
      }
    }

    loadInitialData()
  }, [fetchDashboardStats, fetchRecentSessions, fetchRecentHands])

  // Real-time chart hooks
  const performanceChart = useRealTimeCharts(fetchRecentPerformance, {
    refreshInterval: 45000, // 45 seconds
    autoRefresh: true
  })

  const volumeChart = useRealTimeCharts(fetchVolumeData, {
    refreshInterval: 60000, // 1 minute
    autoRefresh: true
  })

  const positionChart = useRealTimeCharts(fetchPositionData, {
    refreshInterval: 90000, // 1.5 minutes
    autoRefresh: true
  })
  return (
    <Container className="py-4 sm:py-6 lg:py-8">
      <div className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground text-sm sm:text-base">
          Overview of your poker performance and statistics
        </p>
      </div>

      {/* Key Performance Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 lg:gap-6 mb-6 sm:mb-8">
        <PokerStatCard
          title="Total Hands"
          value={dashboardStats?.totalHands || 0}
          statType="hands"
          icon={<Activity className="h-4 w-4" />}
          trend={{
            value: 20.1,
            label: "from last month",
            isPositive: true
          }}
          loading={!dashboardStats}
        />

        <PokerStatCard
          title="Win Rate"
          value={dashboardStats?.winRate || 0}
          statType="winrate"
          icon={<TrendingUp className="h-4 w-4" />}
          trend={{
            value: 2.1,
            label: "from last month",
            isPositive: true
          }}
          loading={!dashboardStats}
        />

        <PokerStatCard
          title="VPIP"
          value={dashboardStats?.vpip || 0}
          statType="vpip"
          icon={<Target className="h-4 w-4" />}
          trend={{
            value: 1.2,
            label: "from last month",
            isPositive: false
          }}
          loading={!dashboardStats}
        />

        <PokerStatCard
          title="PFR"
          value={dashboardStats?.pfr || 0}
          statType="pfr"
          icon={<Users className="h-4 w-4" />}
          trend={{
            value: 0.5,
            label: "from last month",
            isPositive: true
          }}
          loading={!dashboardStats}
        />
      </div>

      {/* Secondary Stats Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 lg:gap-6 mb-6 sm:mb-8">
        <PokerStatCard
          title="Total Profit"
          value={dashboardStats?.profit || 0}
          statType="profit"
          icon={<DollarSign className="h-4 w-4" />}
          subtitle="All time earnings"
          loading={!dashboardStats}
        />

        <PokerStatCard
          title="Sessions"
          value={dashboardStats?.sessions || 0}
          icon={<Activity className="h-4 w-4" />}
          subtitle="Total sessions played"
          loading={!dashboardStats}
        />

        <PokerStatCard
          title="Today's Hands"
          value={dashboardStats?.handsToday || 0}
          statType="hands"
          icon={<Activity className="h-4 w-4" />}
          subtitle="Hands played today"
          loading={!dashboardStats}
        />

        <PokerStatCard
          title="Today's Profit"
          value={dashboardStats?.profitToday || 0}
          statType="profit"
          icon={<DollarSign className="h-4 w-4" />}
          subtitle="Today's earnings"
          loading={!dashboardStats}
        />
      </div>

      {/* Performance Charts Row */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 sm:gap-6 mb-6 sm:mb-8">
        {/* Performance Trend Chart */}
        <PokerAreaChart
          data={performanceChart.data}
          title="Performance Trend"
          subtitle="Win rate over the last 14 days"
          loading={performanceChart.loading}
          onRefresh={performanceChart.refresh}
          refreshing={performanceChart.loading}
          dataKey="value"
          xAxisKey="name"
          color={CHART_COLORS.primary}
          showGradient={true}
          animated={true}
        />

        {/* Volume Chart */}
        <PokerLineChart
          data={volumeChart.data}
          title="Weekly Volume"
          subtitle="Hands played per day this week"
          loading={volumeChart.loading}
          onRefresh={volumeChart.refresh}
          refreshing={volumeChart.loading}
          dataKey="value"
          xAxisKey="name"
          color={CHART_COLORS.secondary}
          showBrush={false}
          animated={true}
        />
      </div>

      {/* Position Analysis and Recent Sessions */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 sm:gap-6 mb-6 sm:mb-8">
        {/* Position Performance Chart */}
        <PokerBarChart
          data={positionChart.data?.map(item => ({
            name: item.position,
            value: item.winRate,
            hands: item.hands,
            profit: item.profit
          })) || []}
          title="Position Analysis"
          subtitle="Win rate by table position"
          loading={positionChart.loading}
          onRefresh={positionChart.refresh}
          refreshing={positionChart.loading}
          dataKey="value"
          xAxisKey="name"
          color={CHART_COLORS.accent}
          showValues={true}
          animated={true}
        />

        {/* Recent Sessions */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg sm:text-xl">Recent Sessions</CardTitle>
            <CardDescription className="text-sm">
              Your latest poker sessions
            </CardDescription>
          </CardHeader>
          <CardContent>
            {recentSessions.length === 0 ? (
              <div className="animate-pulse space-y-4">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="h-16 bg-gray-100 rounded"></div>
                ))}
              </div>
            ) : (
              <div className="space-y-4">
                {recentSessions.slice(0, 4).map((session) => (
                  <div key={session.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <p className="font-medium text-sm sm:text-base truncate">{session.gameType}</p>
                        <span className="text-xs text-muted-foreground">({session.stakes})</span>
                      </div>
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        <span>{new Date(session.timestamp).toLocaleDateString()}</span>
                        <span>{session.duration}</span>
                        <span>{session.hands} hands</span>
                      </div>
                    </div>
                    <div className="text-right ml-4">
                      <p className={`font-medium text-sm sm:text-base ${
                        session.profit > 0 ? 'text-green-600' : session.profit < 0 ? 'text-red-600' : 'text-muted-foreground'
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
          </CardContent>
        </Card>
      </div>

      {/* Recent Hand History Table */}
      <div className="mb-6 sm:mb-8">
        <PokerHandTable
          hands={recentHands}
          title="Recent Hands"
          loading={recentHands.length === 0}
          onHandClick={(hand) => {
            console.log('Hand clicked:', hand)
            // Navigate to hand analysis page
          }}
        />
      </div>

      {/* Real-time Status and Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg sm:text-xl">Real-time Dashboard</CardTitle>
          <CardDescription className="text-sm">
            Charts automatically refresh every 30-90 seconds
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${
                performanceChart.isAutoRefreshing ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
              }`} />
              <span className="text-sm">
                Auto-refresh: {performanceChart.isAutoRefreshing ? 'On' : 'Off'}
              </span>
            </div>
            
            {performanceChart.lastUpdate && (
              <div className="text-sm text-muted-foreground">
                Last updated: {performanceChart.lastUpdate.toLocaleTimeString()}
              </div>
            )}
            
            <Button
              variant="outline"
              size="sm"
              onClick={performanceChart.toggleAutoRefresh}
            >
              {performanceChart.isAutoRefreshing ? 'Pause Updates' : 'Resume Updates'}
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                performanceChart.refresh()
                volumeChart.refresh()
                positionChart.refresh()
              }}
              disabled={performanceChart.loading}
            >
              Refresh All Charts
            </Button>
          </div>
        </CardContent>
      </Card>
    </Container>
  )
}