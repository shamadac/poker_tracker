/**
 * Term Linking Demo Component
 * 
 * Demonstrates the educational term linking functionality with examples
 * of poker content that includes linked terms.
 */

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { TermLinkedContent, SimpleTermLinkedContent } from '@/components/ui/term-linked-content';
import { TermLinkingProvider, TermLinkingSettings } from '@/contexts/term-linking-context';
import { Settings, BookOpen, Zap, Eye } from 'lucide-react';

const sampleContent = {
  analysis: `Your VPIP of 28% is slightly loose for a 6-max game. Consider tightening your preflop range, especially from early position. Your PFR of 22% shows good aggression, but the gap between VPIP and PFR suggests you're limping too often. Focus on raising or folding rather than limping. Your c-bet frequency on dry boards should be higher to maximize fold equity.`,
  
  dashboard: `Today's session shows strong performance with a win rate of 15bb/100 over 250 hands. Your VPIP was well-controlled at 22%, and your PFR of 18% indicates solid preflop aggression. Position awareness was excellent with tighter ranges from early position.`,
  
  education: `Understanding position is crucial for poker success. Players in late position have more information and can play wider ranges. The button is the most profitable position, followed by the cutoff. Early position requires tighter hand selection due to the positional disadvantage.`,
  
  strategy: `When facing a 3-bet, consider your opponent's range and position. Against tight players, fold marginal hands and 4-bet for value with premium holdings. Bluffing frequency should increase against opponents with high fold-to-4-bet percentages. Stack depth affects your decision - deeper stacks favor more speculative hands.`
};

export function TermLinkingDemo() {
  const [selectedContent, setSelectedContent] = useState<keyof typeof sampleContent>('analysis');
  const [showSettings, setShowSettings] = useState(false);

  return (
    <TermLinkingProvider>
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <BookOpen className="h-5 w-5" />
                  Educational Term Linking Demo
                </CardTitle>
                <CardDescription>
                  Interactive demonstration of automatic poker term detection and linking
                </CardDescription>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowSettings(!showSettings)}
              >
                <Settings className="h-4 w-4 mr-2" />
                Settings
              </Button>
            </div>
          </CardHeader>
          
          {showSettings && (
            <CardContent className="border-t">
              <div className="py-4">
                <h4 className="font-semibold mb-3">Term Linking Configuration</h4>
                <TermLinkingSettings />
              </div>
            </CardContent>
          )}
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          {/* Content Selection */}
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle className="text-lg">Content Examples</CardTitle>
              <CardDescription className="text-sm">
                Choose different contexts to see how term linking adapts
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {Object.keys(sampleContent).map((key) => (
                <Button
                  key={key}
                  variant={selectedContent === key ? 'default' : 'outline'}
                  size="sm"
                  className="w-full justify-start"
                  onClick={() => setSelectedContent(key as keyof typeof sampleContent)}
                >
                  <div className="flex items-center gap-2">
                    {key === 'analysis' && <Zap className="h-4 w-4" />}
                    {key === 'dashboard' && <Eye className="h-4 w-4" />}
                    {key === 'education' && <BookOpen className="h-4 w-4" />}
                    {key === 'strategy' && <Settings className="h-4 w-4" />}
                    {key.charAt(0).toUpperCase() + key.slice(1)}
                  </div>
                </Button>
              ))}
            </CardContent>
          </Card>

          {/* Content Display */}
          <Card className="lg:col-span-3">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">
                  {selectedContent.charAt(0).toUpperCase() + selectedContent.slice(1)} Content
                </CardTitle>
                <Badge variant="outline">
                  Context: {selectedContent}
                </Badge>
              </div>
              <CardDescription>
                Hover over highlighted terms for definitions, click for detailed information
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="full" className="w-full">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="full">Full Features</TabsTrigger>
                  <TabsTrigger value="simple">Simple Links</TabsTrigger>
                  <TabsTrigger value="original">Original Text</TabsTrigger>
                </TabsList>
                
                <TabsContent value="full" className="space-y-4">
                  <div className="p-4 bg-muted/30 rounded-lg">
                    <TermLinkedContent
                      content={sampleContent[selectedContent]}
                      context={selectedContent}
                      maxLinks={8}
                      enableHover={true}
                      enableModal={true}
                      className="leading-relaxed"
                    />
                  </div>
                  <div className="text-sm text-muted-foreground">
                    <strong>Features:</strong> Hover previews, click for modals, context-aware term selection
                  </div>
                </TabsContent>
                
                <TabsContent value="simple" className="space-y-4">
                  <div className="p-4 bg-muted/30 rounded-lg">
                    <SimpleTermLinkedContent
                      content={sampleContent[selectedContent]}
                      context={selectedContent}
                      maxLinks={5}
                      className="leading-relaxed"
                      onTermClick={(term) => alert(`Clicked term: ${term}`)}
                    />
                  </div>
                  <div className="text-sm text-muted-foreground">
                    <strong>Features:</strong> Basic term linking with custom click handlers
                  </div>
                </TabsContent>
                
                <TabsContent value="original" className="space-y-4">
                  <div className="p-4 bg-muted/30 rounded-lg">
                    <p className="leading-relaxed">
                      {sampleContent[selectedContent]}
                    </p>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    <strong>Original:</strong> Plain text without term linking
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>

        {/* Feature Overview */}
        <Card>
          <CardHeader>
            <CardTitle>Term Linking Features</CardTitle>
            <CardDescription>
              Comprehensive educational integration for poker terminology
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="space-y-2">
                <h4 className="font-semibold text-sm">Automatic Detection</h4>
                <p className="text-xs text-muted-foreground">
                  Automatically identifies poker terms in any content using regex patterns and context awareness
                </p>
              </div>
              <div className="space-y-2">
                <h4 className="font-semibold text-sm">Hover Previews</h4>
                <p className="text-xs text-muted-foreground">
                  Quick definition previews on hover with source information and difficulty indicators
                </p>
              </div>
              <div className="space-y-2">
                <h4 className="font-semibold text-sm">Detailed Modals</h4>
                <p className="text-xs text-muted-foreground">
                  Full definition modals with explanations, related terms, and links to source content
                </p>
              </div>
              <div className="space-y-2">
                <h4 className="font-semibold text-sm">Context Awareness</h4>
                <p className="text-xs text-muted-foreground">
                  Adapts term selection based on context (dashboard, analysis, education) for relevance
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Implementation Notes */}
        <Card>
          <CardHeader>
            <CardTitle>Implementation Notes</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <h4 className="font-semibold mb-2">Backend Integration</h4>
                <ul className="space-y-1 text-muted-foreground">
                  <li>• Term detection service with caching</li>
                  <li>• Encyclopedia and education content integration</li>
                  <li>• Context-aware term filtering</li>
                  <li>• RESTful API endpoints for term operations</li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold mb-2">Frontend Components</h4>
                <ul className="space-y-1 text-muted-foreground">
                  <li>• React hooks for term linking functionality</li>
                  <li>• Hover preview and modal components</li>
                  <li>• Context provider for global configuration</li>
                  <li>• Graceful degradation to tooltips</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </TermLinkingProvider>
  );
}