"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Play, RotateCcw, TrendingUp, TrendingDown, Minus } from "lucide-react"

interface InteractiveDemoProps {
  contentId: string
  title: string
}

export function InteractiveDemo({ contentId, title }: InteractiveDemoProps) {
  const renderDemo = () => {
    switch (contentId) {
      case "1": // VPIP Demo
        return <VPIPDemo />
      case "2": // PFR Demo  
        return <PFRDemo />
      case "3": // 3-Bet Demo
        return <ThreeBetDemo />
      case "4": // C-Bet Demo
        return <CBetDemo />
      case "5": // ICM Demo
        return <ICMDemo />
      default:
        return <DefaultDemo title={title} />
    }
  }

  return (
    <div className="border rounded-lg bg-muted/50">
      <div className="p-4 border-b bg-background rounded-t-lg">
        <div className="flex items-center gap-2">
          <Play className="h-4 w-4 text-primary" />
          <h4 className="font-semibold">Interactive Demo: {title}</h4>
        </div>
      </div>
      <div className="p-4">
        {renderDemo()}
      </div>
    </div>
  )
}

function DefaultDemo({ title }: { title: string }) {
  return (
    <div className="p-4 text-center text-muted-foreground">
      <Play className="h-8 w-8 mx-auto mb-2 opacity-50" />
      <p>Interactive demo for &quot;{title}&quot; coming soon...</p>
      <p className="text-sm mt-2">This will include hands-on examples and calculations.</p>
    </div>
  )
}

function VPIPDemo() {
  const [handsPlayed, setHandsPlayed] = useState(20)
  const [totalHands, setTotalHands] = useState(100)
  const [showExamples, setShowExamples] = useState(false)
  
  const vpip = totalHands > 0 ? (handsPlayed / totalHands * 100).toFixed(1) : "0"
  
  const getPlayerType = (vpip: number) => {
    if (vpip < 15) return { type: "Nit/Rock", color: "text-red-600", description: "Very tight - only premium hands" }
    if (vpip < 25) return { type: "Tight-Aggressive", color: "text-green-600", description: "Solid, profitable style" }
    if (vpip < 35) return { type: "Loose-Aggressive", color: "text-yellow-600", description: "Wide range, can be profitable" }
    return { type: "Maniac", color: "text-red-600", description: "Too loose - likely losing player" }
  }

  const playerType = getPlayerType(Number(vpip))

  const reset = () => {
    setHandsPlayed(20)
    setTotalHands(100)
    setShowExamples(false)
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-sm font-medium">Hands Played</label>
          <Input
            type="number"
            value={handsPlayed}
            onChange={(e) => setHandsPlayed(Math.max(0, Math.min(Number(e.target.value), totalHands)))}
            min="0"
            max={totalHands}
          />
        </div>
        <div>
          <label className="text-sm font-medium">Total Hands</label>
          <Input
            type="number"
            value={totalHands}
            onChange={(e) => {
              const newTotal = Math.max(1, Number(e.target.value))
              setTotalHands(newTotal)
              if (handsPlayed > newTotal) setHandsPlayed(newTotal)
            }}
            min="1"
          />
        </div>
      </div>
      
      <div className="text-center p-6 bg-primary/10 rounded-lg">
        <div className="text-3xl font-bold text-primary mb-2">{vpip}%</div>
        <div className="text-sm text-muted-foreground mb-3">VPIP (Voluntarily Put In Pot)</div>
        <Badge className={`${playerType.color} bg-transparent border`}>
          {playerType.type}
        </Badge>
        <p className="text-sm mt-2 text-muted-foreground">{playerType.description}</p>
      </div>

      <div className="flex gap-2">
        <Button onClick={() => setShowExamples(!showExamples)} variant="outline" size="sm">
          {showExamples ? "Hide" : "Show"} Examples
        </Button>
        <Button onClick={reset} variant="outline" size="sm">
          <RotateCcw className="h-4 w-4 mr-1" />
          Reset
        </Button>
      </div>

      {showExamples && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">VPIP Examples by Position</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <strong>Early Position (UTG):</strong>
                <ul className="text-xs text-muted-foreground mt-1 space-y-1">
                  <li>• Tight: 8-12% VPIP</li>
                  <li>• Standard: 12-16% VPIP</li>
                  <li>• Loose: 16-20% VPIP</li>
                </ul>
              </div>
              <div>
                <strong>Button:</strong>
                <ul className="text-xs text-muted-foreground mt-1 space-y-1">
                  <li>• Tight: 20-25% VPIP</li>
                  <li>• Standard: 25-35% VPIP</li>
                  <li>• Loose: 35-45% VPIP</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

function PFRDemo() {
  const [vpip, setVpip] = useState(20)
  const [pfr, setPfr] = useState(15)
  const [showAnalysis, setShowAnalysis] = useState(false)
  
  const gap = vpip - pfr
  const aggressionRatio = vpip > 0 ? (pfr / vpip * 100).toFixed(1) : "0"
  
  const getPlayStyle = (gap: number) => {
    if (gap <= 3) return { style: "Very Aggressive", color: "text-red-500", icon: TrendingUp }
    if (gap <= 6) return { style: "Balanced", color: "text-green-500", icon: Minus }
    if (gap <= 10) return { style: "Somewhat Passive", color: "text-yellow-500", icon: TrendingDown }
    return { style: "Very Passive", color: "text-red-500", icon: TrendingDown }
  }

  const playStyle = getPlayStyle(gap)
  const StyleIcon = playStyle.icon

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-sm font-medium">VPIP %</label>
          <Input
            type="number"
            value={vpip}
            onChange={(e) => setVpip(Math.max(0, Math.min(100, Number(e.target.value))))}
            min="0"
            max="100"
          />
        </div>
        <div>
          <label className="text-sm font-medium">PFR %</label>
          <Input
            type="number"
            value={pfr}
            onChange={(e) => setPfr(Math.max(0, Math.min(vpip, Number(e.target.value))))}
            min="0"
            max={vpip}
          />
        </div>
      </div>
      
      <div className="grid grid-cols-3 gap-4">
        <div className="text-center p-3 bg-primary/10 rounded-lg">
          <div className="text-xl font-bold text-primary">{gap}%</div>
          <div className="text-xs text-muted-foreground">VPIP-PFR Gap</div>
        </div>
        <div className="text-center p-3 bg-secondary/50 rounded-lg">
          <div className="text-xl font-bold">{aggressionRatio}%</div>
          <div className="text-xs text-muted-foreground">Raise/Play Ratio</div>
        </div>
        <div className="text-center p-3 bg-muted rounded-lg">
          <StyleIcon className={`h-5 w-5 mx-auto ${playStyle.color}`} />
          <div className={`text-xs font-medium ${playStyle.color}`}>{playStyle.style}</div>
        </div>
      </div>

      <div className="text-sm text-muted-foreground p-3 bg-muted/50 rounded-lg">
        <strong>Analysis:</strong> {gap <= 3 && "Rarely limps, almost always raises when entering pot"}
        {gap > 3 && gap <= 6 && "Good balance of raising and calling"}
        {gap > 6 && gap <= 10 && "Limps frequently, less aggressive preflop"}
        {gap > 10 && "Limps most hands, very passive preflop play"}
      </div>

      <Button onClick={() => setShowAnalysis(!showAnalysis)} variant="outline" size="sm">
        {showAnalysis ? "Hide" : "Show"} Detailed Analysis
      </Button>

      {showAnalysis && (
        <Card>
          <CardContent className="pt-4 space-y-3 text-sm">
            <div>
              <strong>What this means:</strong>
              <ul className="text-xs text-muted-foreground mt-1 space-y-1">
                <li>• VPIP: How often you play hands</li>
                <li>• PFR: How often you raise (vs call/limp)</li>
                <li>• Gap: Shows aggression level</li>
              </ul>
            </div>
            <div>
              <strong>Optimal ranges:</strong>
              <ul className="text-xs text-muted-foreground mt-1 space-y-1">
                <li>• 6-max: VPIP 20-25%, PFR 16-20%</li>
                <li>• 9-max: VPIP 15-20%, PFR 12-16%</li>
                <li>• Gap should be 3-6% for balanced play</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

function ThreeBetDemo() {
  const [position, setPosition] = useState("BTN")
  const [vsPosition, setVsPosition] = useState("CO")
  const [stackSize, setStackSize] = useState(100)
  const [showRanges, setShowRanges] = useState(false)

  const getRecommendedRange = () => {
    const stackMultiplier = stackSize >= 100 ? 1 : 0.8
    
    if (position === "BTN" && vsPosition === "CO") {
      return (10 * stackMultiplier).toFixed(1)
    }
    if (position === "SB" && vsPosition === "BTN") {
      return (12 * stackMultiplier).toFixed(1)
    }
    if (position === "BB" && vsPosition === "BTN") {
      return (8 * stackMultiplier).toFixed(1)
    }
    return (6 * stackMultiplier).toFixed(1)
  }

  const range = getRecommendedRange()

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="text-sm font-medium">Your Position</label>
          <Select value={position} onValueChange={setPosition}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="UTG">UTG</SelectItem>
              <SelectItem value="MP">MP</SelectItem>
              <SelectItem value="CO">CO</SelectItem>
              <SelectItem value="BTN">BTN</SelectItem>
              <SelectItem value="SB">SB</SelectItem>
              <SelectItem value="BB">BB</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <label className="text-sm font-medium">Vs Position</label>
          <Select value={vsPosition} onValueChange={setVsPosition}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="UTG">UTG</SelectItem>
              <SelectItem value="MP">MP</SelectItem>
              <SelectItem value="CO">CO</SelectItem>
              <SelectItem value="BTN">BTN</SelectItem>
              <SelectItem value="SB">SB</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <label className="text-sm font-medium">Stack (BB)</label>
          <Input
            type="number"
            value={stackSize}
            onChange={(e) => setStackSize(Math.max(20, Math.min(200, Number(e.target.value))))}
            min="20"
            max="200"
          />
        </div>
      </div>
      
      <div className="text-center p-6 bg-primary/10 rounded-lg">
        <div className="text-3xl font-bold text-primary">{range}%</div>
        <div className="text-sm text-muted-foreground mb-2">Recommended 3-Bet Frequency</div>
        <Badge variant="outline">
          {position} vs {vsPosition} ({stackSize}bb)
        </Badge>
      </div>

      <Button onClick={() => setShowRanges(!showRanges)} variant="outline" size="sm">
        {showRanges ? "Hide" : "Show"} Hand Ranges
      </Button>

      {showRanges && (
        <Tabs defaultValue="value" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="value">Value Hands</TabsTrigger>
            <TabsTrigger value="bluff">Bluff Hands</TabsTrigger>
          </TabsList>
          <TabsContent value="value" className="space-y-2">
            <div className="text-sm">
              <strong>Premium Value:</strong>
              <div className="flex flex-wrap gap-1 mt-1">
                {["AA", "KK", "QQ", "AK"].map(hand => (
                  <Badge key={hand} variant="default" className="text-xs">{hand}</Badge>
                ))}
              </div>
            </div>
            <div className="text-sm">
              <strong>Thin Value:</strong>
              <div className="flex flex-wrap gap-1 mt-1">
                {["JJ", "TT", "AQ", "AJs"].map(hand => (
                  <Badge key={hand} variant="secondary" className="text-xs">{hand}</Badge>
                ))}
              </div>
            </div>
          </TabsContent>
          <TabsContent value="bluff" className="space-y-2">
            <div className="text-sm">
              <strong>Suited Aces:</strong>
              <div className="flex flex-wrap gap-1 mt-1">
                {["A5s", "A4s", "A3s", "A2s"].map(hand => (
                  <Badge key={hand} variant="outline" className="text-xs">{hand}</Badge>
                ))}
              </div>
            </div>
            <div className="text-sm">
              <strong>Suited Connectors:</strong>
              <div className="flex flex-wrap gap-1 mt-1">
                {["65s", "54s", "76s", "87s"].map(hand => (
                  <Badge key={hand} variant="outline" className="text-xs">{hand}</Badge>
                ))}
              </div>
            </div>
          </TabsContent>
        </Tabs>
      )}
    </div>
  )
}

function CBetDemo() {
  const [boardTexture, setBoardTexture] = useState("dry")
  const [playerCount, setPlayerCount] = useState("heads-up")
  const [position, setPosition] = useState("IP")
  const [showStrategy, setShowStrategy] = useState(false)

  const getRecommendedFreq = () => {
    let base = 70
    if (boardTexture === "wet") base -= 20
    if (boardTexture === "very-wet") base -= 35
    if (playerCount === "multiway") base -= 15
    if (position === "OOP") base -= 10
    return Math.max(base, 30)
  }

  const freq = getRecommendedFreq()
  
  const getBoardExample = () => {
    switch (boardTexture) {
      case "dry": return "A♠ 7♣ 2♦"
      case "wet": return "T♠ 9♣ 8♦"
      case "very-wet": return "9♠ 8♠ 7♣"
      default: return "A♠ 7♣ 2♦"
    }
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="text-sm font-medium">Board Texture</label>
          <Select value={boardTexture} onValueChange={setBoardTexture}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="dry">Dry Board</SelectItem>
              <SelectItem value="wet">Wet Board</SelectItem>
              <SelectItem value="very-wet">Very Wet</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <label className="text-sm font-medium">Opponents</label>
          <Select value={playerCount} onValueChange={setPlayerCount}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="heads-up">Heads-up</SelectItem>
              <SelectItem value="multiway">Multiway</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <label className="text-sm font-medium">Position</label>
          <Select value={position} onValueChange={setPosition}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="IP">In Position</SelectItem>
              <SelectItem value="OOP">Out of Position</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      
      <div className="text-center p-6 bg-primary/10 rounded-lg">
        <div className="text-3xl font-bold text-primary">{freq}%</div>
        <div className="text-sm text-muted-foreground mb-2">Recommended C-Bet Frequency</div>
        <div className="text-lg font-mono bg-background px-3 py-1 rounded border">
          {getBoardExample()}
        </div>
      </div>

      <Button onClick={() => setShowStrategy(!showStrategy)} variant="outline" size="sm">
        {showStrategy ? "Hide" : "Show"} Strategy Notes
      </Button>

      {showStrategy && (
        <Card>
          <CardContent className="pt-4 space-y-3 text-sm">
            <div>
              <strong>Why this frequency?</strong>
              <ul className="text-xs text-muted-foreground mt-1 space-y-1">
                <li>• Dry boards favor the preflop raiser&apos;s range</li>
                <li>• Wet boards connect with calling ranges</li>
                <li>• Multiway pots require stronger hands</li>
                <li>• Position affects betting frequency</li>
              </ul>
            </div>
            <div>
              <strong>Bet sizing:</strong>
              <ul className="text-xs text-muted-foreground mt-1 space-y-1">
                <li>• Dry boards: 33-50% pot</li>
                <li>• Wet boards: 66-75% pot</li>
                <li>• Protection vs value consideration</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

function ICMDemo() {
  const [chipStack, setChipStack] = useState(10000)
  const [totalChips, setTotalChips] = useState(50000)
  const [prizePool, setPrizePool] = useState(1000)
  const [playersLeft, setPlayersLeft] = useState(5)
  const [showCalculation, setShowCalculation] = useState(false)

  // Simplified ICM calculation
  const chipPercentage = totalChips > 0 ? (chipStack / totalChips * 100).toFixed(1) : "0"
  const icmValue = totalChips > 0 ? (prizePool * chipStack / totalChips * 0.85).toFixed(0) : "0" // Simplified

  const getStackStatus = (percentage: number) => {
    if (percentage >= 40) return { status: "Chip Leader", color: "text-green-600" }
    if (percentage >= 25) return { status: "Big Stack", color: "text-blue-600" }
    if (percentage >= 15) return { status: "Medium Stack", color: "text-yellow-600" }
    if (percentage >= 8) return { status: "Short Stack", color: "text-orange-600" }
    return { status: "Critical", color: "text-red-600" }
  }

  const stackStatus = getStackStatus(Number(chipPercentage))

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-sm font-medium">Your Chips</label>
          <Input
            type="number"
            value={chipStack}
            onChange={(e) => setChipStack(Math.max(1000, Number(e.target.value)))}
            min="1000"
          />
        </div>
        <div>
          <label className="text-sm font-medium">Total Chips</label>
          <Input
            type="number"
            value={totalChips}
            onChange={(e) => setTotalChips(Math.max(chipStack, Number(e.target.value)))}
            min={chipStack}
          />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-sm font-medium">Prize Pool ($)</label>
          <Input
            type="number"
            value={prizePool}
            onChange={(e) => setPrizePool(Math.max(100, Number(e.target.value)))}
            min="100"
          />
        </div>
        <div>
          <label className="text-sm font-medium">Players Left</label>
          <Input
            type="number"
            value={playersLeft}
            onChange={(e) => setPlayersLeft(Math.max(2, Math.min(9, Number(e.target.value))))}
            min="2"
            max="9"
          />
        </div>
      </div>
      
      <div className="grid grid-cols-3 gap-4">
        <div className="text-center p-3 bg-primary/10 rounded-lg">
          <div className="text-xl font-bold text-primary">{chipPercentage}%</div>
          <div className="text-xs text-muted-foreground">Chip Share</div>
        </div>
        <div className="text-center p-3 bg-secondary/50 rounded-lg">
          <div className="text-xl font-bold">${icmValue}</div>
          <div className="text-xs text-muted-foreground">ICM Value</div>
        </div>
        <div className="text-center p-3 bg-muted rounded-lg">
          <div className={`text-sm font-bold ${stackStatus.color}`}>{stackStatus.status}</div>
          <div className="text-xs text-muted-foreground">Stack Size</div>
        </div>
      </div>

      <div className="text-sm text-muted-foreground p-3 bg-muted/50 rounded-lg">
        <strong>ICM Impact:</strong> Chips lose value as your stack grows. 
        {Number(chipPercentage) >= 30 && " Play tighter to preserve equity."}
        {Number(chipPercentage) < 15 && " Look for spots to accumulate chips."}
      </div>

      <Button onClick={() => setShowCalculation(!showCalculation)} variant="outline" size="sm">
        {showCalculation ? "Hide" : "Show"} ICM Strategy
      </Button>

      {showCalculation && (
        <Card>
          <CardContent className="pt-4 space-y-3 text-sm">
            <div>
              <strong>Strategy Adjustments:</strong>
              <ul className="text-xs text-muted-foreground mt-1 space-y-1">
                <li>• Big stacks: Avoid marginal spots, apply pressure</li>
                <li>• Medium stacks: Balanced approach, avoid big stacks</li>
                <li>• Short stacks: Look for double-up opportunities</li>
                <li>• Bubble: Extreme ICM pressure, fold more</li>
              </ul>
            </div>
            <div>
              <strong>Key Concepts:</strong>
              <ul className="text-xs text-muted-foreground mt-1 space-y-1">
                <li>• Chip value decreases as stack size increases</li>
                <li>• Survival is often more valuable than chip accumulation</li>
                <li>• Position and stack sizes affect decision making</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}