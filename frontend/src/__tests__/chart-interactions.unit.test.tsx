/**
 * Unit Test for Chart Interactions
 * **Validates: Requirements 6.2**
 * 
 * Tests interactive chart functionality including clicks, hovers, tooltips,
 * legend interactions, and real-time updates
 */

import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
  ChartContainer,
  PokerLineChart,
  PokerAreaChart,
  PokerBarChart,
  PokerPieChart,
  PokerMultiLineChart,
  PokerPositionChart,
  PokerWinRateTrend,
  PokerHeatmap
} from '@/components/ui/chart'

// Mock recharts to avoid canvas issues in tests
jest.mock('recharts', () => ({
  ...jest.requireActual('recharts'),
  ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
  LineChart: ({ children, onClick }: any) => (
    <div data-testid="line-chart" onClick={onClick}>
      {children}
    </div>
  ),
  AreaChart: ({ children, onClick }: any) => (
    <div data-testid="area-chart" onClick={onClick}>
      {children}
    </div>
  ),
  BarChart: ({ children, onClick }: any) => (
    <div data-testid="bar-chart" onClick={onClick}>
      {children}
    </div>
  ),
  PieChart: ({ children }: any) => (
    <div data-testid="pie-chart">
      {children}
    </div>
  ),
  Line: ({ onClick }: any) => <div data-testid="line" onClick={onClick} />,
  Area: ({ onClick }: any) => <div data-testid="area" onClick={onClick} />,
  Bar: ({ onClick }: any) => <div data-testid="bar" onClick={onClick} />,
  Pie: ({ onClick, onMouseEnter, onMouseLeave }: any) => (
    <div 
      data-testid="pie" 
      onClick={onClick}
      onMouseEnter={() => onMouseEnter({}, 0)}
      onMouseLeave={onMouseLeave}
    />
  ),
  Cell: () => <div data-testid="cell" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: ({ onClick }: any) => (
    <div data-testid="legend" onClick={() => onClick({ dataKey: 'testKey' })} />
  ),
  Brush: () => <div data-testid="brush" />,
  ReferenceLine: () => <div data-testid="reference-line" />,
  ReferenceArea: () => <div data-testid="reference-area" />,
}))

// Sample data for testing
const sampleLineData = [
  { name: 'Jan', value: 400 },
  { name: 'Feb', value: 300 },
  { name: 'Mar', value: 200 },
  { name: 'Apr', value: 278 },
  { name: 'May', value: 189 },
]

const samplePieData = [
  { name: 'Group A', value: 400, color: '#8884d8' },
  { name: 'Group B', value: 300, color: '#82ca9d' },
  { name: 'Group C', value: 300, color: '#ffc658' },
  { name: 'Group D', value: 200, color: '#ff7300' },
]

const sampleMultiLineData = [
  { name: 'Jan', vpip: 24, pfr: 18, winRate: 5.2 },
  { name: 'Feb', vpip: 26, pfr: 20, winRate: 3.8 },
  { name: 'Mar', vpip: 22, pfr: 16, winRate: 7.1 },
]

const sampleMultiLines = [
  { dataKey: 'vpip', name: 'VPIP', color: '#8884d8' },
  { dataKey: 'pfr', name: 'PFR', color: '#82ca9d' },
  { dataKey: 'winRate', name: 'Win Rate', color: '#ffc658' },
]

const samplePositionData = [
  { position: 'UTG', winRate: -2.5, vpip: 12.5, pfr: 10.2, hands: 150 },
  { position: 'MP', winRate: 1.8, vpip: 18.3, pfr: 14.7, hands: 200 },
  { position: 'CO', winRate: 4.2, vpip: 25.1, pfr: 19.8, hands: 180 },
  { position: 'BTN', winRate: 8.7, vpip: 32.4, pfr: 24.6, hands: 220 },
]

const sampleWinRateData = [
  { session: '1', winRate: 5.2, movingAverage: 5.2, hands: 100, date: '2024-01-01' },
  { session: '2', winRate: -2.1, movingAverage: 1.55, hands: 150, date: '2024-01-02' },
  { session: '3', winRate: 8.4, movingAverage: 3.83, hands: 120, date: '2024-01-03' },
]

const sampleHeatmapData = [
  { hour: 10, day: 'Mon', winRate: 5.2, hands: 50, sessions: 2 },
  { hour: 14, day: 'Mon', winRate: -1.8, hands: 75, sessions: 3 },
  { hour: 20, day: 'Tue', winRate: 8.1, hands: 100, sessions: 4 },
]

describe('Chart Interactions Unit Tests', () => {
  beforeEach(() => {
    cleanup()
  })

  afterEach(() => {
    cleanup()
  })

  describe('ChartContainer', () => {
    it('should render with title and subtitle', () => {
      render(
        <ChartContainer title="Test Chart" subtitle="Test subtitle">
          <div data-testid="chart-content">Chart Content</div>
        </ChartContainer>
      )

      expect(screen.getByText('Test Chart')).toBeInTheDocument()
      expect(screen.getByText('Test subtitle')).toBeInTheDocument()
      expect(screen.getByTestId('chart-content')).toBeInTheDocument()
    })

    it('should show loading state', () => {
      render(
        <ChartContainer title="Test Chart" loading={true}>
          <div data-testid="chart-content">Chart Content</div>
        </ChartContainer>
      )

      expect(screen.getByText('Loading chart...')).toBeInTheDocument()
      expect(screen.queryByTestId('chart-content')).not.toBeInTheDocument()
    })

    it('should handle refresh functionality', async () => {
      const user = userEvent.setup()
      const mockRefresh = jest.fn()

      render(
        <ChartContainer title="Test Chart" onRefresh={mockRefresh} refreshing={false}>
          <div data-testid="chart-content">Chart Content</div>
        </ChartContainer>
      )

      const refreshButton = screen.getByText('Refresh')
      expect(refreshButton).toBeInTheDocument()

      await user.click(refreshButton)
      expect(mockRefresh).toHaveBeenCalledTimes(1)
    })

    it('should show refreshing state', () => {
      const mockRefresh = jest.fn()

      render(
        <ChartContainer title="Test Chart" onRefresh={mockRefresh} refreshing={true}>
          <div data-testid="chart-content">Chart Content</div>
        </ChartContainer>
      )

      const refreshButton = screen.getByRole('button')
      expect(refreshButton).toBeDisabled()
      expect(refreshButton.querySelector('.animate-spin')).toBeInTheDocument()
    })

    it('should render custom actions', () => {
      const customAction = <button data-testid="custom-action">Custom Action</button>

      render(
        <ChartContainer title="Test Chart" actions={customAction}>
          <div data-testid="chart-content">Chart Content</div>
        </ChartContainer>
      )

      expect(screen.getByTestId('custom-action')).toBeInTheDocument()
    })
  })

  describe('PokerLineChart', () => {
    it('should render line chart with data', () => {
      render(
        <PokerLineChart
          data={sampleLineData}
          title="Line Chart Test"
          dataKey="value"
          xAxisKey="name"
        />
      )

      expect(screen.getByText('Line Chart Test')).toBeInTheDocument()
      expect(screen.getByTestId('line-chart')).toBeInTheDocument()
      expect(screen.getByTestId('line')).toBeInTheDocument()
    })

    it('should handle click interactions', async () => {
      const user = userEvent.setup()
      const mockClick = jest.fn()

      render(
        <PokerLineChart
          data={sampleLineData}
          title="Interactive Line Chart"
          onClick={mockClick}
        />
      )

      const chart = screen.getByTestId('line-chart')
      await user.click(chart)

      expect(mockClick).toHaveBeenCalledTimes(1)
    })

    it('should show brush when enabled', () => {
      render(
        <PokerLineChart
          data={sampleLineData}
          title="Line Chart with Brush"
          showBrush={true}
        />
      )

      expect(screen.getByTestId('brush')).toBeInTheDocument()
    })

    it('should show grid when enabled', () => {
      render(
        <PokerLineChart
          data={sampleLineData}
          title="Line Chart with Grid"
          showGrid={true}
        />
      )

      expect(screen.getByTestId('cartesian-grid')).toBeInTheDocument()
    })
  })

  describe('PokerAreaChart', () => {
    it('should render area chart with gradient', () => {
      render(
        <PokerAreaChart
          data={sampleLineData}
          title="Area Chart Test"
          showGradient={true}
        />
      )

      expect(screen.getByText('Area Chart Test')).toBeInTheDocument()
      expect(screen.getByTestId('area-chart')).toBeInTheDocument()
      expect(screen.getByTestId('area')).toBeInTheDocument()
    })

    it('should handle click interactions', async () => {
      const user = userEvent.setup()
      const mockClick = jest.fn()

      render(
        <PokerAreaChart
          data={sampleLineData}
          title="Interactive Area Chart"
          onClick={mockClick}
        />
      )

      const chart = screen.getByTestId('area-chart')
      await user.click(chart)

      expect(mockClick).toHaveBeenCalledTimes(1)
    })
  })

  describe('PokerBarChart', () => {
    it('should render bar chart', () => {
      render(
        <PokerBarChart
          data={sampleLineData}
          title="Bar Chart Test"
        />
      )

      expect(screen.getByText('Bar Chart Test')).toBeInTheDocument()
      expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
      expect(screen.getByTestId('bar')).toBeInTheDocument()
    })

    it('should handle horizontal layout', () => {
      render(
        <PokerBarChart
          data={sampleLineData}
          title="Horizontal Bar Chart"
          horizontal={true}
        />
      )

      expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
    })

    it('should handle click interactions', async () => {
      const user = userEvent.setup()
      const mockClick = jest.fn()

      render(
        <PokerBarChart
          data={sampleLineData}
          title="Interactive Bar Chart"
          onClick={mockClick}
        />
      )

      const chart = screen.getByTestId('bar-chart')
      await user.click(chart)

      expect(mockClick).toHaveBeenCalledTimes(1)
    })
  })

  describe('PokerPieChart', () => {
    it('should render pie chart with legend', () => {
      render(
        <PokerPieChart
          data={samplePieData}
          title="Pie Chart Test"
          showLegend={true}
        />
      )

      expect(screen.getByText('Pie Chart Test')).toBeInTheDocument()
      expect(screen.getByTestId('pie-chart')).toBeInTheDocument()
      expect(screen.getByTestId('pie')).toBeInTheDocument()
      expect(screen.getByTestId('legend')).toBeInTheDocument()
    })

    it('should handle mouse interactions', async () => {
      const user = userEvent.setup()

      render(
        <PokerPieChart
          data={samplePieData}
          title="Interactive Pie Chart"
        />
      )

      const pie = screen.getByTestId('pie')
      
      // Test mouse enter and leave
      await user.hover(pie)
      await user.unhover(pie)

      expect(pie).toBeInTheDocument()
    })

    it('should handle click interactions', async () => {
      const user = userEvent.setup()
      const mockClick = jest.fn()

      render(
        <PokerPieChart
          data={samplePieData}
          title="Clickable Pie Chart"
          onClick={mockClick}
        />
      )

      const pie = screen.getByTestId('pie')
      await user.click(pie)

      expect(mockClick).toHaveBeenCalledTimes(1)
    })

    it('should render as donut chart with inner radius', () => {
      render(
        <PokerPieChart
          data={samplePieData}
          title="Donut Chart"
          innerRadius={40}
          outerRadius={80}
        />
      )

      expect(screen.getByTestId('pie')).toBeInTheDocument()
    })
  })

  describe('PokerMultiLineChart', () => {
    it('should render multi-line chart with legend', () => {
      render(
        <PokerMultiLineChart
          data={sampleMultiLineData}
          lines={sampleMultiLines}
          title="Multi-Line Chart Test"
          showLegend={true}
        />
      )

      expect(screen.getByText('Multi-Line Chart Test')).toBeInTheDocument()
      expect(screen.getByTestId('line-chart')).toBeInTheDocument()
      expect(screen.getByTestId('legend')).toBeInTheDocument()
    })

    it('should handle legend click interactions', async () => {
      const user = userEvent.setup()

      render(
        <PokerMultiLineChart
          data={sampleMultiLineData}
          lines={sampleMultiLines}
          title="Interactive Multi-Line Chart"
          showLegend={true}
        />
      )

      const legend = screen.getByTestId('legend')
      await user.click(legend)

      // Legend click should toggle line visibility
      expect(legend).toBeInTheDocument()
    })

    it('should handle chart click interactions', async () => {
      const user = userEvent.setup()
      const mockClick = jest.fn()

      render(
        <PokerMultiLineChart
          data={sampleMultiLineData}
          lines={sampleMultiLines}
          title="Clickable Multi-Line Chart"
          onClick={mockClick}
        />
      )

      const chart = screen.getByTestId('line-chart')
      await user.click(chart)

      expect(mockClick).toHaveBeenCalledTimes(1)
    })
  })

  describe('PokerPositionChart', () => {
    it('should render position chart with win rate metric', () => {
      render(
        <PokerPositionChart
          data={samplePositionData}
          title="Position Analysis"
          metric="winRate"
        />
      )

      expect(screen.getByText('Position Analysis')).toBeInTheDocument()
      expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
    })

    it('should render with different metrics', () => {
      render(
        <PokerPositionChart
          data={samplePositionData}
          title="VPIP by Position"
          metric="vpip"
        />
      )

      expect(screen.getByText('VPIP by Position')).toBeInTheDocument()
    })

    it('should show default title and subtitle', () => {
      render(
        <PokerPositionChart data={samplePositionData} />
      )

      expect(screen.getByText('Position Analysis')).toBeInTheDocument()
      expect(screen.getByText('Performance by table position')).toBeInTheDocument()
    })
  })

  describe('PokerWinRateTrend', () => {
    it('should render win rate trend chart', () => {
      render(
        <PokerWinRateTrend
          data={sampleWinRateData}
          title="Win Rate Trend"
          showMovingAverage={true}
        />
      )

      expect(screen.getByText('Win Rate Trend')).toBeInTheDocument()
      expect(screen.getByTestId('line-chart')).toBeInTheDocument()
      expect(screen.getByTestId('reference-line')).toBeInTheDocument()
      expect(screen.getByTestId('legend')).toBeInTheDocument()
    })

    it('should render without moving average', () => {
      render(
        <PokerWinRateTrend
          data={sampleWinRateData}
          title="Simple Win Rate Trend"
          showMovingAverage={false}
        />
      )

      expect(screen.getByText('Simple Win Rate Trend')).toBeInTheDocument()
    })

    it('should show default title and subtitle', () => {
      render(
        <PokerWinRateTrend data={sampleWinRateData} />
      )

      expect(screen.getByText('Win Rate Trend')).toBeInTheDocument()
      expect(screen.getByText('Performance over time with moving average')).toBeInTheDocument()
    })
  })

  describe('PokerHeatmap', () => {
    it('should render heatmap chart', () => {
      render(
        <PokerHeatmap
          data={sampleHeatmapData}
          title="Performance Heatmap"
        />
      )

      expect(screen.getByText('Performance Heatmap')).toBeInTheDocument()
      
      // Should render day labels
      expect(screen.getByText('Mon')).toBeInTheDocument()
      expect(screen.getByText('Tue')).toBeInTheDocument()
      
      // Should render hour labels
      expect(screen.getByText('0')).toBeInTheDocument()
      expect(screen.getByText('10')).toBeInTheDocument()
      expect(screen.getByText('20')).toBeInTheDocument()
    })

    it('should show default title and subtitle', () => {
      render(
        <PokerHeatmap data={sampleHeatmapData} />
      )

      expect(screen.getByText('Performance Heatmap')).toBeInTheDocument()
      expect(screen.getByText('Win rate by day and hour')).toBeInTheDocument()
    })

    it('should render all day and hour labels', () => {
      render(
        <PokerHeatmap data={sampleHeatmapData} />
      )

      // Check for all day labels
      const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
      days.forEach(day => {
        expect(screen.getByText(day)).toBeInTheDocument()
      })

      // Check for some hour labels
      expect(screen.getByText('0')).toBeInTheDocument()
      expect(screen.getByText('12')).toBeInTheDocument()
      expect(screen.getByText('23')).toBeInTheDocument()
    })
  })

  describe('Chart Responsiveness', () => {
    it('should render responsive container for all chart types', () => {
      const charts = [
        <PokerLineChart key="line" data={sampleLineData} />,
        <PokerAreaChart key="area" data={sampleLineData} />,
        <PokerBarChart key="bar" data={sampleLineData} />,
        <PokerPieChart key="pie" data={samplePieData} />,
        <PokerMultiLineChart key="multi" data={sampleMultiLineData} lines={sampleMultiLines} />,
        <PokerPositionChart key="position" data={samplePositionData} />,
        <PokerWinRateTrend key="trend" data={sampleWinRateData} />,
      ]

      charts.forEach((chart, index) => {
        const { unmount } = render(chart)
        expect(screen.getByTestId('responsive-container')).toBeInTheDocument()
        unmount()
      })
    })
  })

  describe('Chart Loading States', () => {
    it('should show loading state for all chart types', () => {
      const chartProps = { loading: true, title: 'Loading Chart' }
      
      const charts = [
        <PokerLineChart key="line" data={[]} {...chartProps} />,
        <PokerAreaChart key="area" data={[]} {...chartProps} />,
        <PokerBarChart key="bar" data={[]} {...chartProps} />,
        <PokerPieChart key="pie" data={[]} {...chartProps} />,
        <PokerMultiLineChart key="multi" data={[]} lines={[]} {...chartProps} />,
        <PokerPositionChart key="position" data={[]} {...chartProps} />,
        <PokerWinRateTrend key="trend" data={[]} {...chartProps} />,
        <PokerHeatmap key="heatmap" data={[]} {...chartProps} />,
      ]

      charts.forEach((chart, index) => {
        const { unmount } = render(chart)
        expect(screen.getByText('Loading Chart')).toBeInTheDocument()
        expect(screen.getByText('Loading chart...')).toBeInTheDocument()
        unmount()
      })
    })
  })

  describe('Chart Accessibility', () => {
    it('should have proper ARIA labels and roles', () => {
      render(
        <PokerLineChart
          data={sampleLineData}
          title="Accessible Chart"
        />
      )

      // Chart title should be accessible as a heading
      const chartTitle = screen.getByRole('heading', { name: 'Accessible Chart' })
      expect(chartTitle).toBeInTheDocument()
      
      // Chart container should exist
      const chartContainer = screen.getByTestId('responsive-container')
      expect(chartContainer).toBeInTheDocument()
    })

    it('should support keyboard navigation for interactive elements', async () => {
      const user = userEvent.setup()
      const mockRefresh = jest.fn()

      render(
        <PokerLineChart
          data={sampleLineData}
          title="Keyboard Accessible Chart"
          onRefresh={mockRefresh}
        />
      )

      const refreshButton = screen.getByRole('button', { name: /refresh/i })
      
      // Should be focusable
      await user.tab()
      expect(refreshButton).toHaveFocus()
      
      // Should be activatable with Enter
      await user.keyboard('{Enter}')
      expect(mockRefresh).toHaveBeenCalledTimes(1)
    })
  })

  describe('Chart Error Handling', () => {
    it('should handle empty data gracefully', () => {
      render(
        <PokerLineChart
          data={[]}
          title="Empty Data Chart"
        />
      )

      expect(screen.getByText('Empty Data Chart')).toBeInTheDocument()
      expect(screen.getByTestId('line-chart')).toBeInTheDocument()
    })

    it('should handle invalid data gracefully', () => {
      const invalidData = [
        { name: 'Test', value: null },
        { name: 'Test2', value: undefined },
        { name: 'Test3', value: 'invalid' },
      ]

      render(
        <PokerLineChart
          data={invalidData as any}
          title="Invalid Data Chart"
        />
      )

      expect(screen.getByText('Invalid Data Chart')).toBeInTheDocument()
    })
  })
})