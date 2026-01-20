import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Container } from "@/components/ui/container"

export default function Settings() {
  return (
    <Container className="py-4 sm:py-6 lg:py-8">
      <div className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground text-sm sm:text-base">
          Configure your poker analyzer preferences
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 sm:gap-6">
        {/* AI Provider Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg sm:text-xl">AI Provider Configuration</CardTitle>
            <CardDescription className="text-sm">
              Configure your AI analysis providers
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">
                Default AI Provider
              </label>
              <select className="w-full p-2 border rounded-md text-sm">
                <option value="groq">Groq (Fast)</option>
                <option value="gemini">Gemini (Detailed)</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">
                Groq API Key
              </label>
              <Input
                type="password"
                placeholder="Enter your Groq API key"
                className="text-sm"
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">
                Gemini API Key
              </label>
              <Input
                type="password"
                placeholder="Enter your Gemini API key"
                className="text-sm"
              />
            </div>

            <Button className="w-full">
              Save AI Settings
            </Button>
          </CardContent>
        </Card>

        {/* File Monitoring Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg sm:text-xl">File Monitoring</CardTitle>
            <CardDescription className="text-sm">
              Configure automatic hand history import
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">
                PokerStars Hand History Path
              </label>
              <div className="flex flex-col sm:flex-row gap-2">
                <Input
                  placeholder="C:/Users/.../PokerStars/HandHistory"
                  className="flex-1 text-sm"
                />
                <Button variant="outline" className="w-full sm:w-auto">Browse</Button>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">
                GGPoker Hand History Path
              </label>
              <div className="flex flex-col sm:flex-row gap-2">
                <Input
                  placeholder="C:/Users/.../GGPoker/HandHistory"
                  className="flex-1 text-sm"
                />
                <Button variant="outline" className="w-full sm:w-auto">Browse</Button>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="auto-import"
                className="rounded"
              />
              <label htmlFor="auto-import" className="text-sm font-medium">
                Enable automatic import
              </label>
            </div>

            <Button className="w-full">
              Save File Settings
            </Button>
          </CardContent>
        </Card>

        {/* Display Preferences */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg sm:text-xl">Display Preferences</CardTitle>
            <CardDescription className="text-sm">
              Customize the appearance and behavior
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">
                Theme
              </label>
              <select className="w-full p-2 border rounded-md text-sm">
                <option value="light">Light</option>
                <option value="dark">Dark</option>
                <option value="system">System</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">
                Currency Display
              </label>
              <select className="w-full p-2 border rounded-md text-sm">
                <option value="usd">USD ($)</option>
                <option value="eur">EUR (€)</option>
                <option value="gbp">GBP (£)</option>
                <option value="bb">Big Blinds (BB)</option>
              </select>
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="animations"
                className="rounded"
                defaultChecked
              />
              <label htmlFor="animations" className="text-sm font-medium">
                Enable animations
              </label>
            </div>

            <Button className="w-full">
              Save Display Settings
            </Button>
          </CardContent>
        </Card>

        {/* Account Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg sm:text-xl">Account Settings</CardTitle>
            <CardDescription className="text-sm">
              Manage your account and data
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">
                Username
              </label>
              <Input
                placeholder="Your username"
                defaultValue="poker_pro_2024"
                className="text-sm"
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">
                Email
              </label>
              <Input
                type="email"
                placeholder="your.email@example.com"
                className="text-sm"
              />
            </div>

            <div className="pt-4 border-t">
              <h4 className="font-medium mb-3 text-sm sm:text-base">Data Management</h4>
              <div className="space-y-2">
                <Button variant="outline" className="w-full text-sm">
                  Export All Data
                </Button>
                <Button variant="destructive" className="w-full text-sm">
                  Delete All Data
                </Button>
              </div>
            </div>

            <Button className="w-full">
              Save Account Settings
            </Button>
          </CardContent>
        </Card>
      </div>
    </Container>
  )
}