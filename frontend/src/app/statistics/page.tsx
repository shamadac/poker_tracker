"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Container } from "@/components/ui/container"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { ExportDialog } from "@/components/ui/export-dialog"
import { PokerStatCard } from "@/components/ui/stat-card"
import { useState, useEffect } from "react"
import { Download, Filter, RefreshCw, TrendingUp, Target, Activity, DollarSign, BarChart3 } from "lucide-react"
import { api } from "@/lib/api-client"

// Statistics interfaces
interface StatisticsFilters {
  dateRange: string
  gameType: string
  stakes: string
  position: string
  sessionType: string
}

interface StatsSummary {
  total_hands: number
  win_rate: number
  vpip: number
  pfr: number
  last_updated: string
  best_position?: string
  worst_position?: string
  trending_up: string[]
  trending_down: string[]
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
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statsSummary, setStatsSummary] = useState<StatsSummary | null>(null)

  // Fetch statistics summary
  const fetchStatsSummary = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.statistics.getSummary()
      setStatsSummary(response.data)
    } catch (err: any) {
      console.error('Error fetching statistics:', err)
      setError(err.response?.data?.detail || 'Failed to load statistics')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStatsSummary()
  }, [])

  // Filter handlers
  const handleFilterChange = (filterType: keyof StatisticsFilters, value: string) => {
    setFilters(prev => ({
      ...prev,
      [filterType]: value
    }))
  }

  const applyFilters = () => {
    fetchStatsSummary()
  }

  const handleExport = async (format: 'pdf' | 'csv') => {
    setIsExporting(true)
    try {
      await api.statistics.exportStats(format, filters)
      alert(`Statistics exported as ${format.toUpperCase()}`)
    } catch (error) {
      console.error('Export failed:', error)
      alert('Export failed. Please try again.')
    } finally {
      setIsExporting(false)
    }
  }

  if (loading) {
    return (
      <Container className="py-4 sm:py-6 lg:py-8">
        <div className="mb-6 sm:mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold">Statistics</h1>
          <p className="text-muted-foreground text-sm sm:text-base">
            Loading your poker statistics...
          </p>
        </div>
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="h-8 w-8 animate-spin" />
        </div>
      </Container>
    )
  }

  if (error) {
    return (
      <Container className="py-4 sm:py-6 lg:py-8">
        <div className="mb-6 sm:mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold">Statistics</h1>
          <p className="text-muted-foreground text-sm sm:text-base">
            Error loading statistics
          </p>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-red-600 mb-4">{error}</p>
              <Button onClick={fetchStatsSummary}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Try Again
              </Button>
            </div>
          </CardContent>
        </Card>
      </Container>
    )
  }

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
            {Object.values(filters).some(f => f !== 'all' && f !== '30d') && (
              <Badge variant="secondary" className="ml-2">
                Filters Active
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Statistics Overview */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="details">Details</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {/* Key Statistics Cards */}
          {statsSummary && (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 lg:gap-6">
              <PokerStatCard
                title="Total Hands"
                value={statsSummary.total_hands}
                icon={<Activity className="h-4 w-4" />}
                subtitle="All time hands played"
              />
              <PokerStatCard
                title="VPIP"
                value={statsSummary.vpip}
                statType="vpip"
                icon={<Target className="h-4 w-4" />}
                subtitle="Voluntarily Put $ In Pot"
              />
              <PokerStatCard
                title="PFR"
                value={statsSummary.pfr}
                statType="pfr"
                icon={<TrendingUp className="h-4 w-4" />}
                subtitle="Pre-Flop Raise"
              />
              <PokerStatCard
                title="Win Rate"
                value={statsSummary.win_rate}
                statType="winrate"
                icon={<BarChart3 className="h-4 w-4" />}
                subtitle="BB/100 hands"
              />
            </div>
          )}

          {/* Position Performance */}
          {statsSummary && (statsSummary.best_position || statsSummary.worst_position) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {statsSummary.best_position && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg text-green-600">Best Position</CardTitle>
                    <CardDescription>Your most profitable position</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{statsSummary.best_position}</div>
                  </CardContent>
                </Card>
              )}
              
              {statsSummary.worst_position && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg text-red-600">Worst Position</CardTitle>
                    <CardDescription>Position needing improvement</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{statsSummary.worst_position}</div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}

          {/* Trending Metrics */}
          {statsSummary && (statsSummary.trending_up.length > 0 || statsSummary.trending_down.length > 0) && (
            <Card>
              <CardHeader>
                <CardTitle>Performance Trends</CardTitle>
                <CardDescription>Metrics showing significant changes</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {statsSummary.trending_up.length > 0 && (
                    <div>
                      <h4 className="font-medium text-green-600 mb-2">Trending Up</h4>
                      <div className="space-y-1">
                        {statsSummary.trending_up.map((metric) => (
                          <Badge key={metric} variant="secondary" className="mr-2">
                            {metric}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {statsSummary.trending_down.length > 0 && (
                    <div>
                      <h4 className="font-medium text-red-600 mb-2">Trending Down</h4>
                      <div className="space-y-1">
                        {statsSummary.trending_down.map((metric) => (
                          <Badge key={metric} variant="secondary" className="mr-2">
                            {metric}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Details Tab */}
        <TabsContent value="details" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Detailed Statistics</CardTitle>
              <CardDescription>
                Upload some hand histories to see detailed statistics and analysis
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <Activity className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground mb-4">
                  No hand history data available yet
                </p>
                <Button variant="outline">
                  Upload Hand Histories
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Last Updated */}
      {statsSummary && (
        <Card className="mt-6">
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground text-center">
              Last updated: {new Date(statsSummary.last_updated).toLocaleString()}
            </div>
          </CardContent>
        </Card>
      )}
      
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