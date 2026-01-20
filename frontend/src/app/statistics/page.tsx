"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Container } from "@/components/ui/container"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { ExportDialog } from "@/components/ui/export-dialog"
import { 
  PokerLineChart, 
  PokerBarChart, 
  PokerMultiLineChart,
  PokerPositionChart,
  PokerWinRateTrend,
  PokerHeatmap,
  PokerPieChart,
  CHART_COLORS 
} from "@/components/ui/chart"
import { PokerStatCard } from "@/components/ui/stat-card"
import { DataTable } from "@/components/ui/data-table"
import { useRealTimeCharts } from "@/hooks/useRealTimeCharts"
import { useState, useCallback, useMemo } from "react"
import { Download, Filter, RefreshCw, TrendingUp, Target, Activity, DollarSign, BarChart3 } from "lucide-react"

// Statistics interfaces
interface StatisticsFilters {
  dateRange: string
  gameType: string
  stakes: string
  position: string
  sessionType: string
}

interface AdvancedStats {
  vpip: number
  pfr: number
  aggressionFactor: number
  winRate: number
  threeBetPercent: number
  foldToThreeBet: number
  cBetFlop: number
  cBetTurn: number
  cBetRiver: number
  foldToCBetFlop: number
  checkRaiseFlop: number
  wtsd: number // Went to showdown
  wsd: number // Won at showdown
  totalHands: number
  totalProfit: number
  hourlyRate: number
  redLine: number
  blueLine: number
}

interface SessionData {
  id: string
  date: string
  gameType: string
  stakes: string
  duration: number // minutes
  hands: number
  profit: number
  winRate: number
  vpip: number
  pfr: number
}

export default function Statistics() {
  const [filters, setFilters] = useState<StatisticsFilters>({
    dateRange: '30d',
    gameType: 'all',
    stakes: 'all',
    position: 'all',
    sessionType: 'all'
  })

  const [activeTab, setActiveTab] = useState('overview')
  const [isExporting, setIsExporting] = useState(false)
  const [showExportDialog, setShowExportDialog] = useState(false)

  // Mock advanced statistics
  const [advancedStats] = useState<AdvancedStats>({
    vpip: 23.4,
    pfr: 18.7,
    aggressionFactor: 2.8,
    winRate: 5.2,
    threeBetPercent: 8.2,
    foldToThreeBet: 72.1,
    cBetFlop: 68.5,
    cBetTurn: 54.2,
    cBetRiver: 42.8,
    foldToCBetFlop: 45.6,
    checkRaiseFlop: 12.3,
    wtsd: 28.5,
    wsd: 54.2,
    totalHands: 12847,
    totalProfit: 2847.50,
    hourlyRate: 15.75,
    redLine: -245.80,
    blueLine: 3093.30
  })

  // Mock data fetching functions
  const fetchPositionData = useCallback(async () => {
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    return [
      { position: 'UTG', winRate: 2.1, vpip: 15.2, pfr: 12.8, hands: 1245, profit: 261.45 },
      { position: 'MP', winRate: 3.4, vpip: 18.5, pfr: 14.2, hands: 1198, profit: 407.32 },
      { position: 'CO', winRate: 6.8, vpip: 24.1, pfr: 18.7, hands: 1167, profit: 793.56 },
      { position: 'BTN', winRate: 8.2, vpip: 28.9, pfr: 22.1, hands: 1156, profit: 947.92 },
      { position: 'SB', winRate: -2.1, vpip: 32.4, pfr: 15.6, hands: 1178, profit: -247.38 },
      { position: 'BB', winRate: -1.5, vpip: 25.7, pfr: 8.9, hands: 1189, profit: -185.35 }
    ]
  }, [filters])

  const fetchWinRateTrend = useCallback(async () => {
    await new Promise(resolve => setTimeout(resolve, 800))
    
    return Array.from({ length: 30 }, (_, i) => {
      const baseWinRate = 3 + Math.sin(i * 0.3) * 2
      const variance = (Math.random() - 0.5) * 6
      const movingAverage = baseWinRate + Math.sin(i * 0.1) * 1.5
      
      return {
        session: (i + 1).toString(),
        winRate: baseWinRate + variance,
        movingAverage: movingAverage,
        hands: Math.floor(Math.random() * 200) + 50,
        date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toLocaleDateString(),
        profit: (baseWinRate + variance) * (Math.floor(Math.random() * 200) + 50) * 0.01
      }
    })
  }, [filters])

  const fetchHourlyData = useCallback(async () => {
    await new Promise(resolve => setTimeout(resolve, 1200))
    
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    const data = []
    
    for (const day of days) {
      for (let hour = 0; hour < 24; hour++) {
        const activityProbability = hour >= 18 && hour <= 23 ? 0.7 : 
                                   hour >= 12 && hour <= 17 ? 0.4 : 0.1
        
        if (Math.random() < activityProbability) {
          data.push({
            hour,
            day,
            winRate: (Math.random() - 0.5) * 15,
            hands: Math.floor(Math.random() * 100) + 20,
            sessions: Math.floor(Math.random() * 3) + 1,
            profit: (Math.random() - 0.3) * 50
          })
        }
      }
    }
    
    return data
  }, [filters])

  const fetchStakesDistribution = useCallback(async () => {
    await new Promise(resolve => setTimeout(resolve, 600))
    
    return [
      { name: 'NL10', value: 35, hands: 4500, profit: 450.25 },
      { name: 'NL25', value: 40, hands: 5100, profit: 1275.80 },
      { name: 'NL50', value: 20, hands: 2600, profit: 1300.45 },
      { name: 'NL100', value: 5, hands: 647, profit: -179.00 }
    ]
  }, [filters])

  const fetchSessionsData = useCallback(async (): Promise<SessionData[]> => {
    await new Promise(resolve => setTimeout(resolve, 900))
    
    return Array.from({ length: 50 }, (_, i) => ({
      id: `session-${i + 1}`,
      date: new Date(Date.now() - i * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      gameType: ['NL Hold\'em', 'Tournament', 'Sit & Go'][Math.floor(Math.random() * 3)],
      stakes: ['$0.10/$0.25', '$0.25/$0.50', '$0.50/$1.00', '$5 Buy-in'][Math.floor(Math.random() * 4)],
      duration: Math.floor(Math.random() * 240) + 60, // 60-300 minutes
      hands: Math.floor(Math.random() * 300) + 50,
      profit: (Math.random() - 0.4) * 200, // Slightly positive bias
      winRate: (Math.random() - 0.3) * 20,
      vpip: Math.random() * 15 + 15, // 15-30%
      pfr: Math.random() * 10 + 10 // 10-20%
    }))
  }, [filters])

  // Real-time chart hooks
  const positionChart = useRealTimeCharts(fetchPositionData, {
    refreshInterval: 60000,
    autoRefresh: true
  })

  const winRateChart = useRealTimeCharts(fetchWinRateTrend, {
    refreshInterval: 30000,
    autoRefresh: true
  })

  const heatmapChart = useRealTimeCharts(fetchHourlyData, {
    refreshInterval: 120000,
    autoRefresh: true
  })

  const stakesChart = useRealTimeCharts(fetchStakesDistribution, {
    refreshInterval: 90000,
    autoRefresh: true
  })

  const sessionsChart = useRealTimeCharts(fetchSessionsData, {
    refreshInterval: 45000,
    autoRefresh: true
  })

  // Filter handlers
  const handleFilterChange = (filterType: keyof StatisticsFilters, value: string) => {
    setFilters(prev => ({
      ...prev,
      [filterType]: value
    }))
  }

  const applyFilters = () => {
    // Refresh all charts when filters change
    positionChart.refresh()
    winRateChart.refresh()
    heatmapChart.refresh()
    stakesChart.refresh()
    sessionsChart.refresh()
  }

  const handleExport = async (format: 'pdf' | 'csv') => {
    setIsExporting(true)
    try {
      // Simulate export process
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      // In real implementation, this would call the backend API
      console.log(`Exporting statistics as ${format.toUpperCase()}`)
      
      // Create a mock download
      const filename = `poker-statistics-${new Date().toISOString().split('T')[0]}.${format}`
      alert(`Statistics exported as ${filename}`)
      
    } catch (error) {
      console.error('Export failed:', error)
      alert('Export failed. Please try again.')
    } finally {
      setIsExporting(false)
    }
  }

  // Computed statistics for display
  const computedStats = useMemo(() => {
    return {
      totalSessions: sessionsChart.data.length,
      avgSessionLength: sessionsChart.data.reduce((acc, s) => acc + s.duration, 0) / sessionsChart.data.length || 0,
      bestSession: sessionsChart.data.reduce((best, current) => 
        current.profit > best.profit ? current : best, 
        sessionsChart.data[0] || { profit: 0 }
      ),
      worstSession: sessionsChart.data.reduce((worst, current) => 
        current.profit < worst.profit ? current : worst, 
        sessionsChart.data[0] || { profit: 0 }
      )
    }
  }, [sessionsChart.data])

  return (
    <Container className="py-4 sm:py-6 lg:py-8">
      <div className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold">Statistics</h1>
        <p className="text-muted-foreground text-sm sm:text-base">
          Comprehensive poker statistics and performance analytics
        </p>
      </div>

      {/* Filters Section */}
      <Card className="mb-4 sm:mb-6">
        <CardHeader>
          <CardTitle className="text-lg sm:text-xl flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filters & Export
          </CardTitle>
          <CardDescription className="text-sm">
            Filter your statistics and export reports
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Date Range</label>
              <Select value={filters.dateRange} onValueChange={(value) => handleFilterChange('dateRange', value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="7d">Last 7 days</SelectItem>
                  <SelectItem value="30d">Last 30 days</SelectItem>
                  <SelectItem value="90d">Last 90 days</SelectItem>
                  <SelectItem value="1y">Last year</SelectItem>
                  <SelectItem value="all">All time</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Game Type</label>
              <Select value={filters.gameType} onValueChange={(value) => handleFilterChange('gameType', value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Games</SelectItem>
                  <SelectItem value="cash">Cash Games</SelectItem>
                  <SelectItem value="tournament">Tournaments</SelectItem>
                  <SelectItem value="sng">Sit & Go</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Stakes</label>
              <Select value={filters.stakes} onValueChange={(value) => handleFilterChange('stakes', value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Stakes</SelectItem>
                  <SelectItem value="micro">Micro ($0.01-$0.05)</SelectItem>
                  <SelectItem value="low">Low ($0.10-$0.50)</SelectItem>
                  <SelectItem value="mid">Mid ($1-$5)</SelectItem>
                  <SelectItem value="high">High ($10+)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Position</label>
              <Select value={filters.position} onValueChange={(value) => handleFilterChange('position', value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Positions</SelectItem>
                  <SelectItem value="early">Early (UTG, UTG+1)</SelectItem>
                  <SelectItem value="middle">Middle (MP, MP+1)</SelectItem>
                  <SelectItem value="late">Late (CO, BTN)</SelectItem>
                  <SelectItem value="blinds">Blinds (SB, BB)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-end">
              <Button onClick={applyFilters} className="w-full">
                <RefreshCw className="h-4 w-4 mr-2" />
                Apply Filters
              </Button>
            </div>
          </div>

          {/* Export Buttons */}
          <div className="flex flex-wrap gap-2">
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => setShowExportDialog(true)}
              disabled={isExporting}
            >
              <Download className="h-4 w-4 mr-2" />
              Export Data
            </Button>
          </div>
            >
              <Download className="h-4 w-4 mr-2" />
              Export CSV
            </Button>
            {Object.values(filters).some(f => f !== 'all' && f !== '30d') && (
              <Badge variant="secondary" className="ml-2">
                Filters Active
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Statistics Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="advanced">Advanced</TabsTrigger>
          <TabsTrigger value="sessions">Sessions</TabsTrigger>
          <TabsTrigger value="trends">Trends</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {/* Key Statistics Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 lg:gap-6">
            <PokerStatCard
              title="VPIP"
              value={advancedStats.vpip}
              statType="vpip"
              icon={<Target className="h-4 w-4" />}
              subtitle="Voluntarily Put $ In Pot"
            />
            <PokerStatCard
              title="PFR"
              value={advancedStats.pfr}
              statType="pfr"
              icon={<TrendingUp className="h-4 w-4" />}
              subtitle="Pre-Flop Raise"
            />
            <PokerStatCard
              title="Win Rate"
              value={advancedStats.winRate}
              statType="winrate"
              icon={<BarChart3 className="h-4 w-4" />}
              subtitle="BB/100 hands"
            />
            <PokerStatCard
              title="Total Profit"
              value={advancedStats.totalProfit}
              statType="profit"
              icon={<DollarSign className="h-4 w-4" />}
              subtitle="All time earnings"
            />
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 sm:gap-6">
            <PokerPositionChart
              data={positionChart.data}
              loading={positionChart.loading}
              onRefresh={positionChart.refresh}
              refreshing={positionChart.loading}
              metric="winRate"
            />

            <PokerPieChart
              data={stakesChart.data}
              title="Stakes Distribution"
              subtitle="Hands played by stakes level"
              loading={stakesChart.loading}
              onRefresh={stakesChart.refresh}
              refreshing={stakesChart.loading}
              showLegend={true}
            />
          </div>

          {/* Win Rate Trend */}
          <PokerWinRateTrend
            data={winRateChart.data}
            loading={winRateChart.loading}
            onRefresh={winRateChart.refresh}
            refreshing={winRateChart.loading}
            showMovingAverage={true}
            period={10}
          />
        </TabsContent>

        {/* Advanced Tab */}
        <TabsContent value="advanced" className="space-y-6">
          {/* Advanced Statistics Grid */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 lg:gap-6">
            <PokerStatCard
              title="3-Bet %"
              value={advancedStats.threeBetPercent}
              statType="pfr"
              subtitle="Pre-flop 3-bet frequency"
            />
            <PokerStatCard
              title="Fold to 3-Bet"
              value={advancedStats.foldToThreeBet}
              statType="vpip"
              subtitle="When facing 3-bet"
            />
            <PokerStatCard
              title="C-Bet Flop"
              value={advancedStats.cBetFlop}
              statType="vpip"
              subtitle="Continuation bet flop"
            />
            <PokerStatCard
              title="WTSD"
              value={advancedStats.wtsd}
              statType="vpip"
              subtitle="Went to showdown"
            />
          </div>

          {/* Red Line / Blue Line */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 sm:gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Showdown vs Non-Showdown</CardTitle>
                <CardDescription>Red line (non-showdown) vs Blue line (showdown) winnings</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                      <span className="text-sm">Red Line (Non-showdown)</span>
                    </div>
                    <span className={`font-medium ${advancedStats.redLine >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {advancedStats.redLine >= 0 ? '+' : ''}${advancedStats.redLine.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                      <span className="text-sm">Blue Line (Showdown)</span>
                    </div>
                    <span className={`font-medium ${advancedStats.blueLine >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {advancedStats.blueLine >= 0 ? '+' : ''}${advancedStats.blueLine.toFixed(2)}
                    </span>
                  </div>
                  <div className="pt-2 border-t">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Total</span>
                      <span className={`font-bold ${advancedStats.totalProfit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {advancedStats.totalProfit >= 0 ? '+' : ''}${advancedStats.totalProfit.toFixed(2)}
                      </span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Performance Heatmap */}
            <PokerHeatmap
              data={heatmapChart.data}
              loading={heatmapChart.loading}
              onRefresh={heatmapChart.refresh}
              refreshing={heatmapChart.loading}
            />
          </div>
        </TabsContent>

        {/* Sessions Tab */}
        <TabsContent value="sessions" className="space-y-6">
          {/* Session Summary Stats */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 lg:gap-6">
            <PokerStatCard
              title="Total Sessions"
              value={computedStats.totalSessions}
              icon={<Activity className="h-4 w-4" />}
              subtitle="All time sessions"
            />
            <PokerStatCard
              title="Avg Session"
              value={`${Math.round(computedStats.avgSessionLength)}m`}
              icon={<Activity className="h-4 w-4" />}
              subtitle="Average duration"
            />
            <PokerStatCard
              title="Best Session"
              value={computedStats.bestSession?.profit || 0}
              statType="profit"
              icon={<TrendingUp className="h-4 w-4" />}
              subtitle="Highest profit"
            />
            <PokerStatCard
              title="Hourly Rate"
              value={advancedStats.hourlyRate}
              statType="profit"
              icon={<DollarSign className="h-4 w-4" />}
              subtitle="Per hour average"
            />
          </div>

          {/* Sessions Table */}
          <DataTable
            data={sessionsChart.data}
            columns={[
              {
                key: 'date',
                title: 'Date',
                sortable: true,
                width: '120px'
              },
              {
                key: 'gameType',
                title: 'Game',
                sortable: true,
                filterable: true,
                width: '120px'
              },
              {
                key: 'stakes',
                title: 'Stakes',
                sortable: true,
                width: '100px'
              },
              {
                key: 'duration',
                title: 'Duration',
                sortable: true,
                width: '100px',
                render: (value: number) => `${Math.round(value)}m`
              },
              {
                key: 'hands',
                title: 'Hands',
                sortable: true,
                width: '80px',
                align: 'right' as const
              },
              {
                key: 'profit',
                title: 'Profit',
                sortable: true,
                width: '100px',
                align: 'right' as const,
                render: (value: number) => (
                  <span className={value >= 0 ? 'text-green-600' : 'text-red-600'}>
                    {value >= 0 ? '+' : ''}${value.toFixed(2)}
                  </span>
                )
              },
              {
                key: 'winRate',
                title: 'Win Rate',
                sortable: true,
                width: '100px',
                align: 'right' as const,
                render: (value: number) => (
                  <span className={value >= 0 ? 'text-green-600' : 'text-red-600'}>
                    {value >= 0 ? '+' : ''}{value.toFixed(1)} BB/100
                  </span>
                )
              }
            ]}
            title="Session History"
            subtitle="Detailed breakdown of all poker sessions"
            loading={sessionsChart.loading}
            pageSize={15}
            searchable={true}
            searchPlaceholder="Search sessions..."
          />
        </TabsContent>

        {/* Trends Tab */}
        <TabsContent value="trends" className="space-y-6">
          {/* Multi-line Performance Comparison */}
          <PokerMultiLineChart
            data={winRateChart.data.map(item => ({
              name: item.session,
              winRate: item.winRate,
              movingAverage: item.movingAverage,
              profit: item.profit,
              hands: item.hands
            }))}
            lines={[
              { dataKey: 'winRate', name: 'Session Win Rate', color: CHART_COLORS.primary },
              { dataKey: 'movingAverage', name: '10-Session Average', color: CHART_COLORS.secondary },
              { dataKey: 'profit', name: 'Session Profit', color: CHART_COLORS.accent }
            ]}
            title="Performance Trends"
            subtitle="Win rate, moving average, and profit over time"
            loading={winRateChart.loading}
            onRefresh={winRateChart.refresh}
            refreshing={winRateChart.loading}
            showBrush={true}
            showLegend={true}
          />

          {/* Volume and Profit Trends */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 sm:gap-6">
            <PokerBarChart
              data={stakesChart.data}
              title="Profit by Stakes"
              subtitle="Total profit at each stakes level"
              loading={stakesChart.loading}
              onRefresh={stakesChart.refresh}
              refreshing={stakesChart.loading}
              dataKey="profit"
              xAxisKey="name"
              color={CHART_COLORS.secondary}
              showValues={true}
            />

            <Card>
              <CardHeader>
                <CardTitle>Trend Analysis</CardTitle>
                <CardDescription>Key performance trends and insights</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                    <div>
                      <p className="font-medium text-green-800">Improving Win Rate</p>
                      <p className="text-sm text-green-600">Last 10 sessions trending upward</p>
                    </div>
                    <TrendingUp className="h-5 w-5 text-green-600" />
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                    <div>
                      <p className="font-medium text-blue-800">Consistent Volume</p>
                      <p className="text-sm text-blue-600">Steady hands per session</p>
                    </div>
                    <Activity className="h-5 w-5 text-blue-600" />
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
                    <div>
                      <p className="font-medium text-yellow-800">Position Awareness</p>
                      <p className="text-sm text-yellow-600">Strong late position play</p>
                    </div>
                    <Target className="h-5 w-5 text-yellow-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* Real-time Status */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-lg sm:text-xl">Real-time Statistics</CardTitle>
          <CardDescription className="text-sm">
            Statistics automatically refresh based on your filter settings
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${
                positionChart.isAutoRefreshing ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
              }`} />
              <span className="text-sm">
                Auto-refresh: {positionChart.isAutoRefreshing ? 'On' : 'Off'}
              </span>
            </div>
            
            {positionChart.lastUpdate && (
              <div className="text-sm text-muted-foreground">
                Last updated: {positionChart.lastUpdate.toLocaleTimeString()}
              </div>
            )}
            
            <Button
              variant="outline"
              size="sm"
              onClick={positionChart.toggleAutoRefresh}
            >
              {positionChart.isAutoRefreshing ? 'Pause Updates' : 'Resume Updates'}
            </Button>
          </div>
        </CardContent>
      </Card>
      
      {/* Export Dialog */}
      <ExportDialog
        isOpen={showExportDialog}
        onClose={() => setShowExportDialog(false)}
        currentFilters={filters}
        title="Export Statistics"
        description="Export your poker statistics and performance data"
      />
    </Container>
  )
}