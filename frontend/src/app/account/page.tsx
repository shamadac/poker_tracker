"use client"

import { useState, useEffect } from 'react'
import { Container } from '@/components/ui/container'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useToast } from '@/hooks/use-toast'
import { api } from '@/lib/api-client'
import { AlertTriangle, Download, Trash2, Shield, User, Settings } from 'lucide-react'

interface UserProfile {
  id: string
  email: string
  created_at: string
  preferences: Record<string, any>
  api_keys_configured: Record<string, boolean>
  hand_history_paths: Record<string, string>
}

interface DataSummary {
  user_id: string
  data_counts: Record<string, number>
  total_records: number
  summary_generated_at: string
}

export default function AccountPage() {
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [dataSummary, setDataSummary] = useState<DataSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [deletePassword, setDeletePassword] = useState('')
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
  const { toast } = useToast()

  useEffect(() => {
    loadAccountData()
  }, [])

  const loadAccountData = async () => {
    try {
      setLoading(true)
      const [profileResponse, summaryResponse] = await Promise.all([
        api.users.getProfile(),
        api.users.getDataSummary()
      ])
      
      setProfile(profileResponse.data)
      setDataSummary(summaryResponse.data)
    } catch (error) {
      console.error('Failed to load account data:', error)
      toast({
        title: "Error",
        description: "Failed to load account information",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }

  const handleExportData = async () => {
    try {
      setIsExporting(true)
      const response = await api.users.exportData()
      
      // Create and download the export file
      const blob = new Blob([JSON.stringify(response.data, null, 2)], {
        type: 'application/json'
      })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `poker-analyzer-data-export-${new Date().toISOString().split('T')[0]}.json`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      toast({
        title: "Success",
        description: "Your data has been exported successfully",
      })
    } catch (error) {
      console.error('Failed to export data:', error)
      toast({
        title: "Error",
        description: "Failed to export your data",
        variant: "destructive"
      })
    } finally {
      setIsExporting(false)
    }
  }

  const handleDeleteAccount = async () => {
    if (!deletePassword.trim()) {
      toast({
        title: "Error",
        description: "Please enter your password to confirm deletion",
        variant: "destructive"
      })
      return
    }

    try {
      setIsDeleting(true)
      const response = await api.users.deleteAccount(deletePassword, true)
      
      toast({
        title: "Account Deleted",
        description: "Your account and all associated data have been permanently deleted",
      })
      
      // Clear local storage and redirect
      localStorage.clear()
      window.location.href = '/'
      
    } catch (error: any) {
      console.error('Failed to delete account:', error)
      const errorMessage = error.response?.data?.detail || "Failed to delete account"
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive"
      })
    } finally {
      setIsDeleting(false)
      setShowDeleteConfirm(false)
      setDeletePassword('')
    }
  }

  if (loading) {
    return (
      <Container className="py-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading account information...</p>
          </div>
        </div>
      </Container>
    )
  }

  return (
    <Container className="py-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Account Management</h1>
          <p className="text-gray-600">
            Manage your account settings, view your data, and control your privacy
          </p>
        </div>

        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview" className="flex items-center gap-2">
              <User className="h-4 w-4" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="data" className="flex items-center gap-2">
              <Settings className="h-4 w-4" />
              Data
            </TabsTrigger>
            <TabsTrigger value="privacy" className="flex items-center gap-2">
              <Shield className="h-4 w-4" />
              Privacy
            </TabsTrigger>
            <TabsTrigger value="danger" className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              Danger Zone
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Account Information</CardTitle>
                <CardDescription>
                  Your basic account details and configuration status
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {profile && (
                  <>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label className="text-sm font-medium text-gray-700">Email</Label>
                        <p className="text-gray-900">{profile.email}</p>
                      </div>
                      <div>
                        <Label className="text-sm font-medium text-gray-700">Account Created</Label>
                        <p className="text-gray-900">
                          {new Date(profile.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    
                    <div>
                      <Label className="text-sm font-medium text-gray-700 mb-2 block">
                        AI Providers Configured
                      </Label>
                      <div className="flex gap-2">
                        <Badge variant={profile.api_keys_configured.gemini ? "default" : "secondary"}>
                          Gemini {profile.api_keys_configured.gemini ? "✓" : "✗"}
                        </Badge>
                        <Badge variant={profile.api_keys_configured.groq ? "default" : "secondary"}>
                          Groq {profile.api_keys_configured.groq ? "✓" : "✗"}
                        </Badge>
                      </div>
                    </div>

                    <div>
                      <Label className="text-sm font-medium text-gray-700 mb-2 block">
                        Hand History Paths
                      </Label>
                      <div className="space-y-1">
                        {Object.entries(profile.hand_history_paths).length > 0 ? (
                          Object.entries(profile.hand_history_paths).map(([platform, path]) => (
                            <div key={platform} className="text-sm">
                              <span className="font-medium capitalize">{platform}:</span>{' '}
                              <span className="text-gray-600">{path}</span>
                            </div>
                          ))
                        ) : (
                          <p className="text-gray-500 text-sm">No paths configured</p>
                        )}
                      </div>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="data" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Data Summary</CardTitle>
                <CardDescription>
                  Overview of your stored data in the system
                </CardDescription>
              </CardHeader>
              <CardContent>
                {dataSummary && (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                      <div className="text-center p-4 bg-blue-50 rounded-lg">
                        <div className="text-2xl font-bold text-blue-600">
                          {dataSummary.data_counts.poker_hands || 0}
                        </div>
                        <div className="text-sm text-gray-600">Poker Hands</div>
                      </div>
                      <div className="text-center p-4 bg-green-50 rounded-lg">
                        <div className="text-2xl font-bold text-green-600">
                          {dataSummary.data_counts.analysis_results || 0}
                        </div>
                        <div className="text-sm text-gray-600">Analyses</div>
                      </div>
                      <div className="text-center p-4 bg-purple-50 rounded-lg">
                        <div className="text-2xl font-bold text-purple-600">
                          {dataSummary.data_counts.statistics_cache || 0}
                        </div>
                        <div className="text-sm text-gray-600">Cached Stats</div>
                      </div>
                    </div>
                    
                    <div className="text-center p-4 bg-gray-50 rounded-lg">
                      <div className="text-3xl font-bold text-gray-800">
                        {dataSummary.total_records}
                      </div>
                      <div className="text-sm text-gray-600">Total Records</div>
                    </div>
                    
                    <p className="text-xs text-gray-500 text-center">
                      Last updated: {new Date(dataSummary.summary_generated_at).toLocaleString()}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="privacy" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Data Export</CardTitle>
                <CardDescription>
                  Download all your data for backup or transfer purposes (GDPR compliance)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <p className="text-sm text-gray-600">
                    Export includes your account information, preferences, hand history data, 
                    analysis results, and statistics. API keys are not included for security reasons.
                  </p>
                  <Button 
                    onClick={handleExportData}
                    disabled={isExporting}
                    className="flex items-center gap-2"
                  >
                    <Download className="h-4 w-4" />
                    {isExporting ? 'Exporting...' : 'Export My Data'}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="danger" className="space-y-6">
            <Card className="border-red-200">
              <CardHeader>
                <CardTitle className="text-red-600">Delete Account</CardTitle>
                <CardDescription>
                  Permanently delete your account and all associated data. This action cannot be undone.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                      <AlertTriangle className="h-5 w-5 text-red-500 mt-0.5" />
                      <div className="space-y-2">
                        <h4 className="font-medium text-red-800">
                          This will permanently delete:
                        </h4>
                        <ul className="text-sm text-red-700 space-y-1">
                          <li>• Your account and all preferences</li>
                          <li>• All poker hand history data</li>
                          <li>• All AI analysis results</li>
                          <li>• All statistics and cached data</li>
                          <li>• All file monitoring settings</li>
                        </ul>
                      </div>
                    </div>
                  </div>

                  {!showDeleteConfirm ? (
                    <Button 
                      variant="destructive"
                      onClick={() => setShowDeleteConfirm(true)}
                      className="flex items-center gap-2"
                    >
                      <Trash2 className="h-4 w-4" />
                      Delete My Account
                    </Button>
                  ) : (
                    <div className="space-y-4 border border-red-200 rounded-lg p-4">
                      <h4 className="font-medium text-red-800">
                        Confirm Account Deletion
                      </h4>
                      <div className="space-y-2">
                        <Label htmlFor="delete-password">
                          Enter your password to confirm deletion:
                        </Label>
                        <Input
                          id="delete-password"
                          type="password"
                          value={deletePassword}
                          onChange={(e) => setDeletePassword(e.target.value)}
                          placeholder="Your current password"
                          className="max-w-sm"
                        />
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="destructive"
                          onClick={handleDeleteAccount}
                          disabled={isDeleting || !deletePassword.trim()}
                          className="flex items-center gap-2"
                        >
                          <Trash2 className="h-4 w-4" />
                          {isDeleting ? 'Deleting...' : 'Permanently Delete Account'}
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => {
                            setShowDeleteConfirm(false)
                            setDeletePassword('')
                          }}
                          disabled={isDeleting}
                        >
                          Cancel
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </Container>
  )
}