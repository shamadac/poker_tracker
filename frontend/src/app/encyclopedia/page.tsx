'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { TermLinkedContent } from '@/components/ui/term-linked-content';
import { useToast } from '@/hooks/use-toast';
import { Search, BookOpen, ExternalLink, Clock, User } from 'lucide-react';

interface EncyclopediaEntry {
  id: string;
  title: string;
  content: string;
  status: 'draft' | 'published' | 'archived';
  ai_provider: string;
  created_by: string;
  approved_by?: string;
  published_at?: string;
  created_at: string;
  updated_at: string;
}

interface SearchResult {
  entries: EncyclopediaEntry[];
  total_count: number;
  query: string;
}

export default function EncyclopediaPage() {
  const [entries, setEntries] = useState<EncyclopediaEntry[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    loadPublishedEntries();
  }, []);

  const loadPublishedEntries = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('/api/v1/encyclopedia/entries?status_filter=published');
      if (response.ok) {
        const data = await response.json();
        setEntries(data);
      } else {
        toast({
          title: 'Error',
          description: 'Failed to load encyclopedia entries',
          variant: 'destructive'
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load encyclopedia entries',
        variant: 'destructive'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const searchEntries = async () => {
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }

    try {
      setIsSearching(true);
      const response = await fetch('/api/v1/encyclopedia/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          query: searchQuery,
          status_filter: 'published',
          limit: 20
        })
      });

      if (response.ok) {
        const results = await response.json();
        setSearchResults(results);
      } else {
        toast({
          title: 'Error',
          description: 'Failed to search encyclopedia',
          variant: 'destructive'
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to search encyclopedia',
        variant: 'destructive'
      });
    } finally {
      setIsSearching(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    searchEntries();
  };

  const clearSearch = () => {
    setSearchQuery('');
    setSearchResults(null);
  };

  const displayEntries = searchResults ? searchResults.entries : entries;

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const truncateContent = (content: string, maxLength: number = 300) => {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength).trim() + '...';
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="text-center space-y-4">
        <div className="flex justify-center">
          <BookOpen className="h-12 w-12 text-primary" />
        </div>
        <h1 className="text-4xl font-bold">Poker Encyclopedia</h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Comprehensive poker knowledge powered by AI. Learn concepts, strategies, and terminology 
          to improve your game.
        </p>
      </div>

      <Card>
        <CardContent className="p-6">
          <form onSubmit={handleSearchSubmit} className="flex space-x-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search poker concepts, strategies, terms..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Button type="submit" disabled={isSearching}>
              {isSearching ? 'Searching...' : 'Search'}
            </Button>
            {searchResults && (
              <Button type="button" variant="outline" onClick={clearSearch}>
                Clear
              </Button>
            )}
          </form>
        </CardContent>
      </Card>

      {searchResults && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Found {searchResults.total_count} result{searchResults.total_count !== 1 ? 's' : ''} for "{searchResults.query}"
          </p>
        </div>
      )}

      {isLoading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading encyclopedia entries...</p>
        </div>
      ) : displayEntries.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12">
            <BookOpen className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">
              {searchResults ? 'No results found' : 'No entries available'}
            </h3>
            <p className="text-muted-foreground">
              {searchResults 
                ? 'Try adjusting your search terms or browse all entries.'
                : 'Encyclopedia entries will appear here once they are published.'
              }
            </p>
            {searchResults && (
              <Button onClick={clearSearch} className="mt-4">
                Browse All Entries
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6">
          {displayEntries.map((entry) => (
            <Card key={entry.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <CardTitle className="text-xl mb-2">
                      <Link 
                        href={`/encyclopedia/${entry.id}`}
                        className="hover:text-primary transition-colors"
                      >
                        {entry.title}
                      </Link>
                    </CardTitle>
                    <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                      <Clock className="h-4 w-4" />
                      <span>Published {formatDate(entry.published_at || entry.created_at)}</span>
                      <Separator orientation="vertical" className="h-4" />
                      <Badge variant="outline" className="text-xs">
                        {entry.ai_provider.toUpperCase()}
                      </Badge>
                    </div>
                  </div>
                  <Link href={`/encyclopedia/${entry.id}`}>
                    <Button variant="ghost" size="sm">
                      <ExternalLink className="h-4 w-4" />
                    </Button>
                  </Link>
                </div>
              </CardHeader>
              <CardContent>
                <div className="prose prose-sm max-w-none">
                  <TermLinkedContent 
                    content={truncateContent(entry.content)}
                    context="encyclopedia"
                    maxLinks={3}
                    className="text-muted-foreground leading-relaxed"
                  />
                </div>
                <div className="mt-4 pt-4 border-t">
                  <Link href={`/encyclopedia/${entry.id}`}>
                    <Button variant="outline" size="sm">
                      Read Full Entry
                      <ExternalLink className="h-4 w-4 ml-2" />
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {!searchResults && entries.length > 0 && (
        <Card>
          <CardContent className="text-center py-8">
            <h3 className="text-lg font-semibold mb-2">Explore More</h3>
            <p className="text-muted-foreground mb-4">
              Use the search above to find specific poker concepts, or browse through all available entries.
            </p>
            <div className="flex justify-center space-x-2">
              <Badge variant="secondary">Strategy</Badge>
              <Badge variant="secondary">Statistics</Badge>
              <Badge variant="secondary">Terminology</Badge>
              <Badge variant="secondary">Psychology</Badge>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}