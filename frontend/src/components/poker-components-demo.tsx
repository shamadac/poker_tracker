"use client"

import * as React from "react"
import { 
  PokerCard, 
  HoleCards, 
  CommunityCards,
  StatCard,
  PokerStatCard,
  PokerLineChart,
  PokerAreaChart,
  PokerBarChart,
  PokerPieChart,
  PokerMultiLineChart,
  DataTable,
  PokerHandTable,
  type PokerHandData,
  type DataTableColumn
} from "./ui"

// Demo component to showcase all poker-specific components
export function PokerComponentsDemo() {
  // Sample data for charts
  const lineChartData = [
    { name: 'Jan', value: 400 },
    { name: 'Feb', value: 300 },
    { name: 'Mar', value: 600 },
    { name: 'Apr', value: 800 },
    { name: 'May', value: 500 },
  ]

  const pieChartData = [
    { name: 'Fold', value: 65 },
    { name: 'Call', value: 20 },
    { name: 'Raise', value: 15 },
  ]

  const multiLineData = [
    { name: 'Jan', vpip: 22, pfr: 18, aggression: 2.1 },
    { name: 'Feb', vpip: 25, pfr: 20, aggression: 2.3 },
    { name: 'Mar', vpip: 20, pfr: 16, aggression: 1.9 },
    { name: 'Apr', vpip: 23, pfr: 19, aggression: 2.2 },
    { name: 'May', vpip: 21, pfr: 17, aggression: 2.0 },
  ]

  const multiLines = [
    { dataKey: 'vpip', name: 'VPIP', color: '#3b82f6' },
    { dataKey: 'pfr', name: 'PFR', color: '#10b981' },
    { dataKey: 'aggression', name: 'Aggression', color: '#f59e0b' },
  ]

  // Sample hand data
  const sampleHands: PokerHandData[] = [
    {
      id: '1',
      handId: 'PS123456789',
      date: '2024-01-20T10:30:00Z',
      gameType: 'Hold\'em',
      stakes: '$0.50/$1.00',
      position: 'BTN',
      cards: ['As', 'Kh'],
      result: 'Won',
      profit: 15.50,
      vpip: true,
      pfr: true
    },
    {
      id: '2',
      handId: 'PS123456790',
      date: '2024-01-20T10:32:00Z',
      gameType: 'Hold\'em',
      stakes: '$0.50/$1.00',
      position: 'BB',
      cards: ['7c', '2d'],
      result: 'Folded',
      profit: -1.00,
      vpip: false,
      pfr: false
    },
    {
      id: '3',
      handId: 'PS123456791',
      date: '2024-01-20T10:35:00Z',
      gameType: 'Hold\'em',
      stakes: '$0.50/$1.00',
      position: 'CO',
      cards: ['Qh', 'Js'],
      result: 'Lost',
      profit: -8.75,
      vpip: true,
      pfr: false
    }
  ]

  return (
    <div className="space-y-8 p-6">
      <h1 className="text-3xl font-bold">Poker Components Demo</h1>
      
      {/* Poker Cards Section */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Poker Cards</h2>
        
        <div className="space-y-4">
          <div>
            <h3 className="text-lg font-medium mb-2">Individual Cards</h3>
            <div className="flex gap-4">
              <PokerCard rank="A" suit="spades" size="sm" />
              <PokerCard rank="K" suit="hearts" size="md" />
              <PokerCard rank="Q" suit="diamonds" size="lg" />
              <PokerCard faceDown size="md" />
            </div>
          </div>
          
          <div>
            <h3 className="text-lg font-medium mb-2">Hole Cards</h3>
            <HoleCards cards={['As', 'Kh']} size="md" />
          </div>
          
          <div>
            <h3 className="text-lg font-medium mb-2">Community Cards</h3>
            <CommunityCards cards={['Ah', 'Kd', 'Qc', 'Js', '9h']} size="md" />
          </div>
        </div>
      </section>

      {/* Stat Cards Section */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Statistics Cards</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Total Hands"
            value="1,234"
            subtitle="This month"
            trend={{ value: 12, label: "vs last month", isPositive: true }}
          />
          
          <PokerStatCard
            title="VPIP"
            value={22.5}
            statType="vpip"
            subtitle="Voluntary Put in Pot"
          />
          
          <PokerStatCard
            title="PFR"
            value={18.2}
            statType="pfr"
            subtitle="Pre-flop Raise"
          />
          
          <PokerStatCard
            title="Win Rate"
            value={3.2}
            statType="winrate"
            subtitle="BB/100 hands"
          />
        </div>
      </section>

      {/* Charts Section */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Charts</h2>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <PokerLineChart
            data={lineChartData}
            title="Profit Over Time"
            subtitle="Monthly profit in BB"
            dataKey="value"
          />
          
          <PokerAreaChart
            data={lineChartData}
            title="Cumulative Profit"
            subtitle="Running total"
            dataKey="value"
          />
          
          <PokerBarChart
            data={lineChartData}
            title="Monthly Volume"
            subtitle="Hands played per month"
            dataKey="value"
          />
          
          <PokerPieChart
            data={pieChartData}
            title="Action Distribution"
            subtitle="Preflop actions"
          />
        </div>
        
        <PokerMultiLineChart
          data={multiLineData}
          lines={multiLines}
          title="Statistics Trends"
          subtitle="Key metrics over time"
          className="col-span-full"
        />
      </section>

      {/* Data Table Section */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Data Tables</h2>
        
        <PokerHandTable
          hands={sampleHands}
          title="Recent Hands"
          onHandClick={(hand) => console.log('Clicked hand:', hand)}
        />
      </section>
    </div>
  )
}