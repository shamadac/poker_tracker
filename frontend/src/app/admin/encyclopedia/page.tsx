'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/hooks/use-toast';
import { Loader2, Plus, Edit, Check, X, Search, Lightbulb, Link } from 'lucide-react';

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
  conversations?: EncyclopediaConversation[];
}

interface EncyclopediaConversation {
  id: string;
  prompt: string;
  response: string;
  ai_provider: string;
  created_at: string;
}

interface TopicSuggestion {
  title: string;
  description: string;
}

export default function EncyclopediaAdminPage() {
  const [entries, setEntries] = useState<EncyclopediaEntry[]>([]);
  const [selectedEntry, setSelectedEntry] = useState<EncyclopediaEntry | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('entries');
  const { toast } = useToast();

  // Form states
  const [newEntryForm, setNewEntryForm] = useState({
    title: '',
    initial_prompt: '',
    ai_provider: 'groq'
  });
  const [refinementPrompt, setRefinementPrompt] = useState('');
  const [refinementProvider, setRefinementProvider] = useState('groq');
  const [searchQuery, setSearchQuery] = useState('');
  const [topicSuggestions, setTopicSuggestions] = useState<TopicSuggestion[]>([]);

  useEffect(() => {
    loadEntries();
  }, []);

  const loadEntries = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('/api/v1/encyclopedia/entries');
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

  const createEntry = async () => {
    if (!newEntryForm.title || !newEntryForm.initial_prompt) {
      toast({
        title: 'Error',
        description: 'Please fill in all required fields',
        variant: 'destructive'
      });
      return;
    }

    try {
      setIsLoading(true);
      const response = await fetch('/api/v1/encyclopedia/entries', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newEntryForm)
      });

      if (response.ok) {
        const newEntry = await response.json();
        setEntries([newEntry, ...entries]);
        setNewEntryForm({ title: '', initial_prompt: '', ai_provider: 'groq' });
        toast({
          title: 'Success',
          description: 'Encyclopedia entry created successfully'
        });
      } else {
        const error = await response.json();
        toast({
          title: 'Error',
          description: error.detail || 'Failed to create encyclopedia entry',
          variant: 'destructive'
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to create encyclopedia entry',
        variant: 'destructive'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const refineEntry = async (entryId: string) => {
    if (!refinementPrompt) {
      toast({
        title: 'Error',
        description: 'Please enter a refinement prompt',
        variant: 'destructive'
      });
      return;
    }

    try {
      setIsLoading(true);
      const response = await fetch(`/api/v1/encyclopedia/entries/${entryId}/refine`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          refinement_prompt: refinementPrompt,
          ai_provider: refinementProvider
        })
      });

      if (response.ok) {
        const updatedEntry = await response.json();
        setEntries(entries.map(e => e.id === entryId ? updatedEntry : e));
        setSelectedEntry(updatedEntry);
        setRefinementPrompt('');
        toast({
          title: 'Success',
          description: 'Encyclopedia entry refined successfully'
        });
      } else {
        const error = await response.json();
        toast({
          title: 'Error',
          description: error.detail || 'Failed to refine encyclopedia entry',
          variant: 'destructive'
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to refine encyclopedia entry',
        variant: 'destructive'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const approveEntry = async (entryId: string) => {
    try {
      setIsLoading(true);
      const response = await fetch(`/api/v1/encyclopedia/entries/${entryId}/approve`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
      });

      if (response.ok) {
        const updatedEntry = await response.json();
        setEntries(entries.map(e => e.id === entryId ? updatedEntry : e));
        setSelectedEntry(updatedEntry);
        toast({
          title: 'Success',
          description: 'Encyclopedia entry approved and published'
        });
      } else {
        const error = await response.json();
        toast({
          title: 'Error',
          description: error.detail || 'Failed to approve encyclopedia entry',
          variant: 'destructive'
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to approve encyclopedia entry',
        variant: 'destructive'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const generateTopicSuggestions = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('/api/v1/encyclopedia/suggestions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ai_provider: 'groq',
          limit: 10
        })
      });

      if (response.ok) {
        const suggestions = await response.json();
        setTopicSuggestions(suggestions);
        toast({
          title: 'Success',
          description: `Generated ${suggestions.length} topic suggestions`
        });
      } else {
        const error = await response.json();
        toast({
          title: 'Error',
          description: error.detail || 'Failed to generate topic suggestions',
          variant: 'destructive'
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to generate topic suggestions',
        variant: 'destructive'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const generateLinks = async (entryId: string) => {
    // DEPRECATED: Manual link generation replaced by automatic term linking
    toast({
      title: 'Info',
      description: 'Manual link generation is deprecated. Links are now created automatically throughout the interface.',
      variant: 'default'
    });
  };

  const getStatusBadge = (status: string) => {
    const variants = {
      draft: 'secondary',
      published: 'default',
      archived: 'outline'
    } as const;
    
    return (
      <Badge variant={variants[status as keyof typeof variants] || 'secondary'}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  const filteredEntries = entries.filter(entry =>
    entry.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    entry.content.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Encyclopedia Management</h1>
          <p className="text-muted-foreground">
            Create and manage AI-powered poker encyclopedia entries
          </p>
        </div>
        <Button onClick={loadEntries} disabled={isLoading}>
          {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Refresh'}
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="entries">Entries</TabsTrigger>
          <TabsTrigger value="create">Create New</TabsTrigger>
          <TabsTrigger value="suggestions">Topic Suggestions</TabsTrigger>
        </TabsList>

        <TabsContent value="entries" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Encyclopedia Entries</CardTitle>
              <CardDescription>
                Manage existing encyclopedia entries. Inter-entry links are now created automatically throughout the interface.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center space-x-2">
                <Search className="h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search entries..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="max-w-sm"
                />
              </div>

              <div className="grid gap-4">
                {filteredEntries.map((entry) => (
                  <Card key={entry.id} className="cursor-pointer hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <h3 className="font-semibold">{entry.title}</h3>
                            {getStatusBadge(entry.status)}
                            <Badge variant="outline">{entry.ai_provider}</Badge>
                          </div>
                          <p className="text-sm text-muted-foreground mb-2">
                            {entry.content.substring(0, 200)}...
                          </p>
                          <p className="text-xs text-muted-foreground">
                            Created: {new Date(entry.created_at).toLocaleDateString()}
                          </p>
                        </div>
                        <div className="flex space-x-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setSelectedEntry(entry)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          {entry.status === 'draft' && (
                            <Button
                              size="sm"
                              onClick={() => approveEntry(entry.id)}
                              disabled={isLoading}
                            >
                              <Check className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>

          {selectedEntry && (
            <Card>
              <CardHeader>
                <CardTitle>Edit Entry: {selectedEntry.title}</CardTitle>
                <CardDescription>
                  Refine content using AI conversation
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="content">Current Content</Label>
                  <Textarea
                    id="content"
                    value={selectedEntry.content}
                    readOnly
                    className="min-h-[200px]"
                  />
                </div>

                <Separator />

                <div className="space-y-4">
                  <div>
                    <Label htmlFor="refinement">Refinement Prompt</Label>
                    <Textarea
                      id="refinement"
                      placeholder="Describe how you want to refine this content..."
                      value={refinementPrompt}
                      onChange={(e) => setRefinementPrompt(e.target.value)}
                    />
                  </div>

                  <div>
                    <Label htmlFor="provider">AI Provider</Label>
                    <Select value={refinementProvider} onValueChange={setRefinementProvider}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="groq">Groq</SelectItem>
                        <SelectItem value="gemini">Gemini</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex space-x-2">
                    <Button
                      onClick={() => refineEntry(selectedEntry.id)}
                      disabled={isLoading || !refinementPrompt}
                    >
                      {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Refine Content'}
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => setSelectedEntry(null)}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>

                {selectedEntry.conversations && selectedEntry.conversations.length > 0 && (
                  <div>
                    <h4 className="font-semibold mb-2">Conversation History</h4>
                    <div className="space-y-2 max-h-60 overflow-y-auto">
                      {selectedEntry.conversations.map((conv) => (
                        <div key={conv.id} className="border rounded p-2 text-sm">
                          <p><strong>Prompt:</strong> {conv.prompt}</p>
                          <p><strong>Response:</strong> {conv.response.substring(0, 100)}...</p>
                          <p className="text-xs text-muted-foreground">
                            {conv.ai_provider} - {new Date(conv.created_at).toLocaleString()}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="create" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Create New Encyclopedia Entry</CardTitle>
              <CardDescription>
                Generate new content using AI
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="title">Title</Label>
                <Input
                  id="title"
                  placeholder="Enter encyclopedia entry title..."
                  value={newEntryForm.title}
                  onChange={(e) => setNewEntryForm({ ...newEntryForm, title: e.target.value })}
                />
              </div>

              <div>
                <Label htmlFor="prompt">Initial Prompt</Label>
                <Textarea
                  id="prompt"
                  placeholder="Describe what content you want to generate..."
                  value={newEntryForm.initial_prompt}
                  onChange={(e) => setNewEntryForm({ ...newEntryForm, initial_prompt: e.target.value })}
                />
              </div>

              <div>
                <Label htmlFor="ai-provider">AI Provider</Label>
                <Select
                  value={newEntryForm.ai_provider}
                  onValueChange={(value) => setNewEntryForm({ ...newEntryForm, ai_provider: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="groq">Groq</SelectItem>
                    <SelectItem value="gemini">Gemini</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Button onClick={createEntry} disabled={isLoading}>
                {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
                Create Entry
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="suggestions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Topic Suggestions</CardTitle>
              <CardDescription>
                AI-generated suggestions for new encyclopedia topics
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button onClick={generateTopicSuggestions} disabled={isLoading}>
                {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Lightbulb className="h-4 w-4" />}
                Generate Suggestions
              </Button>

              {topicSuggestions.length > 0 && (
                <div className="grid gap-4">
                  {topicSuggestions.map((suggestion, index) => (
                    <Card key={index}>
                      <CardContent className="p-4">
                        <h4 className="font-semibold mb-2">{suggestion.title}</h4>
                        <p className="text-sm text-muted-foreground mb-2">
                          {suggestion.description}
                        </p>
                        <Button
                          size="sm"
                          onClick={() => {
                            setNewEntryForm({
                              title: suggestion.title,
                              initial_prompt: `Create a comprehensive encyclopedia entry about ${suggestion.title}. ${suggestion.description}`,
                              ai_provider: 'groq'
                            });
                            setActiveTab('create');
                          }}
                        >
                          Use This Topic
                        </Button>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}