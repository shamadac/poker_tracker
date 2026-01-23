/**
 * Term Definition Modal Component
 * 
 * Displays detailed term definitions in a modal dialog with related terms
 * and navigation to full encyclopedia/education content.
 */

import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from './dialog';
import { Button } from './button';
import { Badge } from './badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './card';
import { Separator } from './separator';
import { ScrollArea } from './scroll-area';
import {
  BookOpen,
  GraduationCap,
  ExternalLink,
  ArrowRight,
  X,
  Lightbulb,
} from 'lucide-react';
import { TermDefinition } from '@/hooks/use-term-linking';

interface TermDefinitionModalProps {
  isOpen: boolean;
  term: string;
  definition?: TermDefinition;
  relatedTerms: TermDefinition[];
  onClose: () => void;
  onTermClick?: (term: string) => void;
  onViewSource?: (sourceType: string, sourceId: string) => void;
}

export function TermDefinitionModal({
  isOpen,
  term,
  definition,
  relatedTerms,
  onClose,
  onTermClick,
  onViewSource,
}: TermDefinitionModalProps) {
  const getSourceIcon = (sourceType: string) => {
    switch (sourceType) {
      case 'encyclopedia':
        return <BookOpen className="h-4 w-4" />;
      case 'education':
        return <GraduationCap className="h-4 w-4" />;
      default:
        return <BookOpen className="h-4 w-4" />;
    }
  };

  const getDifficultyColor = (difficulty?: string) => {
    switch (difficulty) {
      case 'beginner':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'intermediate':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'advanced':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const handleViewSource = () => {
    if (definition && onViewSource) {
      onViewSource(definition.source_type, definition.source_id);
    }
  };

  const handleRelatedTermClick = (relatedTerm: string) => {
    if (onTermClick) {
      onTermClick(relatedTerm);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden">
        <DialogHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <DialogTitle className="text-2xl font-bold text-gray-900">
                {term}
              </DialogTitle>
              {definition && (
                <div className="flex items-center gap-2 mt-2">
                  <Badge
                    variant="outline"
                    className="flex items-center gap-1"
                  >
                    {getSourceIcon(definition.source_type)}
                    {definition.source_type === 'encyclopedia' ? 'Encyclopedia' : 'Education'}
                  </Badge>
                  {definition.difficulty_level && (
                    <Badge
                      className={getDifficultyColor(definition.difficulty_level)}
                    >
                      {definition.difficulty_level}
                    </Badge>
                  )}
                  {definition.category && (
                    <Badge variant="secondary">
                      {definition.category.replace('_', ' ')}
                    </Badge>
                  )}
                </div>
              )}
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-8 w-8 p-0"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </DialogHeader>

        <ScrollArea className="flex-1 pr-4">
          <div className="space-y-6">
            {definition ? (
              <>
                {/* Main Definition */}
                <div className="space-y-3">
                  <h3 className="text-lg font-semibold">Definition</h3>
                  <p className="text-gray-700 leading-relaxed">
                    {definition.definition}
                  </p>
                </div>

                {/* Detailed Explanation */}
                {definition.explanation && definition.explanation !== definition.definition && (
                  <>
                    <Separator />
                    <div className="space-y-3">
                      <h3 className="text-lg font-semibold">Detailed Explanation</h3>
                      <div className="prose prose-sm max-w-none">
                        <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                          {definition.explanation}
                        </p>
                      </div>
                    </div>
                  </>
                )}

                {/* Related Terms */}
                {relatedTerms.length > 0 && (
                  <>
                    <Separator />
                    <div className="space-y-3">
                      <div className="flex items-center gap-2">
                        <Lightbulb className="h-5 w-5 text-yellow-500" />
                        <h3 className="text-lg font-semibold">Related Terms</h3>
                      </div>
                      <div className="grid gap-3">
                        {relatedTerms.map((relatedTerm, index) => (
                          <Card
                            key={index}
                            className="cursor-pointer hover:shadow-md transition-shadow"
                            onClick={() => handleRelatedTermClick(relatedTerm.term)}
                          >
                            <CardHeader className="pb-2">
                              <div className="flex items-center justify-between">
                                <CardTitle className="text-base">
                                  {relatedTerm.term}
                                </CardTitle>
                                <ArrowRight className="h-4 w-4 text-muted-foreground" />
                              </div>
                            </CardHeader>
                            <CardContent className="pt-0">
                              <CardDescription className="text-sm line-clamp-2">
                                {relatedTerm.definition}
                              </CardDescription>
                              <div className="flex items-center gap-2 mt-2">
                                <Badge variant="outline" className="text-xs">
                                  {getSourceIcon(relatedTerm.source_type)}
                                  {relatedTerm.source_type}
                                </Badge>
                                {relatedTerm.difficulty_level && (
                                  <Badge
                                    className={`text-xs ${getDifficultyColor(relatedTerm.difficulty_level)}`}
                                  >
                                    {relatedTerm.difficulty_level}
                                  </Badge>
                                )}
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </div>
                  </>
                )}

                {/* Action Buttons */}
                <Separator />
                <div className="flex justify-between items-center">
                  <DialogDescription className="text-sm">
                    Learn more about this concept in our {definition.source_type === 'encyclopedia' ? 'encyclopedia' : 'education'} section.
                  </DialogDescription>
                  <div className="flex gap-2">
                    <Button variant="outline" onClick={onClose}>
                      Close
                    </Button>
                    {onViewSource && (
                      <Button onClick={handleViewSource}>
                        <ExternalLink className="h-4 w-4 mr-2" />
                        View Full Article
                      </Button>
                    )}
                  </div>
                </div>
              </>
            ) : (
              /* Loading State */
              <div className="flex flex-col items-center justify-center py-12 space-y-4">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                <p className="text-muted-foreground">Loading definition...</p>
              </div>
            )}
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}

/**
 * Simplified term definition sidebar component
 */
interface TermDefinitionSidebarProps {
  isOpen: boolean;
  term: string;
  definition?: TermDefinition;
  onClose: () => void;
  onViewSource?: (sourceType: string, sourceId: string) => void;
}

export function TermDefinitionSidebar({
  isOpen,
  term,
  definition,
  onClose,
  onViewSource,
}: TermDefinitionSidebarProps) {
  if (!isOpen) {
    return null;
  }

  const handleViewSource = () => {
    if (definition && onViewSource) {
      onViewSource(definition.source_type, definition.source_id);
    }
  };

  return (
    <div className="fixed right-0 top-0 h-full w-80 bg-white shadow-xl border-l z-40 transform transition-transform">
      <div className="flex flex-col h-full">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">Term Definition</h2>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
        
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-4">
            <div>
              <h3 className="text-xl font-bold">{term}</h3>
              {definition && (
                <div className="flex items-center gap-2 mt-2">
                  <Badge variant="outline" className="text-xs">
                    {definition.source_type === 'encyclopedia' ? (
                      <BookOpen className="h-3 w-3 mr-1" />
                    ) : (
                      <GraduationCap className="h-3 w-3 mr-1" />
                    )}
                    {definition.source_type}
                  </Badge>
                  {definition.difficulty_level && (
                    <Badge variant="secondary" className="text-xs">
                      {definition.difficulty_level}
                    </Badge>
                  )}
                </div>
              )}
            </div>
            
            {definition ? (
              <div className="space-y-4">
                <div>
                  <h4 className="font-semibold mb-2">Definition</h4>
                  <p className="text-sm text-gray-700 leading-relaxed">
                    {definition.definition}
                  </p>
                </div>
                
                {definition.explanation && definition.explanation !== definition.definition && (
                  <div>
                    <h4 className="font-semibold mb-2">Explanation</h4>
                    <p className="text-sm text-gray-700 leading-relaxed">
                      {definition.explanation.substring(0, 300)}
                      {definition.explanation.length > 300 && '...'}
                    </p>
                  </div>
                )}
                
                {onViewSource && (
                  <Button onClick={handleViewSource} className="w-full">
                    <ExternalLink className="h-4 w-4 mr-2" />
                    View Full Article
                  </Button>
                )}
              </div>
            ) : (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
              </div>
            )}
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}