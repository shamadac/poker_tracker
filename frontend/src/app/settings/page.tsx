"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Container } from "@/components/ui/container"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { useState, useCallback } from "react"
import { 
  Settings as SettingsIcon, 
  Brain, 
  Zap, 
  FolderOpen, 
  Palette, 
  User, 
  Shield, 
  Download,
  Trash2,
  Eye,
  EyeOff,
  CheckCircle,
  AlertCircle,
  Folder,
  HardDrive
} from "lucide-react"

// Settings interfaces
interface AIProviderSettings {
  defaultProvider: 'groq' | 'gemini'
  groqApiKey: string
  geminiApiKey: string
  analysisDepth: 'basic' | 'standard' | 'advanced'
  enableBatchAnalysis: boolean
}

interface FileMonitoringSettings {
  pokerstarsPath: string
  ggpokerPath: string
  autoImport: boolean
  monitoringEnabled: boolean
  fileTypes: string[]
  scanInterval: number
}

interface DisplaySettings {
  theme: 'light' | 'dark' | 'system'
  currency: 'usd' | 'eur' | 'gbp' | 'bb'
  dateFormat: 'us' | 'eu' | 'iso'
  enableAnimations: boolean
  compactMode: boolean
  showAdvancedStats: boolean
}

interface AccountSettings {
  username: string
  email: string
  timezone: string
  language: string
  emailNotifications: boolean
  dataRetention: number // days
}

export default function Settings() {
  const [activeTab, setActiveTab] = useState('ai-providers')
  const [isSaving, setIsSaving] = useState(false)
  const [showApiKeys, setShowApiKeys] = useState(false)
  const [testingConnection, setTestingConnection] = useState<string | null>(null)

  // Settings state
  const [aiSettings, setAISettings] = useState<AIProviderSettings>({
    defaultProvider: 'groq',
    groqApiKey: '',
    geminiApiKey: '',
    analysisDepth: 'standard',
    enableBatchAnalysis: true
  })

  const [fileSettings, setFileSettings] = useState<FileMonitoringSettings>({
    pokerstarsPath: '',
    ggpokerPath: '',
    autoImport: true,
    monitoringEnabled: true,
    fileTypes: ['.txt', '.log'],
    scanInterval: 30
  })

  const [displaySettings, setDisplaySettings] = useState<DisplaySettings>({
    theme: 'system',
    currency: 'usd',
    dateFormat: 'us',
    enableAnimations: true,
    compactMode: false,
    showAdvancedStats: true
  })

  const [accountSettings, setAccountSettings] = useState<AccountSettings>({
    username: 'poker_pro_2024',
    email: 'user@example.com',
    timezone: 'America/New_York',
    language: 'en',
    emailNotifications: true,
    dataRetention: 365
  })

  // Handlers
  const handleSaveSettings = useCallback(async (section: string) => {
    setIsSaving(true)
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500))
      
      console.log(`Saving ${section} settings:`, {
        aiSettings,
        fileSettings,
        displaySettings,
        accountSettings
      })
      
      alert(`${section} settings saved successfully!`)
    } catch (error) {
      console.error('Failed to save settings:', error)
      alert('Failed to save settings. Please try again.')
    } finally {
      setIsSaving(false)
    }
  }, [aiSettings, fileSettings, displaySettings, accountSettings])

  const handleTestConnection = useCallback(async (provider: 'groq' | 'gemini') => {
    setTestingConnection(provider)
    try {
      // Simulate API key validation
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      const apiKey = provider === 'groq' ? aiSettings.groqApiKey : aiSettings.geminiApiKey
      if (!apiKey) {
        throw new Error('API key is required')
      }
      
      // Mock validation - in real app this would call the actual API
      const isValid = apiKey.length > 10 // Simple validation
      
      if (isValid) {
        alert(`${provider === 'groq' ? 'Groq' : 'Gemini'} API key is valid!`)
      } else {
        throw new Error('Invalid API key format')
      }
    } catch (error) {
      alert(`Connection test failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
    } finally {
      setTestingConnection(null)
    }
  }, [aiSettings])

  const handleBrowseFolder = useCallback(async (pathType: 'pokerstars' | 'ggpoker') => {
    try {
      // In a real app, this would open a native file dialog
      // For now, we'll simulate with a prompt
      const path = prompt(`Enter the path to your ${pathType === 'pokerstars' ? 'PokerStars' : 'GGPoker'} hand history folder:`)
      
      if (path) {
        setFileSettings(prev => ({
          ...prev,
          [pathType === 'pokerstars' ? 'pokerstarsPath' : 'ggpokerPath']: path
        }))
      }
    } catch (error) {
      console.error('Failed to browse folder:', error)
    }
  }, [])

  const handleExportData = useCallback(async () => {
    try {
      // Simulate data export
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      const exportData = {
        settings: { aiSettings, fileSettings, displaySettings, accountSettings },
        exportDate: new Date().toISOString(),
        version: '1.0'
      }
      
      // In real app, this would trigger a download
      console.log('Exporting data:', exportData)
      alert('Data export completed! Check your downloads folder.')
    } catch (error) {
      console.error('Export failed:', error)
      alert('Export failed. Please try again.')
    }
  }, [aiSettings, fileSettings, displaySettings, accountSettings])

  const handleDeleteAllData = useCallback(async () => {
    const confirmed = confirm(
      'Are you sure you want to delete ALL your data? This action cannot be undone.\n\n' +
      'This will delete:\n' +
      '• All hand histories\n' +
      '• All analysis results\n' +
      '• All statistics\n' +
      '• All settings\n\n' +
      'Type "DELETE" to confirm:'
    )
    
    if (confirmed) {
      const confirmation = prompt('Type "DELETE" to confirm:')
      if (confirmation === 'DELETE') {
        try {
          // Simulate data deletion
          await new Promise(resolve => setTimeout(resolve, 3000))
          alert('All data has been deleted successfully.')
        } catch (error) {
          console.error('Deletion failed:', error)
          alert('Deletion failed. Please try again.')
        }
      }
    }
  }, [])

  return (
    <Container className="py-4 sm:py-6 lg:py-8">
      <div className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold flex items-center gap-2">
          <SettingsIcon className="h-8 w-8" />
          Settings
        </h1>
        <p className="text-muted-foreground text-sm sm:text-base">
          Configure your poker analyzer preferences and integrations
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="ai-providers">AI Providers</TabsTrigger>
          <TabsTrigger value="file-monitoring">File Monitoring</TabsTrigger>
          <TabsTrigger value="display">Display</TabsTrigger>
          <TabsTrigger value="account">Account</TabsTrigger>
        </TabsList>

        {/* AI Providers Tab */}
        <TabsContent value="ai-providers" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg sm:text-xl flex items-center gap-2">
                <Brain className="h-5 w-5" />
                AI Provider Configuration
              </CardTitle>
              <CardDescription className="text-sm">
                Configure your AI analysis providers and API keys
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Default Provider Selection */}
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Default AI Provider
                </label>
                <Select 
                  value={aiSettings.defaultProvider} 
                  onValueChange={(value: 'groq' | 'gemini') => 
                    setAISettings(prev => ({ ...prev, defaultProvider: value }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="groq">
                      <div className="flex items-center gap-2">
                        <Zap className="h-4 w-4" />
                        Groq (Fast Analysis)
                      </div>
                    </SelectItem>
                    <SelectItem value="gemini">
                      <div className="flex items-center gap-2">
                        <Brain className="h-4 w-4" />
                        Gemini (Detailed Analysis)
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground mt-1">
                  Choose your preferred AI provider for hand analysis
                </p>
              </div>

              {/* API Keys Section */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium">API Keys</h3>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowApiKeys(!showApiKeys)}
                  >
                    {showApiKeys ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    {showApiKeys ? 'Hide' : 'Show'} Keys
                  </Button>
                </div>

                {/* Groq API Key */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Groq API Key</label>
                  <div className="flex gap-2">
                    <Input
                      type={showApiKeys ? "text" : "password"}
                      placeholder="Enter your Groq API key"
                      value={aiSettings.groqApiKey}
                      onChange={(e) => setAISettings(prev => ({ 
                        ...prev, 
                        groqApiKey: e.target.value 
                      }))}
                      className="flex-1"
                    />
                    <Button
                      variant="outline"
                      onClick={() => handleTestConnection('groq')}
                      disabled={testingConnection === 'groq' || !aiSettings.groqApiKey}
                    >
                      {testingConnection === 'groq' ? 'Testing...' : 'Test'}
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Get your API key from <a href="https://console.groq.com" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Groq Console</a>
                  </p>
                </div>

                {/* Gemini API Key */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Gemini API Key</label>
                  <div className="flex gap-2">
                    <Input
                      type={showApiKeys ? "text" : "password"}
                      placeholder="Enter your Gemini API key"
                      value={aiSettings.geminiApiKey}
                      onChange={(e) => setAISettings(prev => ({ 
                        ...prev, 
                        geminiApiKey: e.target.value 
                      }))}
                      className="flex-1"
                    />
                    <Button
                      variant="outline"
                      onClick={() => handleTestConnection('gemini')}
                      disabled={testingConnection === 'gemini' || !aiSettings.geminiApiKey}
                    >
                      {testingConnection === 'gemini' ? 'Testing...' : 'Test'}
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Get your API key from <a href="https://makersuite.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Google AI Studio</a>
                  </p>
                </div>
              </div>

              {/* Analysis Settings */}
              <div className="space-y-4">
                <h3 className="text-sm font-medium">Analysis Settings</h3>
                
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Default Analysis Depth
                  </label>
                  <Select 
                    value={aiSettings.analysisDepth} 
                    onValueChange={(value: 'basic' | 'standard' | 'advanced') => 
                      setAISettings(prev => ({ ...prev, analysisDepth: value }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="basic">Basic - Quick overview</SelectItem>
                      <SelectItem value="standard">Standard - Balanced analysis</SelectItem>
                      <SelectItem value="advanced">Advanced - Comprehensive review</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium">Enable Batch Analysis</label>
                    <p className="text-xs text-muted-foreground">Analyze multiple hands at once</p>
                  </div>
                  <Switch
                    checked={aiSettings.enableBatchAnalysis}
                    onCheckedChange={(checked) => 
                      setAISettings(prev => ({ ...prev, enableBatchAnalysis: checked }))
                    }
                  />
                </div>
              </div>

              <Button 
                onClick={() => handleSaveSettings('AI Provider')} 
                disabled={isSaving}
                className="w-full"
              >
                {isSaving ? 'Saving...' : 'Save AI Settings'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* File Monitoring Tab */}
        <TabsContent value="file-monitoring" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg sm:text-xl flex items-center gap-2">
                <FolderOpen className="h-5 w-5" />
                File Monitoring
              </CardTitle>
              <CardDescription className="text-sm">
                Configure automatic hand history import and monitoring
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Hand History Paths */}
              <div className="space-y-4">
                <h3 className="text-sm font-medium">Hand History Paths</h3>
                
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    PokerStars Hand History Path
                  </label>
                  <div className="flex gap-2">
                    <Input
                      placeholder="C:/Users/.../PokerStars/HandHistory"
                      value={fileSettings.pokerstarsPath}
                      onChange={(e) => setFileSettings(prev => ({ 
                        ...prev, 
                        pokerstarsPath: e.target.value 
                      }))}
                      className="flex-1"
                    />
                    <Button 
                      variant="outline"
                      onClick={() => handleBrowseFolder('pokerstars')}
                    >
                      <Folder className="h-4 w-4 mr-2" />
                      Browse
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Default: %LOCALAPPDATA%\PokerStars\HandHistory\[username]\
                  </p>
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">
                    GGPoker Hand History Path
                  </label>
                  <div className="flex gap-2">
                    <Input
                      placeholder="C:/Users/.../GGPoker/HandHistory"
                      value={fileSettings.ggpokerPath}
                      onChange={(e) => setFileSettings(prev => ({ 
                        ...prev, 
                        ggpokerPath: e.target.value 
                      }))}
                      className="flex-1"
                    />
                    <Button 
                      variant="outline"
                      onClick={() => handleBrowseFolder('ggpoker')}
                    >
                      <Folder className="h-4 w-4 mr-2" />
                      Browse
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Default: %APPDATA%\GGPoker\HandHistory\
                  </p>
                </div>
              </div>

              {/* Monitoring Settings */}
              <div className="space-y-4">
                <h3 className="text-sm font-medium">Monitoring Settings</h3>
                
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium">Enable Auto Import</label>
                    <p className="text-xs text-muted-foreground">Automatically import new hand histories</p>
                  </div>
                  <Switch
                    checked={fileSettings.autoImport}
                    onCheckedChange={(checked) => 
                      setFileSettings(prev => ({ ...prev, autoImport: checked }))
                    }
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium">Enable File Monitoring</label>
                    <p className="text-xs text-muted-foreground">Monitor directories for new files</p>
                  </div>
                  <Switch
                    checked={fileSettings.monitoringEnabled}
                    onCheckedChange={(checked) => 
                      setFileSettings(prev => ({ ...prev, monitoringEnabled: checked }))
                    }
                  />
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Scan Interval (seconds)
                  </label>
                  <Input
                    type="number"
                    min="10"
                    max="300"
                    value={fileSettings.scanInterval}
                    onChange={(e) => setFileSettings(prev => ({ 
                      ...prev, 
                      scanInterval: parseInt(e.target.value) || 30 
                    }))}
                    className="w-32"
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    How often to check for new files (10-300 seconds)
                  </p>
                </div>
              </div>

              {/* File Types */}
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Supported File Types
                </label>
                <div className="flex gap-2">
                  {fileSettings.fileTypes.map((type, index) => (
                    <Badge key={index} variant="secondary">
                      {type}
                    </Badge>
                  ))}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  File extensions that will be monitored and imported
                </p>
              </div>

              <Button 
                onClick={() => handleSaveSettings('File Monitoring')} 
                disabled={isSaving}
                className="w-full"
              >
                {isSaving ? 'Saving...' : 'Save File Settings'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Display Tab */}
        <TabsContent value="display" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg sm:text-xl flex items-center gap-2">
                <Palette className="h-5 w-5" />
                Display Preferences
              </CardTitle>
              <CardDescription className="text-sm">
                Customize the appearance and behavior of the application
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Theme Settings */}
              <div>
                <label className="text-sm font-medium mb-2 block">Theme</label>
                <Select 
                  value={displaySettings.theme} 
                  onValueChange={(value: 'light' | 'dark' | 'system') => 
                    setDisplaySettings(prev => ({ ...prev, theme: value }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="light">Light</SelectItem>
                    <SelectItem value="dark">Dark</SelectItem>
                    <SelectItem value="system">System</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Currency Display */}
              <div>
                <label className="text-sm font-medium mb-2 block">Currency Display</label>
                <Select 
                  value={displaySettings.currency} 
                  onValueChange={(value: 'usd' | 'eur' | 'gbp' | 'bb') => 
                    setDisplaySettings(prev => ({ ...prev, currency: value }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="usd">USD ($)</SelectItem>
                    <SelectItem value="eur">EUR (€)</SelectItem>
                    <SelectItem value="gbp">GBP (£)</SelectItem>
                    <SelectItem value="bb">Big Blinds (BB)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Date Format */}
              <div>
                <label className="text-sm font-medium mb-2 block">Date Format</label>
                <Select 
                  value={displaySettings.dateFormat} 
                  onValueChange={(value: 'us' | 'eu' | 'iso') => 
                    setDisplaySettings(prev => ({ ...prev, dateFormat: value }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="us">US (MM/DD/YYYY)</SelectItem>
                    <SelectItem value="eu">European (DD/MM/YYYY)</SelectItem>
                    <SelectItem value="iso">ISO (YYYY-MM-DD)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Display Options */}
              <div className="space-y-4">
                <h3 className="text-sm font-medium">Display Options</h3>
                
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium">Enable Animations</label>
                    <p className="text-xs text-muted-foreground">Smooth transitions and effects</p>
                  </div>
                  <Switch
                    checked={displaySettings.enableAnimations}
                    onCheckedChange={(checked) => 
                      setDisplaySettings(prev => ({ ...prev, enableAnimations: checked }))
                    }
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium">Compact Mode</label>
                    <p className="text-xs text-muted-foreground">Reduce spacing and padding</p>
                  </div>
                  <Switch
                    checked={displaySettings.compactMode}
                    onCheckedChange={(checked) => 
                      setDisplaySettings(prev => ({ ...prev, compactMode: checked }))
                    }
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium">Show Advanced Statistics</label>
                    <p className="text-xs text-muted-foreground">Display detailed poker metrics</p>
                  </div>
                  <Switch
                    checked={displaySettings.showAdvancedStats}
                    onCheckedChange={(checked) => 
                      setDisplaySettings(prev => ({ ...prev, showAdvancedStats: checked }))
                    }
                  />
                </div>
              </div>

              <Button 
                onClick={() => handleSaveSettings('Display')} 
                disabled={isSaving}
                className="w-full"
              >
                {isSaving ? 'Saving...' : 'Save Display Settings'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Account Tab */}
        <TabsContent value="account" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg sm:text-xl flex items-center gap-2">
                <User className="h-5 w-5" />
                Account Settings
              </CardTitle>
              <CardDescription className="text-sm">
                Manage your account information and preferences
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Profile Information */}
              <div className="space-y-4">
                <h3 className="text-sm font-medium">Profile Information</h3>
                
                <div>
                  <label className="text-sm font-medium mb-2 block">Username</label>
                  <Input
                    value={accountSettings.username}
                    onChange={(e) => setAccountSettings(prev => ({ 
                      ...prev, 
                      username: e.target.value 
                    }))}
                    placeholder="Your username"
                  />
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">Email</label>
                  <Input
                    type="email"
                    value={accountSettings.email}
                    onChange={(e) => setAccountSettings(prev => ({ 
                      ...prev, 
                      email: e.target.value 
                    }))}
                    placeholder="your.email@example.com"
                  />
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">Timezone</label>
                  <Select 
                    value={accountSettings.timezone} 
                    onValueChange={(value) => 
                      setAccountSettings(prev => ({ ...prev, timezone: value }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="America/New_York">Eastern Time (ET)</SelectItem>
                      <SelectItem value="America/Chicago">Central Time (CT)</SelectItem>
                      <SelectItem value="America/Denver">Mountain Time (MT)</SelectItem>
                      <SelectItem value="America/Los_Angeles">Pacific Time (PT)</SelectItem>
                      <SelectItem value="Europe/London">London (GMT)</SelectItem>
                      <SelectItem value="Europe/Paris">Paris (CET)</SelectItem>
                      <SelectItem value="Asia/Tokyo">Tokyo (JST)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Preferences */}
              <div className="space-y-4">
                <h3 className="text-sm font-medium">Preferences</h3>
                
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium">Email Notifications</label>
                    <p className="text-xs text-muted-foreground">Receive updates and alerts via email</p>
                  </div>
                  <Switch
                    checked={accountSettings.emailNotifications}
                    onCheckedChange={(checked) => 
                      setAccountSettings(prev => ({ ...prev, emailNotifications: checked }))
                    }
                  />
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Data Retention (days)
                  </label>
                  <Input
                    type="number"
                    min="30"
                    max="3650"
                    value={accountSettings.dataRetention}
                    onChange={(e) => setAccountSettings(prev => ({ 
                      ...prev, 
                      dataRetention: parseInt(e.target.value) || 365 
                    }))}
                    className="w-32"
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    How long to keep your data (30-3650 days)
                  </p>
                </div>
              </div>

              <Button 
                onClick={() => handleSaveSettings('Account')} 
                disabled={isSaving}
                className="w-full"
              >
                {isSaving ? 'Saving...' : 'Save Account Settings'}
              </Button>
            </CardContent>
          </Card>

          {/* Data Management */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg sm:text-xl flex items-center gap-2">
                <HardDrive className="h-5 w-5" />
                Data Management
              </CardTitle>
              <CardDescription className="text-sm">
                Export or delete your poker data
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-col sm:flex-row gap-4">
                <Button 
                  variant="outline" 
                  onClick={handleExportData}
                  className="flex-1"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Export All Data
                </Button>
                
                <Button 
                  variant="destructive" 
                  onClick={handleDeleteAllData}
                  className="flex-1"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete All Data
                </Button>
              </div>
              
              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div className="flex items-start gap-2">
                  <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-yellow-800">Data Management Notice</p>
                    <p className="text-xs text-yellow-700 mt-1">
                      Exporting data will create a backup of all your poker hands, analyses, and settings. 
                      Deleting data is permanent and cannot be undone.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </Container>
  )
}