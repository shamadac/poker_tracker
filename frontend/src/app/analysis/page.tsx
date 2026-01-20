import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Container } from "@/components/ui/container"
import { LoadingButton } from "@/components/loading-states"

export default function Analysis() {
  return (
    <Container className="py-4 sm:py-6 lg:py-8">
      <div className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold">Hand Analysis</h1>
        <p className="text-muted-foreground text-sm sm:text-base">
          Analyze poker hands with AI-powered insights
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 sm:gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg sm:text-xl">Hand Input</CardTitle>
            <CardDescription className="text-sm">
              Paste your hand history or upload a file
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">
                Hand History
              </label>
              <textarea
                className="w-full h-24 sm:h-32 p-3 border rounded-md resize-none text-sm"
                placeholder="Paste your hand history here..."
              />
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  AI Provider
                </label>
                <select className="w-full p-2 border rounded-md text-sm">
                  <option value="groq">Groq (Fast)</option>
                  <option value="gemini">Gemini (Detailed)</option>
                </select>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">
                  Analysis Depth
                </label>
                <select className="w-full p-2 border rounded-md text-sm">
                  <option value="basic">Basic</option>
                  <option value="standard">Standard</option>
                  <option value="advanced">Advanced</option>
                </select>
              </div>
            </div>

            <LoadingButton className="w-full" loading={false}>
              Analyze Hand
            </LoadingButton>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg sm:text-xl">Analysis Results</CardTitle>
            <CardDescription className="text-sm">
              AI-powered strategic insights
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] sm:h-[400px] flex items-center justify-center text-muted-foreground text-sm text-center p-4">
              Analysis results will appear here after submitting a hand
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="mt-4 sm:mt-6">
        <CardHeader>
          <CardTitle className="text-lg sm:text-xl">Recent Analyses</CardTitle>
          <CardDescription className="text-sm">
            Your previously analyzed hands
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 sm:space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between p-3 sm:p-4 border rounded-lg gap-3 sm:gap-4">
              <div className="min-w-0 flex-1">
                <p className="font-medium text-sm sm:text-base">AK vs QQ - Button vs UTG</p>
                <p className="text-xs sm:text-sm text-muted-foreground">Analyzed 1 hour ago</p>
              </div>
              <LoadingButton className="w-full sm:w-auto" loading={false}>
                View Analysis
              </LoadingButton>
            </div>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between p-3 sm:p-4 border rounded-lg gap-3 sm:gap-4">
              <div className="min-w-0 flex-1">
                <p className="font-medium text-sm sm:text-base">77 vs AA - Small Blind vs Big Blind</p>
                <p className="text-xs sm:text-sm text-muted-foreground">Analyzed 3 hours ago</p>
              </div>
              <LoadingButton className="w-full sm:w-auto" loading={false}>
                View Analysis
              </LoadingButton>
            </div>
          </div>
        </CardContent>
      </Card>
    </Container>
  )
}