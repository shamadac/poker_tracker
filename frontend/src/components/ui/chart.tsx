"use client"

import * as React from "react"
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  TooltipProps,
  Brush,
  ReferenceLine,
  ReferenceArea
} from "recharts"
import { Card, CardContent, CardHeader, CardTitle } from "./card"
import { Button } from "./button"
import { cn } from "@/lib/utils"

// Common chart colors
const CHART_COLORS = {
  primary: "#3b82f6",
  secondary: "#10b981",
  accent: "#f59e0b",
  danger: "#ef4444",
  muted: "#6b7280"
}

const PIE_COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"]

// Base chart container
export interface ChartContainerProps {
  title?: string
  subtitle?: string
  className?: string
  children: React.ReactElement
  loading?: boolean
  onRefresh?: () => void
  refreshing?: boolean
  actions?: React.ReactNode
}

export const ChartContainer = React.forwardRef<HTMLDivElement, ChartContainerProps>(
  ({ title, subtitle, className, children, loading = false, onRefresh, refreshing = false, actions }, ref) => {
    if (loading) {
      return (
        <Card ref={ref} className={className}>
          {title && (
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>{title}</CardTitle>
                  {subtitle && <p className="text-sm text-muted-foreground">{subtitle}</p>}
                </div>
                {actions}
              </div>
            </CardHeader>
          )}
          <CardContent>
            <div className="h-64 flex items-center justify-center">
              <div className="animate-pulse text-muted-foreground">Loading chart...</div>
            </div>
          </CardContent>
        </Card>
      )
    }

    return (
      <Card ref={ref} className={className}>
        {title && (
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>{title}</CardTitle>
                {subtitle && <p className="text-sm text-muted-foreground">{subtitle}</p>}
              </div>
              <div className="flex items-center gap-2">
                {onRefresh && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={onRefresh}
                    disabled={refreshing}
                    className="h-8 px-2"
                  >
                    {refreshing ? (
                      <div className="animate-spin h-4 w-4 border-2 border-current border-t-transparent rounded-full" />
                    ) : (
                      "Refresh"
                    )}
                  </Button>
                )}
                {actions}
              </div>
            </div>
          </CardHeader>
        )}
        <CardContent>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              {children}
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    )
  }
)

ChartContainer.displayName = "ChartContainer"

// Custom tooltip component with enhanced interactivity
const CustomTooltip = ({ active, payload, label }: TooltipProps<any, any>) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-background border border-border rounded-lg shadow-lg p-3 min-w-[120px]">
        <p className="font-medium text-foreground mb-1">{label}</p>
        {payload.map((entry, index) => (
          <div key={index} className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-1">
              <div 
                className="w-2 h-2 rounded-full" 
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-sm text-muted-foreground">{entry.name}:</span>
            </div>
            <span className="text-sm font-medium" style={{ color: entry.color }}>
              {typeof entry.value === 'number' ? entry.value.toFixed(2) : entry.value}
            </span>
          </div>
        ))}
      </div>
    )
  }
  return null
}

// Enhanced tooltip for percentage values
const PercentageTooltip = ({ active, payload, label }: TooltipProps<any, any>) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-background border border-border rounded-lg shadow-lg p-3 min-w-[120px]">
        <p className="font-medium text-foreground mb-1">{label}</p>
        {payload.map((entry, index) => (
          <div key={index} className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-1">
              <div 
                className="w-2 h-2 rounded-full" 
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-sm text-muted-foreground">{entry.name}:</span>
            </div>
            <span className="text-sm font-medium" style={{ color: entry.color }}>
              {typeof entry.value === 'number' ? `${entry.value.toFixed(1)}%` : entry.value}
            </span>
          </div>
        ))}
      </div>
    )
  }
  return null
}

// Line Chart Component with enhanced interactivity
export interface LineChartData {
  name: string
  value: number
  [key: string]: any
}

export interface PokerLineChartProps {
  data: LineChartData[]
  title?: string
  subtitle?: string
  dataKey?: string
  xAxisKey?: string
  className?: string
  loading?: boolean
  color?: string
  onRefresh?: () => void
  refreshing?: boolean
  showBrush?: boolean
  showGrid?: boolean
  animated?: boolean
  onClick?: (data: any) => void
}

export const PokerLineChart = React.forwardRef<HTMLDivElement, PokerLineChartProps>(
  ({ 
    data, 
    title, 
    subtitle, 
    dataKey = "value", 
    xAxisKey = "name", 
    className, 
    loading = false,
    color = CHART_COLORS.primary,
    onRefresh,
    refreshing = false,
    showBrush = false,
    showGrid = true,
    animated = true,
    onClick
  }, ref) => {
    const handleClick = (data: any) => {
      if (onClick) {
        onClick(data)
      }
    }

    return (
      <ChartContainer 
        ref={ref} 
        title={title} 
        subtitle={subtitle} 
        className={className} 
        loading={loading}
        onRefresh={onRefresh}
        refreshing={refreshing}
      >
        <LineChart data={data} onClick={handleClick}>
          {showGrid && <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />}
          <XAxis 
            dataKey={xAxisKey} 
            className="text-xs fill-muted-foreground"
            tick={{ fontSize: 12 }}
          />
          <YAxis 
            className="text-xs fill-muted-foreground"
            tick={{ fontSize: 12 }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Line 
            type="monotone" 
            dataKey={dataKey} 
            stroke={color}
            strokeWidth={2}
            dot={{ fill: color, strokeWidth: 2, r: 4 }}
            activeDot={{ r: 6, stroke: color, strokeWidth: 2 }}
            animationDuration={animated ? 1000 : 0}
          />
          {showBrush && <Brush dataKey={xAxisKey} height={30} stroke={color} />}
        </LineChart>
      </ChartContainer>
    )
  }
)

PokerLineChart.displayName = "PokerLineChart"

// Area Chart Component with enhanced interactivity
export interface PokerAreaChartProps extends PokerLineChartProps {
  fillOpacity?: number
  showGradient?: boolean
}

export const PokerAreaChart = React.forwardRef<HTMLDivElement, PokerAreaChartProps>(
  ({ 
    data, 
    title, 
    subtitle, 
    dataKey = "value", 
    xAxisKey = "name", 
    className, 
    loading = false,
    color = CHART_COLORS.primary,
    fillOpacity = 0.3,
    showGradient = true,
    onRefresh,
    refreshing = false,
    showBrush = false,
    showGrid = true,
    animated = true,
    onClick
  }, ref) => {
    const gradientId = `gradient-${Math.random().toString(36).substr(2, 9)}`
    
    const handleClick = (data: any) => {
      if (onClick) {
        onClick(data)
      }
    }

    return (
      <ChartContainer 
        ref={ref} 
        title={title} 
        subtitle={subtitle} 
        className={className} 
        loading={loading}
        onRefresh={onRefresh}
        refreshing={refreshing}
      >
        <AreaChart data={data} onClick={handleClick}>
          <defs>
            {showGradient && (
              <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={fillOpacity * 2} />
                <stop offset="95%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            )}
          </defs>
          {showGrid && <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />}
          <XAxis 
            dataKey={xAxisKey} 
            className="text-xs fill-muted-foreground"
            tick={{ fontSize: 12 }}
          />
          <YAxis 
            className="text-xs fill-muted-foreground"
            tick={{ fontSize: 12 }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area 
            type="monotone" 
            dataKey={dataKey} 
            stroke={color}
            fill={showGradient ? `url(#${gradientId})` : color}
            fillOpacity={showGradient ? 1 : fillOpacity}
            strokeWidth={2}
            animationDuration={animated ? 1000 : 0}
          />
          {showBrush && <Brush dataKey={xAxisKey} height={30} stroke={color} />}
        </AreaChart>
      </ChartContainer>
    )
  }
)

PokerAreaChart.displayName = "PokerAreaChart"

// Bar Chart Component with enhanced interactivity
export interface PokerBarChartProps extends PokerLineChartProps {
  horizontal?: boolean
  showValues?: boolean
}

export const PokerBarChart = React.forwardRef<HTMLDivElement, PokerBarChartProps>(
  ({ 
    data, 
    title, 
    subtitle, 
    dataKey = "value", 
    xAxisKey = "name", 
    className, 
    loading = false,
    color = CHART_COLORS.primary,
    horizontal = false,
    showValues = false,
    onRefresh,
    refreshing = false,
    showGrid = true,
    animated = true,
    onClick
  }, ref) => {
    const handleClick = (data: any) => {
      if (onClick) {
        onClick(data)
      }
    }

    return (
      <ChartContainer 
        ref={ref} 
        title={title} 
        subtitle={subtitle} 
        className={className} 
        loading={loading}
        onRefresh={onRefresh}
        refreshing={refreshing}
      >
        <BarChart data={data} layout={horizontal ? "horizontal" : "vertical"} onClick={handleClick}>
          {showGrid && <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />}
          <XAxis 
            dataKey={horizontal ? dataKey : xAxisKey}
            type={horizontal ? "number" : "category"}
            className="text-xs fill-muted-foreground"
            tick={{ fontSize: 12 }}
          />
          <YAxis 
            dataKey={horizontal ? xAxisKey : dataKey}
            type={horizontal ? "category" : "number"}
            className="text-xs fill-muted-foreground"
            tick={{ fontSize: 12 }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar 
            dataKey={dataKey} 
            fill={color} 
            radius={[2, 2, 0, 0]}
            animationDuration={animated ? 1000 : 0}
          />
        </BarChart>
      </ChartContainer>
    )
  }
)

PokerBarChart.displayName = "PokerBarChart"

// Pie Chart Component with enhanced interactivity
export interface PieChartData {
  name: string
  value: number
  color?: string
}

export interface PokerPieChartProps {
  data: PieChartData[]
  title?: string
  subtitle?: string
  className?: string
  loading?: boolean
  showLegend?: boolean
  onRefresh?: () => void
  refreshing?: boolean
  animated?: boolean
  onClick?: (data: any) => void
  innerRadius?: number
  outerRadius?: number
}

export const PokerPieChart = React.forwardRef<HTMLDivElement, PokerPieChartProps>(
  ({ 
    data, 
    title, 
    subtitle, 
    className, 
    loading = false, 
    showLegend = true,
    onRefresh,
    refreshing = false,
    animated = true,
    onClick,
    innerRadius = 0,
    outerRadius = 80
  }, ref) => {
    const [activeIndex, setActiveIndex] = React.useState<number | null>(null)

    const handleMouseEnter = (_: any, index: number) => {
      setActiveIndex(index)
    }

    const handleMouseLeave = () => {
      setActiveIndex(null)
    }

    const handleClick = (data: any) => {
      if (onClick) {
        onClick(data)
      }
    }

    return (
      <ChartContainer 
        ref={ref} 
        title={title} 
        subtitle={subtitle} 
        className={className} 
        loading={loading}
        onRefresh={onRefresh}
        refreshing={refreshing}
      >
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={innerRadius}
            outerRadius={outerRadius}
            fill="#8884d8"
            dataKey="value"
            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
            onClick={handleClick}
            animationDuration={animated ? 1000 : 0}
          >
            {data.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={entry.color || PIE_COLORS[index % PIE_COLORS.length]}
                stroke={activeIndex === index ? "#333" : "none"}
                strokeWidth={activeIndex === index ? 2 : 0}
              />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          {showLegend && <Legend />}
        </PieChart>
      </ChartContainer>
    )
  }
)

PokerPieChart.displayName = "PokerPieChart"

// Multi-line chart for comparing multiple metrics with enhanced interactivity
export interface MultiLineData {
  name: string
  [key: string]: any
}

export interface PokerMultiLineChartProps {
  data: MultiLineData[]
  lines: Array<{
    dataKey: string
    name: string
    color: string
  }>
  title?: string
  subtitle?: string
  xAxisKey?: string
  className?: string
  loading?: boolean
  onRefresh?: () => void
  refreshing?: boolean
  showBrush?: boolean
  showGrid?: boolean
  animated?: boolean
  onClick?: (data: any) => void
  showLegend?: boolean
}

export const PokerMultiLineChart = React.forwardRef<HTMLDivElement, PokerMultiLineChartProps>(
  ({ 
    data, 
    lines, 
    title, 
    subtitle, 
    xAxisKey = "name", 
    className, 
    loading = false,
    onRefresh,
    refreshing = false,
    showBrush = false,
    showGrid = true,
    animated = true,
    onClick,
    showLegend = true
  }, ref) => {
    const [hiddenLines, setHiddenLines] = React.useState<Set<string>>(new Set())

    const handleLegendClick = (dataKey: any) => {
      if (!dataKey || typeof dataKey !== 'string') return
      
      const newHiddenLines = new Set(hiddenLines)
      if (hiddenLines.has(dataKey)) {
        newHiddenLines.delete(dataKey)
      } else {
        newHiddenLines.add(dataKey)
      }
      setHiddenLines(newHiddenLines)
    }

    const handleClick = (data: any) => {
      if (onClick) {
        onClick(data)
      }
    }

    return (
      <ChartContainer 
        ref={ref} 
        title={title} 
        subtitle={subtitle} 
        className={className} 
        loading={loading}
        onRefresh={onRefresh}
        refreshing={refreshing}
      >
        <LineChart data={data} onClick={handleClick}>
          {showGrid && <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />}
          <XAxis 
            dataKey={xAxisKey} 
            className="text-xs fill-muted-foreground"
            tick={{ fontSize: 12 }}
          />
          <YAxis 
            className="text-xs fill-muted-foreground"
            tick={{ fontSize: 12 }}
          />
          <Tooltip content={<CustomTooltip />} />
          {showLegend && (
            <Legend 
              onClick={(e) => handleLegendClick(e.dataKey)}
              wrapperStyle={{ cursor: 'pointer' }}
            />
          )}
          {lines.map((line, index) => (
            <Line
              key={index}
              type="monotone"
              dataKey={line.dataKey}
              name={line.name}
              stroke={line.color}
              strokeWidth={2}
              dot={{ fill: line.color, strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, stroke: line.color, strokeWidth: 2 }}
              hide={hiddenLines.has(line.dataKey)}
              animationDuration={animated ? 1000 : 0}
            />
          ))}
          {showBrush && <Brush dataKey={xAxisKey} height={30} />}
        </LineChart>
      </ChartContainer>
    )
  }
)

PokerMultiLineChart.displayName = "PokerMultiLineChart"

// Specialized Poker Statistics Charts

// Position-based performance chart
export interface PositionData {
  position: string
  winRate: number
  vpip: number
  pfr: number
  hands: number
}

export interface PokerPositionChartProps {
  data: PositionData[]
  title?: string
  subtitle?: string
  className?: string
  loading?: boolean
  onRefresh?: () => void
  refreshing?: boolean
  metric?: 'winRate' | 'vpip' | 'pfr'
}

export const PokerPositionChart = React.forwardRef<HTMLDivElement, PokerPositionChartProps>(
  ({ 
    data, 
    title = "Position Analysis", 
    subtitle = "Performance by table position",
    className, 
    loading = false,
    onRefresh,
    refreshing = false,
    metric = 'winRate'
  }, ref) => {
    const getColor = (value: number) => {
      if (metric === 'winRate') {
        return value > 0 ? CHART_COLORS.secondary : CHART_COLORS.danger
      }
      return CHART_COLORS.primary
    }

    const formatValue = (value: number) => {
      if (metric === 'winRate') {
        return `${value > 0 ? '+' : ''}${value.toFixed(1)} BB/100`
      }
      return `${value.toFixed(1)}%`
    }

    return (
      <ChartContainer 
        ref={ref} 
        title={title} 
        subtitle={subtitle} 
        className={className} 
        loading={loading}
        onRefresh={onRefresh}
        refreshing={refreshing}
      >
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
          <XAxis 
            dataKey="position" 
            className="text-xs fill-muted-foreground"
            tick={{ fontSize: 12 }}
          />
          <YAxis 
            className="text-xs fill-muted-foreground"
            tick={{ fontSize: 12 }}
          />
          <Tooltip 
            content={({ active, payload, label }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload
                return (
                  <div className="bg-background border border-border rounded-lg shadow-lg p-3">
                    <p className="font-medium text-foreground mb-2">{label}</p>
                    <div className="space-y-1">
                      <p className="text-sm">Win Rate: {formatValue(data.winRate)}</p>
                      <p className="text-sm">VPIP: {data.vpip.toFixed(1)}%</p>
                      <p className="text-sm">PFR: {data.pfr.toFixed(1)}%</p>
                      <p className="text-sm">Hands: {data.hands}</p>
                    </div>
                  </div>
                )
              }
              return null
            }}
          />
          <Bar 
            dataKey={metric} 
            fill={CHART_COLORS.primary}
            radius={[2, 2, 0, 0]}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getColor(entry[metric])} />
            ))}
          </Bar>
        </BarChart>
      </ChartContainer>
    )
  }
)

PokerPositionChart.displayName = "PokerPositionChart"

// Win rate trend chart with moving average
export interface WinRateTrendData {
  session: string
  winRate: number
  movingAverage: number
  hands: number
  date: string
}

export interface PokerWinRateTrendProps {
  data: WinRateTrendData[]
  title?: string
  subtitle?: string
  className?: string
  loading?: boolean
  onRefresh?: () => void
  refreshing?: boolean
  showMovingAverage?: boolean
  period?: number
}

export const PokerWinRateTrend = React.forwardRef<HTMLDivElement, PokerWinRateTrendProps>(
  ({ 
    data, 
    title = "Win Rate Trend", 
    subtitle = "Performance over time with moving average",
    className, 
    loading = false,
    onRefresh,
    refreshing = false,
    showMovingAverage = true,
    period = 10
  }, ref) => {
    return (
      <ChartContainer 
        ref={ref} 
        title={title} 
        subtitle={subtitle} 
        className={className} 
        loading={loading}
        onRefresh={onRefresh}
        refreshing={refreshing}
      >
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
          <XAxis 
            dataKey="session" 
            className="text-xs fill-muted-foreground"
            tick={{ fontSize: 12 }}
          />
          <YAxis 
            className="text-xs fill-muted-foreground"
            tick={{ fontSize: 12 }}
          />
          <Tooltip 
            content={({ active, payload, label }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload
                return (
                  <div className="bg-background border border-border rounded-lg shadow-lg p-3">
                    <p className="font-medium text-foreground mb-2">Session {label}</p>
                    <div className="space-y-1">
                      <p className="text-sm">Date: {data.date}</p>
                      <p className="text-sm">Win Rate: {data.winRate > 0 ? '+' : ''}{data.winRate.toFixed(1)} BB/100</p>
                      {showMovingAverage && (
                        <p className="text-sm">MA({period}): {data.movingAverage > 0 ? '+' : ''}{data.movingAverage.toFixed(1)} BB/100</p>
                      )}
                      <p className="text-sm">Hands: {data.hands}</p>
                    </div>
                  </div>
                )
              }
              return null
            }}
          />
          <ReferenceLine y={0} stroke="#666" strokeDasharray="2 2" />
          <Line 
            type="monotone" 
            dataKey="winRate" 
            stroke={CHART_COLORS.primary}
            strokeWidth={1}
            dot={{ fill: CHART_COLORS.primary, strokeWidth: 1, r: 2 }}
            name="Win Rate"
          />
          {showMovingAverage && (
            <Line 
              type="monotone" 
              dataKey="movingAverage" 
              stroke={CHART_COLORS.secondary}
              strokeWidth={2}
              dot={false}
              name={`${period}-Session MA`}
            />
          )}
          <Legend />
        </LineChart>
      </ChartContainer>
    )
  }
)

PokerWinRateTrend.displayName = "PokerWinRateTrend"

// Heatmap-style chart for hourly performance
export interface HourlyData {
  hour: number
  day: string
  winRate: number
  hands: number
  sessions: number
}

export interface PokerHeatmapProps {
  data: HourlyData[]
  title?: string
  subtitle?: string
  className?: string
  loading?: boolean
  onRefresh?: () => void
  refreshing?: boolean
}

export const PokerHeatmap = React.forwardRef<HTMLDivElement, PokerHeatmapProps>(
  ({ 
    data, 
    title = "Performance Heatmap", 
    subtitle = "Win rate by day and hour",
    className, 
    loading = false,
    onRefresh,
    refreshing = false
  }, ref) => {
    // Transform data for heatmap visualization
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    const hours = Array.from({ length: 24 }, (_, i) => i)
    
    const getIntensity = (winRate: number) => {
      const normalized = Math.max(0, Math.min(1, (winRate + 10) / 20)) // Normalize -10 to +10 range
      return normalized
    }

    const getColor = (winRate: number) => {
      if (winRate > 5) return '#22c55e' // Green for good performance
      if (winRate > 0) return '#84cc16' // Light green for positive
      if (winRate > -5) return '#f59e0b' // Yellow for slightly negative
      return '#ef4444' // Red for poor performance
    }

    return (
      <ChartContainer 
        ref={ref} 
        title={title} 
        subtitle={subtitle} 
        className={className} 
        loading={loading}
        onRefresh={onRefresh}
        refreshing={refreshing}
      >
        <div className="w-full h-full p-4">
          <div className="grid gap-1 h-full" style={{ gridTemplateColumns: 'auto repeat(24, 1fr)' }}>
            {/* Hour labels */}
            <div></div>
            {hours.map(hour => (
              <div key={hour} className="text-xs text-center text-muted-foreground">
                {hour}
              </div>
            ))}
            
            {/* Data grid */}
            {days.map(day => (
              <React.Fragment key={day}>
                <div className="text-xs text-muted-foreground flex items-center">
                  {day}
                </div>
                {hours.map(hour => {
                  const cellData = data.find(d => d.day === day && d.hour === hour)
                  const winRate = cellData?.winRate || 0
                  const hands = cellData?.hands || 0
                  
                  return (
                    <div
                      key={`${day}-${hour}`}
                      className="aspect-square rounded-sm border border-border cursor-pointer hover:border-foreground transition-colors"
                      style={{ 
                        backgroundColor: hands > 0 ? getColor(winRate) : '#f3f4f6',
                        opacity: hands > 0 ? 0.8 : 0.3
                      }}
                      title={`${day} ${hour}:00 - ${hands} hands, ${winRate > 0 ? '+' : ''}${winRate.toFixed(1)} BB/100`}
                    />
                  )
                })}
              </React.Fragment>
            ))}
          </div>
        </div>
      </ChartContainer>
    )
  }
)

PokerHeatmap.displayName = "PokerHeatmap"

export { CHART_COLORS, PercentageTooltip }