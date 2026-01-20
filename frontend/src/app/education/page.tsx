"use client"

import { useState, useEffect, useMemo } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Search, BookOpen, Star, Bookmark, Play, Calculator, TrendingUp, Users, Target } from "lucide-react"
import { InteractiveDemo } from "@/components/education/interactive-demos"

// Mock data - in real app this would come from API
const mockEducationContent = [
  {
    id: "1",
    title: "VPIP (Voluntarily Put In Pot)",
    slug: "vpip",
    category: "basic",
    difficulty: "beginner",
    definition: "The percentage of hands a player voluntarily puts money into the pot preflop.",
    explanation: "VPIP is one of the most fundamental poker statistics. It measures how often a player chooses to play a hand by calling, betting, or raising preflop. A tight player might have a VPIP of 15-20%, while a loose player could have 30%+.",
    examples: [
      "If you play 20 out of 100 hands, your VPIP is 20%",
      "Tight-aggressive players typically have VPIP of 15-25%",
      "Loose-aggressive players often have VPIP of 25-35%"
    ],
    tags: ["preflop", "statistics", "fundamental"],
    interactive_demo: true,
    video_url: "https://example.com/vpip-video",
    progress: null
  },
  {
    id: "2",
    title: "PFR (Preflop Raise)",
    slug: "pfr",
    category: "basic",
    difficulty: "beginner",
    definition: "The percentage of hands a player raises preflop when they enter the pot.",
    explanation: "PFR measures aggression preflop. The gap between VPIP and PFR shows how often a player limps vs raises. A smaller gap indicates more aggressive play.",
    examples: [
      "VPIP 20%, PFR 15% = raises 75% of played hands",
      "Large VPIP-PFR gap suggests passive play",
      "Small gap indicates aggressive style"
    ],
    tags: ["preflop", "aggression", "statistics"],
    interactive_demo: true,
    video_url: null,
    progress: { is_read: true, is_bookmarked: false, is_favorite: true }
  },
  {
    id: "3",
    title: "3-Bet Percentage",
    slug: "three-bet-percentage",
    category: "advanced",
    difficulty: "intermediate",
    definition: "The frequency with which a player re-raises (3-bets) after facing a preflop raise.",
    explanation: "3-betting is a crucial advanced concept. It's used for value with strong hands and as a bluff with weaker hands. Optimal 3-bet ranges depend on position, opponent tendencies, and stack sizes.",
    examples: [
      "Typical 3-bet range: 5-8% from most positions",
      "Button 3-bet vs CO open: 8-12%",
      "Polarized 3-bet range: AA-QQ, AK, A5s-A2s, suited connectors"
    ],
    tags: ["preflop", "advanced", "3-betting", "ranges"],
    interactive_demo: true,
    video_url: "https://example.com/3bet-video",
    progress: null
  },
  {
    id: "4",
    title: "C-Bet (Continuation Bet)",
    slug: "c-bet",
    category: "advanced",
    difficulty: "intermediate",
    definition: "A bet made by the preflop aggressor on the flop, continuing their aggressive line.",
    explanation: "C-betting is fundamental to postflop play. The preflop raiser has a range advantage on most flops and should bet frequently. C-bet frequency varies by board texture, position, and opponent count.",
    examples: [
      "Dry boards (A72r): C-bet 80-90%",
      "Wet boards (987r): C-bet 40-60%",
      "Heads-up vs multiway affects frequency"
    ],
    tags: ["postflop", "c-betting", "aggression"],
    interactive_demo: true,
    video_url: null,
    progress: { is_read: false, is_bookmarked: true, is_favorite: false }
  },
  {
    id: "5",
    title: "ICM (Independent Chip Model)",
    slug: "icm",
    category: "tournament",
    difficulty: "advanced",
    definition: "A mathematical model used to calculate the real money value of tournament chips.",
    explanation: "ICM is crucial for tournament play, especially near the bubble and final table. It shows that chips lose value as your stack grows, leading to more conservative play in certain situations.",
    examples: [
      "Bubble play: Avoid marginal spots",
      "Final table: Short stacks have fold equity",
      "Chip leader should apply pressure"
    ],
    tags: ["tournament", "icm", "bubble", "strategy"],
    interactive_demo: true,
    video_url: "https://example.com/icm-video",
    progress: null
  }
]

const categories = [
  { value: "all", label: "All Categories", icon: BookOpen },
  { value: "basic", label: "Basic Concepts", icon: Target },
  { value: "advanced", label: "Advanced Strategy", icon: TrendingUp },
  { value: "tournament", label: "Tournament Play", icon: Users },
  { value: "cash_game", label: "Cash Games", icon: Calculator }
]

const difficulties = [
  { value: "all", label: "All Levels" },
  { value: "beginner", label: "Beginner" },
  { value: "intermediate", label: "Intermediate" },
  { value: "advanced", label: "Advanced" }
]

export default function EducationPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedCategory, setSelectedCategory] = useState("all")
  const [selectedDifficulty, setSelectedDifficulty] = useState("all")
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false)
  const [showBookmarksOnly, setShowBookmarksOnly] = useState(false)

  // Filter content based on search criteria
  const filteredContent = useMemo(() => {
    return mockEducationContent.filter(content => {
      // Search query filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase()
        const matchesSearch = 
          content.title.toLowerCase().includes(query) ||
          content.definition.toLowerCase().includes(query) ||
          content.explanation.toLowerCase().includes(query) ||
          content.tags.some(tag => tag.toLowerCase().includes(query))
        
        if (!matchesSearch) return false
      }

      // Category filter
      if (selectedCategory !== "all" && content.category !== selectedCategory) {
        return false
      }

      // Difficulty filter
      if (selectedDifficulty !== "all" && content.difficulty !== selectedDifficulty) {
        return false
      }

      // Tags filter
      if (selectedTags.length > 0) {
        const hasMatchingTag = selectedTags.some(tag => 
          content.tags.includes(tag)
        )
        if (!hasMatchingTag) return false
      }

      // Favorites filter
      if (showFavoritesOnly && (!content.progress?.is_favorite)) {
        return false
      }

      // Bookmarks filter
      if (showBookmarksOnly && (!content.progress?.is_bookmarked)) {
        return false
      }

      return true
    })
  }, [searchQuery, selectedCategory, selectedDifficulty, selectedTags, showFavoritesOnly, showBookmarksOnly])

  // Get all unique tags from content
  const allTags = useMemo(() => {
    const tags = new Set<string>()
    mockEducationContent.forEach(content => {
      content.tags.forEach(tag => tags.add(tag))
    })
    return Array.from(tags).sort()
  }, [])

  const toggleTag = (tag: string) => {
    setSelectedTags(prev => 
      prev.includes(tag) 
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Poker Education</h1>
        <p className="text-muted-foreground">
          Learn poker concepts, statistics, and strategies with interactive examples and demos.
        </p>
      </div>

      {/* Search and Filters */}
      <div className="mb-8 space-y-4">
        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search education content..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Filter Controls */}
        <div className="flex flex-wrap gap-4 items-center">
          <Select value={selectedCategory} onValueChange={setSelectedCategory}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Category" />
            </SelectTrigger>
            <SelectContent>
              {categories.map(category => (
                <SelectItem key={category.value} value={category.value}>
                  <div className="flex items-center gap-2">
                    <category.icon className="h-4 w-4" />
                    {category.label}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={selectedDifficulty} onValueChange={setSelectedDifficulty}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Difficulty" />
            </SelectTrigger>
            <SelectContent>
              {difficulties.map(difficulty => (
                <SelectItem key={difficulty.value} value={difficulty.value}>
                  {difficulty.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <div className="flex gap-2">
            <Button
              variant={showFavoritesOnly ? "default" : "outline"}
              size="sm"
              onClick={() => setShowFavoritesOnly(!showFavoritesOnly)}
            >
              <Star className="h-4 w-4 mr-1" />
              Favorites
            </Button>
            <Button
              variant={showBookmarksOnly ? "default" : "outline"}
              size="sm"
              onClick={() => setShowBookmarksOnly(!showBookmarksOnly)}
            >
              <Bookmark className="h-4 w-4 mr-1" />
              Bookmarks
            </Button>
          </div>
        </div>

        {/* Tag Filters */}
        {allTags.length > 0 && (
          <div className="space-y-2">
            <label className="text-sm font-medium">Filter by tags:</label>
            <div className="flex flex-wrap gap-2">
              {allTags.map(tag => (
                <Badge
                  key={tag}
                  variant={selectedTags.includes(tag) ? "default" : "outline"}
                  className="cursor-pointer"
                  onClick={() => toggleTag(tag)}
                >
                  {tag}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Active Filters Summary */}
        {(selectedTags.length > 0 || selectedCategory !== "all" || selectedDifficulty !== "all" || showFavoritesOnly || showBookmarksOnly) && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>Active filters:</span>
            {selectedCategory !== "all" && (
              <Badge variant="secondary">{categories.find(c => c.value === selectedCategory)?.label}</Badge>
            )}
            {selectedDifficulty !== "all" && (
              <Badge variant="secondary">{difficulties.find(d => d.value === selectedDifficulty)?.label}</Badge>
            )}
            {selectedTags.map(tag => (
              <Badge key={tag} variant="secondary">{tag}</Badge>
            ))}
            {showFavoritesOnly && <Badge variant="secondary">Favorites</Badge>}
            {showBookmarksOnly && <Badge variant="secondary">Bookmarks</Badge>}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setSelectedCategory("all")
                setSelectedDifficulty("all")
                setSelectedTags([])
                setShowFavoritesOnly(false)
                setShowBookmarksOnly(false)
              }}
            >
              Clear all
            </Button>
          </div>
        )}
      </div>

      {/* Results Summary */}
      <div className="mb-6">
        <p className="text-sm text-muted-foreground">
          Showing {filteredContent.length} of {mockEducationContent.length} results
        </p>
      </div>

      {/* Content Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {filteredContent.map(content => (
          <Card key={content.id} className="h-fit">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="space-y-2">
                  <CardTitle className="text-lg">{content.title}</CardTitle>
                  <div className="flex gap-2">
                    <Badge variant="outline" className="text-xs">
                      {content.category.replace('_', ' ')}
                    </Badge>
                    <Badge 
                      variant={
                        content.difficulty === 'beginner' ? 'default' :
                        content.difficulty === 'intermediate' ? 'secondary' : 'destructive'
                      }
                      className="text-xs"
                    >
                      {content.difficulty}
                    </Badge>
                  </div>
                </div>
                <div className="flex gap-1">
                  {content.progress?.is_favorite && (
                    <Star className="h-4 w-4 text-yellow-500 fill-current" />
                  )}
                  {content.progress?.is_bookmarked && (
                    <Bookmark className="h-4 w-4 text-blue-500 fill-current" />
                  )}
                </div>
              </div>
              <CardDescription>{content.definition}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground line-clamp-3">
                {content.explanation}
              </p>

              {/* Tags */}
              <div className="flex flex-wrap gap-1">
                {content.tags.map(tag => (
                  <Badge key={tag} variant="outline" className="text-xs">
                    {tag}
                  </Badge>
                ))}
              </div>

              {/* Interactive Demo */}
              {content.interactive_demo && (
                <div className="pt-4 border-t">
                  <Tabs defaultValue="overview" className="w-full">
                    <TabsList className="grid w-full grid-cols-2">
                      <TabsTrigger value="overview">Overview</TabsTrigger>
                      <TabsTrigger value="demo">Interactive Demo</TabsTrigger>
                    </TabsList>
                    <TabsContent value="overview" className="space-y-2">
                      <h4 className="font-semibold text-sm">Examples:</h4>
                      <ul className="text-xs space-y-1 text-muted-foreground">
                        {content.examples.slice(0, 2).map((example, idx) => (
                          <li key={idx}>• {example}</li>
                        ))}
                      </ul>
                    </TabsContent>
                    <TabsContent value="demo">
                      <InteractiveDemo contentId={content.id} title={content.title} />
                    </TabsContent>
                  </Tabs>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-2 pt-2">
                <Button size="sm" className="flex-1">
                  Read More
                </Button>
                <Button size="sm" variant="outline">
                  <Bookmark className="h-4 w-4" />
                </Button>
                <Button size="sm" variant="outline">
                  <Star className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* No Results */}
      {filteredContent.length === 0 && (
        <div className="text-center py-12">
          <BookOpen className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">No content found</h3>
          <p className="text-muted-foreground mb-4">
            Try adjusting your search criteria or filters.
          </p>
          <Button
            onClick={() => {
              setSearchQuery("")
              setSelectedCategory("all")
              setSelectedDifficulty("all")
              setSelectedTags([])
              setShowFavoritesOnly(false)
              setShowBookmarksOnly(false)
            }}
          >
            Clear all filters
          </Button>
        </div>
      )}
    </div>
  )
}