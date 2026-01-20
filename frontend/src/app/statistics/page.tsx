import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Container } from "@/components/ui/container"

export default function Statistics() {
  return (
    <Container className="py-4 sm:py-6 lg:py-8">
      <div className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold">Statistics</h1>
        <p className="text-muted-foreground text-sm sm:text-base">
          Detailed poker statistics and performance metrics
        </p>
      </div>

      {/* Filters */}
      <Card className="mb-4 sm:mb-6">
        <CardHeader>
          <CardTitle className="text-lg sm:text-xl">Filters</CardTitle>
          <CardDescription className="text-sm">
            Filter your statistics by various criteria
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Date Range</label>
              <select className="w-full p-2 border rounded-md text-sm">
                <option value="7d">Last 7 days</option>
                <option value="30d">Last 30 days</option>
                <option value="90d">Last 90 days</option>
                <option value="1y">Last year</option>
                <option value="all">All time</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Game Type</label>
              <select className="w-full p-2 border rounded-md text-sm">
                <option value="all">All Games</option>
                <option value="cash">Cash Games</option>
                <option value="tournament">Tournaments</option>
                <option value="sng">Sit & Go</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Stakes</label>
              <select className="w-full p-2 border rounded-md text-sm">
                <option value="all">All Stakes</option>
                <option value="micro">Micro ($0.01-$0.05)</option>
                <option value="low">Low ($0.10-$0.50)</option>
                <option value="mid">Mid ($1-$5)</option>
              </select>
            </div>
            <div className="flex items-end">
              <Button className="w-full">Apply Filters</Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Basic Statistics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 lg:gap-6 mb-4 sm:mb-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-xs sm:text-sm">VPIP</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-lg sm:text-2xl font-bold">23.4%</div>
            <p className="text-xs text-muted-foreground">Voluntarily Put $ In Pot</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-xs sm:text-sm">PFR</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-lg sm:text-2xl font-bold">18.7%</div>
            <p className="text-xs text-muted-foreground">Pre-Flop Raise</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-xs sm:text-sm">Aggression Factor</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-lg sm:text-2xl font-bold">2.8</div>
            <p className="text-xs text-muted-foreground">(Bet+Raise)/Call</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-xs sm:text-sm">Win Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-lg sm:text-2xl font-bold">+5.2 BB/100</div>
            <p className="text-xs text-muted-foreground">Big Blinds per 100 hands</p>
          </CardContent>
        </Card>
      </div>

      {/* Advanced Statistics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 mb-4 sm:mb-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg sm:text-xl">Positional Statistics</CardTitle>
            <CardDescription className="text-sm">Performance by position</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm">UTG</span>
                <span className="text-sm font-medium">+2.1 BB/100</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">MP</span>
                <span className="text-sm font-medium">+3.4 BB/100</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">CO</span>
                <span className="text-sm font-medium">+6.8 BB/100</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">BTN</span>
                <span className="text-sm font-medium">+8.2 BB/100</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">SB</span>
                <span className="text-sm font-medium">-2.1 BB/100</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">BB</span>
                <span className="text-sm font-medium">-1.5 BB/100</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg sm:text-xl">Advanced Metrics</CardTitle>
            <CardDescription className="text-sm">Detailed performance indicators</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm">3-Bet %</span>
                <span className="text-sm font-medium">8.2%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">C-Bet Flop %</span>
                <span className="text-sm font-medium">68.5%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">C-Bet Turn %</span>
                <span className="text-sm font-medium">52.3%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Fold to 3-Bet %</span>
                <span className="text-sm font-medium">72.1%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Check-Raise %</span>
                <span className="text-sm font-medium">12.4%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">WTSD %</span>
                <span className="text-sm font-medium">28.7%</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg sm:text-xl">Performance Over Time</CardTitle>
          <CardDescription className="text-sm">Win rate and volume trends</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[250px] sm:h-[300px] flex items-center justify-center text-muted-foreground text-sm text-center">
            Performance charts will be implemented with Recharts
          </div>
        </CardContent>
      </Card>
    </Container>
  )
}