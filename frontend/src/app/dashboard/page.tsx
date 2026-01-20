import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Container } from "@/components/ui/container"
import { Skeleton, SkeletonCard } from "@/components/loading-states"

export default function Dashboard() {
  return (
    <Container className="py-4 sm:py-6 lg:py-8">
      <div className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground text-sm sm:text-base">
          Overview of your poker performance and statistics
        </p>
      </div>

      {/* Stats Grid - Responsive */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 lg:gap-6 mb-6 sm:mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-xs sm:text-sm font-medium">Total Hands</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-lg sm:text-2xl font-bold">1,234</div>
            <p className="text-xs text-muted-foreground">
              +20.1% from last month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-xs sm:text-sm font-medium">Win Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-lg sm:text-2xl font-bold">+5.2 BB/100</div>
            <p className="text-xs text-muted-foreground">
              +2.1% from last month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-xs sm:text-sm font-medium">VPIP</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-lg sm:text-2xl font-bold">23.4%</div>
            <p className="text-xs text-muted-foreground">
              -1.2% from last month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-xs sm:text-sm font-medium">PFR</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-lg sm:text-2xl font-bold">18.7%</div>
            <p className="text-xs text-muted-foreground">
              +0.5% from last month
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid - Responsive */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 sm:gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg sm:text-xl">Recent Sessions</CardTitle>
            <CardDescription className="text-sm">
              Your latest poker sessions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="min-w-0 flex-1">
                  <p className="font-medium text-sm sm:text-base truncate">NL25 Cash Game</p>
                  <p className="text-xs sm:text-sm text-muted-foreground">2 hours ago</p>
                </div>
                <div className="text-right ml-4">
                  <p className="font-medium text-green-600 text-sm sm:text-base">+$45.20</p>
                  <p className="text-xs sm:text-sm text-muted-foreground">156 hands</p>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <div className="min-w-0 flex-1">
                  <p className="font-medium text-sm sm:text-base truncate">Tournament</p>
                  <p className="text-xs sm:text-sm text-muted-foreground">1 day ago</p>
                </div>
                <div className="text-right ml-4">
                  <p className="font-medium text-red-600 text-sm sm:text-base">-$22.00</p>
                  <p className="text-xs sm:text-sm text-muted-foreground">89 hands</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg sm:text-xl">Performance Chart</CardTitle>
            <CardDescription className="text-sm">
              Win rate over time
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[200px] sm:h-[250px] flex items-center justify-center text-muted-foreground text-sm sm:text-base">
              Chart placeholder - will be implemented with Recharts
            </div>
          </CardContent>
        </Card>
      </div>
    </Container>
  )
}