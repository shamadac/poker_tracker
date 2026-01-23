"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Container } from "@/components/ui/container"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { LoadingButton } from "@/components/loading-states"
import { TermLinkedContent } from "@/components/ui/term-linked-content"
import { useState, useCallback } from "react"
import { Upload, FileText, Zap, Brain, Clock, TrendingUp, AlertCircle, CheckCircle } from "lucide-react"

// Analysis interfaces
interface AnalysisRequest {
  handHistory: string
  provider: 'groq' | 'gemini'
  depth: 'basic' | 'standard' | 'advanced'
  analysisType: 'single' | 'session'
}

interface AnalysisResult {
  id: string
  handId: string
  provider: 'groq' | 'gemini'
  depth: string
  timestamp: string
  analysis: {
    summary: string
    strengths: string[]
    mistakes: string[]
    recommendations: string[]
    confidence: number
  }
  handDetails: {
    gameType: string
    stakes: string
    position: string
    cards: string[]
    actions: string[]
    result: string
    potSize: number
  }
  processingTime: number
}

interface RecentAnalysis {
  id: string
  title: string
  timestamp: string
  provider: string
  confidence: number
  result: 'positive' | 'negative' | 'neutral'
}

export default function Analysis() {
  const [analysisRequest, setAnalysisRequest] = useState<AnalysisRequest>({
    handHistory: '',
    provider: 'groq',
    depth: 'standard',
    analysisType: 'single'
  })
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [currentAnalysis, setCurrentAnalysis] = useState<AnalysisResult | null>(null)
  const [recentAnalyses, setRecentAnalyses] = useState<RecentAnalysis[]>([
    {
      id: '1',
      title: 'AK vs QQ - Button vs UTG',
      timestamp: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
      provider: 'Gemini',
      confidence: 87,
      result: 'positive'
    },
    {
      id: '2',
      title: '77 vs AA - Small Blind vs Big Blind',
      timestamp: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
      provider: 'Groq',
      confidence: 92,
      result: 'negative'
    },
    {
      id: '3',
      title: 'A5s Bluff - CO vs BTN',
      timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
      provider: 'Gemini',
      confidence: 78,
      result: 'neutral'
    },
    {
      id: '4',
      title: 'KQ Suited - MP vs BB',
      timestamp: new Date(Date.now() - 8 * 60 * 60 * 1000).toISOString(),
      provider: 'Groq',
      confidence: 85,
      result: 'positive'
    }
  ])

  const handleAnalyze = useCallback(async () => {
    if (!analysisRequest.handHistory.trim()) {
      alert('Please enter a hand history to analyze')
      return
    }

    setIsAnalyzing(true)
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 
        analysisRequest.provider === 'groq' ? 2000 : 4000
      ))

      // Mock analysis result
      const mockResult: AnalysisResult = {
        id: `analysis-${Date.now()}`,
        handId: 'PS123456789',
        provider: analysisRequest.provider,
        depth: analysisRequest.depth,
        timestamp: new Date().toISOString(),
        analysis: {
          summary: analysisRequest.provider === 'groq' 
            ? "Quick analysis: This was a well-played hand with good position awareness. The preflop raise sizing was appropriate, and the continuation bet on the flop showed good aggression."
            : "Comprehensive analysis: This hand demonstrates excellent strategic thinking. Your preflop raise from the cutoff with AK was textbook, sizing at 3x the big blind. The flop continuation bet of 65% pot was well-sized for value and protection. Your turn decision to check-call showed good pot control against a tight opponent. The river fold was disciplined, avoiding a marginal spot against likely value.",
          strengths: [
            "Excellent preflop positioning",
            "Appropriate bet sizing throughout",
            "Good hand reading on the river",
            "Disciplined fold in marginal spot"
          ],
          mistakes: [
            "Could have considered a smaller c-bet size on this dry board",
            "Turn check might have been too passive against this opponent type"
          ],
          recommendations: [
            "Consider varying your c-bet sizes based on board texture",
            "Against tight opponents, lean towards more aggressive lines",
            "Study opponent's fold-to-c-bet statistics for better sizing",
            "Review similar spots in your database for pattern recognition"
          ],
          confidence: analysisRequest.provider === 'groq' ? 85 : 92
        },
        handDetails: {
          gameType: 'NL Hold\'em',
          stakes: '$0.25/$0.50',
          position: 'Cutoff',
          cards: ['A♠', 'K♦'],
          actions: ['Raise $1.50', 'Call', 'Bet $2.25', 'Call', 'Check', 'Call $4.50', 'Fold'],
          result: 'Lost',
          potSize: 18.75
        },
        processingTime: analysisRequest.provider === 'groq' ? 1.8 : 3.7
      }

      setCurrentAnalysis(mockResult)
      
      // Add to recent analyses
      const newRecentAnalysis: RecentAnalysis = {
        id: mockResult.id,
        title: `${mockResult.handDetails.cards.join('')} - ${mockResult.handDetails.position}`,
        timestamp: mockResult.timestamp,
        provider: mockResult.provider === 'groq' ? 'Groq' : 'Gemini',
        confidence: mockResult.analysis.confidence,
        result: mockResult.handDetails.result === 'Won' ? 'positive' : 'negative'
      }
      
      setRecentAnalyses(prev => [newRecentAnalysis, ...prev.slice(0, 9)])
      
    } catch (error) {
      console.error('Analysis failed:', error)
      alert('Analysis failed. Please try again.')
    } finally {
      setIsAnalyzing(false)
    }
  }, [analysisRequest])

  const handleFileUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        const content = e.target?.result as string
        setAnalysisRequest(prev => ({ ...prev, handHistory: content }))
      }
      reader.readAsText(file)
    }
  }, [])

  const loadSampleHand = useCallback(() => {
    const sampleHand = `PokerStars Hand #123456789: Hold'em No Limit ($0.25/$0.50 USD) - 2024/01/20 15:30:00 ET
Table 'Sample Table' 6-max Seat #3 is the button
Seat 1: Player1 ($50.00 in chips)
Seat 2: Player2 ($75.25 in chips)
Seat 3: Hero ($100.00 in chips)
Seat 4: Player4 ($45.50 in chips)
Seat 5: Player5 ($80.75 in chips)
Seat 6: Player6 ($60.00 in chips)
Player4: posts small blind $0.25
Player5: posts big blind $0.50
*** HOLE CARDS ***
Dealt to Hero [As Kd]
Player6: folds
Player1: folds
Player2: folds
Hero: raises $1.50 to $2.00
Player4: folds
Player5: calls $1.50
*** FLOP *** [Ah 7c 2s]
Player5: checks
Hero: bets $2.25
Player5: calls $2.25
*** TURN *** [Ah 7c 2s] [9h]
Player5: checks
Hero: checks
*** RIVER *** [Ah 7c 2s 9h] [Kh]
Player5: bets $4.50
Hero: folds
Player5 collected $8.75 from pot
*** SUMMARY ***
Total pot $9.00 | Rake $0.25
Board [Ah 7c 2s 9h Kh]
Seat 3: Hero (button) folded on the River`

    setAnalysisRequest(prev => ({ ...prev, handHistory: sampleHand }))
  }, [])

  return (
    <Container className="py-4 sm:py-6 lg:py-8">
      <div className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold">Hand Analysis</h1>
        <p className="text-muted-foreground text-sm sm:text-base">
          <TermLinkedContent 
            content="Analyze poker hands with AI-powered insights and strategic recommendations using advanced hand analysis techniques"
            context="analysis"
            maxLinks={3}
          />
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 sm:gap-6">
        {/* Hand Input Section */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg sm:text-xl flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Hand Input
            </CardTitle>
            <CardDescription className="text-sm">
              Paste your hand history, upload a file, or use a sample hand
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Hand History Input */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                Hand History
              </label>
              <textarea
                className="w-full h-32 sm:h-40 p-3 border rounded-md resize-none text-sm font-mono"
                placeholder="Paste your PokerStars or GGPoker hand history here..."
                value={analysisRequest.handHistory}
                onChange={(e) => setAnalysisRequest(prev => ({ 
                  ...prev, 
                  handHistory: e.target.value 
                }))}
              />
            </div>

            {/* File Upload and Sample */}
            <div className="flex flex-col sm:flex-row gap-2">
              <div className="flex-1">
                <input
                  type="file"
                  accept=".txt,.log"
                  onChange={handleFileUpload}
                  className="hidden"
                  id="file-upload"
                />
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => document.getElementById('file-upload')?.click()}
                >
                  <Upload className="h-4 w-4 mr-2" />
                  Upload File
                </Button>
              </div>
              <Button
                variant="outline"
                className="flex-1"
                onClick={loadSampleHand}
              >
                Load Sample
              </Button>
            </div>
            
            {/* Analysis Configuration */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  AI Provider
                </label>
                <Select 
                  value={analysisRequest.provider} 
                  onValueChange={(value: 'groq' | 'gemini') => 
                    setAnalysisRequest(prev => ({ ...prev, provider: value }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="groq">
                      <div className="flex items-center gap-2">
                        <Zap className="h-4 w-4" />
                        Groq (Fast)
                      </div>
                    </SelectItem>
                    <SelectItem value="gemini">
                      <div className="flex items-center gap-2">
                        <Brain className="h-4 w-4" />
                        Gemini (Detailed)
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">
                  Analysis Depth
                </label>
                <Select 
                  value={analysisRequest.depth} 
                  onValueChange={(value: 'basic' | 'standard' | 'advanced') => 
                    setAnalysisRequest(prev => ({ ...prev, depth: value }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="basic">Basic</SelectItem>
                    <SelectItem value="standard">Standard</SelectItem>
                    <SelectItem value="advanced">Advanced</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Analysis Type */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                Analysis Type
              </label>
              <div className="flex gap-2">
                <Button
                  variant={analysisRequest.analysisType === 'single' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setAnalysisRequest(prev => ({ ...prev, analysisType: 'single' }))}
                >
                  Single Hand
                </Button>
                <Button
                  variant={analysisRequest.analysisType === 'session' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setAnalysisRequest(prev => ({ ...prev, analysisType: 'session' }))}
                >
                  Session Analysis
                </Button>
              </div>
            </div>

            <LoadingButton 
              className="w-full" 
              loading={isAnalyzing}
              onClick={handleAnalyze}
              disabled={!analysisRequest.handHistory.trim()}
            >
              {isAnalyzing ? 'Analyzing...' : 'Analyze Hand'}
            </LoadingButton>
          </CardContent>
        </Card>

        {/* Analysis Results Section */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg sm:text-xl flex items-center gap-2">
              <Brain className="h-5 w-5" />
              Analysis Results
            </CardTitle>
            <CardDescription className="text-sm">
              AI-powered strategic insights and recommendations
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!currentAnalysis ? (
              <div className="h-[400px] sm:h-[500px] flex items-center justify-center text-muted-foreground text-sm text-center p-4">
                <div className="space-y-2">
                  <Brain className="h-12 w-12 mx-auto opacity-50" />
                  <p>Analysis results will appear here after submitting a hand</p>
                  <p className="text-xs">Choose your AI provider and analysis depth, then click &quot;Analyze Hand&quot;</p>
                </div>
              </div>
            ) : (
              <Tabs defaultValue="summary" className="w-full">
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="summary">Summary</TabsTrigger>
                  <TabsTrigger value="details">Details</TabsTrigger>
                  <TabsTrigger value="recommendations">Tips</TabsTrigger>
                  <TabsTrigger value="hand">Hand</TabsTrigger>
                </TabsList>

                <TabsContent value="summary" className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">
                        {currentAnalysis.provider === 'groq' ? 'Groq' : 'Gemini'}
                      </Badge>
                      <Badge variant="secondary">
                        {currentAnalysis.depth}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Clock className="h-4 w-4" />
                      {currentAnalysis.processingTime}s
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <h4 className="font-semibold mb-2 flex items-center gap-2">
                        <TrendingUp className="h-4 w-4" />
                        Analysis Summary
                      </h4>
                      <TermLinkedContent 
                        content={currentAnalysis.analysis.summary}
                        context="analysis"
                        maxLinks={5}
                        className="text-sm text-muted-foreground leading-relaxed"
                      />
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">Confidence:</span>
                      <div className="flex-1 bg-muted rounded-full h-2">
                        <div 
                          className="bg-primary h-2 rounded-full transition-all duration-500"
                          style={{ width: `${currentAnalysis.analysis.confidence}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium">{currentAnalysis.analysis.confidence}%</span>
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="details" className="space-y-4">
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-semibold mb-2 flex items-center gap-2 text-green-600">
                        <CheckCircle className="h-4 w-4" />
                        Strengths
                      </h4>
                      <ul className="space-y-1">
                        {currentAnalysis.analysis.strengths.map((strength, index) => (
                          <li key={index} className="text-sm text-muted-foreground flex items-start gap-2">
                            <span className="text-green-500 mt-1">•</span>
                            <TermLinkedContent 
                              content={strength}
                              context="analysis"
                              maxLinks={2}
                            />
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div>
                      <h4 className="font-semibold mb-2 flex items-center gap-2 text-red-600">
                        <AlertCircle className="h-4 w-4" />
                        Areas for Improvement
                      </h4>
                      <ul className="space-y-1">
                        {currentAnalysis.analysis.mistakes.map((mistake, index) => (
                          <li key={index} className="text-sm text-muted-foreground flex items-start gap-2">
                            <span className="text-red-500 mt-1">•</span>
                            <TermLinkedContent 
                              content={mistake}
                              context="analysis"
                              maxLinks={2}
                            />
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="recommendations" className="space-y-4">
                  <div>
                    <h4 className="font-semibold mb-3">Strategic Recommendations</h4>
                    <div className="space-y-3">
                      {currentAnalysis.analysis.recommendations.map((rec, index) => (
                        <div key={index} className="p-3 bg-muted/50 rounded-lg">
                          <TermLinkedContent 
                            content={rec}
                            context="analysis"
                            maxLinks={3}
                            className="text-sm"
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="hand" className="space-y-4">
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-medium">Game:</span> {currentAnalysis.handDetails.gameType}
                      </div>
                      <div>
                        <span className="font-medium">Stakes:</span> {currentAnalysis.handDetails.stakes}
                      </div>
                      <div>
                        <span className="font-medium">Position:</span> {currentAnalysis.handDetails.position}
                      </div>
                      <div>
                        <span className="font-medium">Result:</span> 
                        <span className={`ml-1 ${currentAnalysis.handDetails.result === 'Won' ? 'text-green-600' : 'text-red-600'}`}>
                          {currentAnalysis.handDetails.result}
                        </span>
                      </div>
                    </div>

                    <div>
                      <span className="font-medium text-sm">Cards:</span>
                      <div className="flex gap-2 mt-1">
                        {currentAnalysis.handDetails.cards.map((card, index) => (
                          <span key={index} className="bg-muted px-2 py-1 rounded text-sm font-mono">
                            {card}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div>
                      <span className="font-medium text-sm">Pot Size:</span>
                      <span className="ml-2 text-sm">${currentAnalysis.handDetails.potSize}</span>
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Analyses */}
      <Card className="mt-4 sm:mt-6">
        <CardHeader>
          <CardTitle className="text-lg sm:text-xl">Recent Analyses</CardTitle>
          <CardDescription className="text-sm">
            Your previously analyzed hands
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 sm:space-y-4">
            {recentAnalyses.map((analysis) => (
              <div key={analysis.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-3 sm:p-4 border rounded-lg gap-3 sm:gap-4 hover:bg-muted/50 transition-colors">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <p className="font-medium text-sm sm:text-base">{analysis.title}</p>
                    <Badge variant="outline" className="text-xs">
                      {analysis.provider}
                    </Badge>
                    <div className={`w-2 h-2 rounded-full ${
                      analysis.result === 'positive' ? 'bg-green-500' :
                      analysis.result === 'negative' ? 'bg-red-500' : 'bg-yellow-500'
                    }`} />
                  </div>
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <span>{new Date(analysis.timestamp).toLocaleString()}</span>
                    <span>Confidence: {analysis.confidence}%</span>
                  </div>
                </div>
                <Button variant="outline" size="sm" className="w-full sm:w-auto">
                  View Analysis
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </Container>
  )
}