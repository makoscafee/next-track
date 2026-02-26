import React, { useState, useEffect, useCallback } from 'react';
import { Music2, RefreshCw, AlertCircle } from 'lucide-react';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/ui/tabs';
import { Skeleton } from '../components/ui/skeleton';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  adminLogin,
  isLoggedIn,
  getAdminStats,
  getAdminHealth,
  getAdminFeedback,
  getExperimentDetail,
  listExperiments,
} from '../../services/adminApi';
import type {
  AdminStats,
  AdminHealth,
  AdminFeedbackLog,
  AdminExperimentDetail,
} from '../../services/types';

// ── Helpers ──────────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  const s = status.toLowerCase();
  const variant =
    s === 'healthy' || s === 'running' || s === 'loaded'
      ? 'default'
      : s === 'degraded'
      ? 'secondary'
      : 'destructive';
  const cls =
    s === 'healthy' || s === 'running'
      ? 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300'
      : s === 'degraded'
      ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300'
      : s === 'draft' || s === 'paused' || s === 'completed'
      ? 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
      : 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300';
  return (
    <Badge variant={variant} className={`capitalize ${cls}`}>
      {status}
    </Badge>
  );
}

function ErrorBanner({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex items-center gap-3 p-4 rounded-md bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300">
      <AlertCircle className="w-5 h-5 flex-shrink-0" />
      <span className="text-sm flex-1">{message}</span>
      {onRetry && (
        <Button size="sm" variant="outline" onClick={onRetry} className="text-red-700 border-red-300">
          Retry
        </Button>
      )}
    </div>
  );
}

// ── Login Form ────────────────────────────────────────────────────────────────

interface LoginFormProps {
  onSuccess: () => void;
}

function LoginForm({ onSuccess }: LoginFormProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await adminLogin(username, password);
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <Card className="w-full max-w-sm p-8">
        <div className="flex items-center gap-2 justify-center mb-6">
          <Music2 className="w-7 h-7 text-primary" />
          <span className="text-xl font-bold">NextTrack</span>
        </div>
        <div className="text-center mb-6">
          <h1 className="text-xl font-semibold mb-1">Admin Dashboard</h1>
          <p className="text-sm text-muted-foreground">Sign in to access the admin panel</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="username">Username</Label>
            <Input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="admin"
              required
              autoFocus
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>
          {error && (
            <p className="text-sm text-red-500">{error}</p>
          )}
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? 'Signing in…' : 'Sign In'}
          </Button>
        </form>
      </Card>
    </div>
  );
}

// ── Overview Tab ─────────────────────────────────────────────────────────────

function OverviewTab() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setStats(await getAdminStats());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load stats');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) return (
    <div className="space-y-4">
      <div className="grid md:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => <Skeleton key={i} className="h-36 rounded-lg" />)}
      </div>
      <Skeleton className="h-48 rounded-lg" />
    </div>
  );

  if (error) return <ErrorBanner message={error} onRetry={load} />;
  if (!stats) return null;

  const { content_based, collaborative } = stats.models;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <p className="text-xs text-muted-foreground">Last updated: {new Date(stats.generated_at).toLocaleString()}</p>
        <Button size="sm" variant="outline" onClick={load}>
          <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
          Refresh
        </Button>
      </div>

      {/* Model Cards */}
      <div className="grid md:grid-cols-3 gap-4">
        <Card className="p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-sm">Content Model</h3>
            <StatusBadge status={content_based.loaded ? 'healthy' : 'unhealthy'} />
          </div>
          <div className="space-y-1.5 text-sm text-muted-foreground">
            {content_based.n_tracks != null && (
              <div className="flex justify-between">
                <span>Tracks</span>
                <span className="font-medium text-foreground">{content_based.n_tracks.toLocaleString()}</span>
              </div>
            )}
            {content_based.version && (
              <div className="flex justify-between">
                <span>Version</span>
                <span className="font-mono text-xs text-foreground">{content_based.version}</span>
              </div>
            )}
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-sm">Collab. Filter Model</h3>
            <StatusBadge status={collaborative.loaded ? 'healthy' : 'unhealthy'} />
          </div>
          <div className="space-y-1.5 text-sm text-muted-foreground">
            {collaborative.n_users != null && (
              <div className="flex justify-between">
                <span>Users</span>
                <span className="font-medium text-foreground">{collaborative.n_users.toLocaleString()}</span>
              </div>
            )}
            {collaborative.n_tracks != null && (
              <div className="flex justify-between">
                <span>Tracks</span>
                <span className="font-medium text-foreground">{collaborative.n_tracks.toLocaleString()}</span>
              </div>
            )}
            {collaborative.version && (
              <div className="flex justify-between">
                <span>Version</span>
                <span className="font-mono text-xs text-foreground">{collaborative.version}</span>
              </div>
            )}
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-sm">Feedback</h3>
            <span className="text-2xl font-bold">{stats.feedback.total}</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {Object.entries(stats.feedback.by_type).map(([type, count]) => (
              <Badge key={type} variant="secondary" className="text-xs capitalize">
                {type}: {count}
              </Badge>
            ))}
            {Object.keys(stats.feedback.by_type).length === 0 && (
              <span className="text-xs text-muted-foreground">No feedback recorded yet</span>
            )}
          </div>
        </Card>
      </div>

      {/* Experiments Table */}
      <Card className="p-5">
        <h3 className="font-semibold mb-4">A/B Experiments</h3>
        {stats.experiments.length === 0 ? (
          <p className="text-sm text-muted-foreground">No experiments found.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Variants</TableHead>
                <TableHead className="text-right">Observations</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {stats.experiments.map((exp) => (
                <TableRow key={exp.name}>
                  <TableCell className="font-mono text-sm">{exp.name}</TableCell>
                  <TableCell><StatusBadge status={exp.status} /></TableCell>
                  <TableCell className="text-right">{exp.variants}</TableCell>
                  <TableCell className="text-right">{exp.total_observations}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>
    </div>
  );
}

// ── Health Tab ────────────────────────────────────────────────────────────────

function HealthTab() {
  const [health, setHealth] = useState<AdminHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setHealth(await getAdminHealth());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load health');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) return (
    <div className="space-y-4">
      <Skeleton className="h-12 rounded-lg" />
      <div className="grid md:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => <Skeleton key={i} className="h-40 rounded-lg" />)}
      </div>
    </div>
  );

  if (error) return <ErrorBanner message={error} onRetry={load} />;
  if (!health) return null;

  const components = [
    { key: 'content_based_model', label: 'Content Model', data: health.components.content_based_model },
    { key: 'collaborative_model', label: 'Collab. Filter Model', data: health.components.collaborative_model },
    { key: 'ab_testing', label: 'A/B Testing', data: health.components.ab_testing },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium">Overall Status</span>
          <StatusBadge status={health.status} />
        </div>
        <div className="flex items-center gap-3">
          <p className="text-xs text-muted-foreground">Checked: {new Date(health.checked_at).toLocaleString()}</p>
          <Button size="sm" variant="outline" onClick={load}>
            <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
            Refresh
          </Button>
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-4">
        {components.map(({ key, label, data }) => (
          <Card key={key} className="p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-sm">{label}</h3>
              <StatusBadge status={data.status} />
            </div>
            <div className="space-y-1.5 text-sm text-muted-foreground">
              {data.loaded !== undefined && (
                <div className="flex justify-between">
                  <span>Loaded</span>
                  <span className={`font-medium ${data.loaded ? 'text-green-600' : 'text-red-500'}`}>
                    {data.loaded ? 'Yes' : 'No'}
                  </span>
                </div>
              )}
              {data.experiments_count !== undefined && (
                <div className="flex justify-between">
                  <span>Experiments</span>
                  <span className="font-medium text-foreground">{data.experiments_count}</span>
                </div>
              )}
              {data.info && Object.entries(data.info).slice(0, 4).map(([k, v]) => (
                typeof v !== 'object' && (
                  <div key={k} className="flex justify-between">
                    <span className="capitalize">{k.replace(/_/g, ' ')}</span>
                    <span className="font-medium text-foreground truncate max-w-28 text-right">
                      {String(v)}
                    </span>
                  </div>
                )
              ))}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

// ── Feedback Tab ──────────────────────────────────────────────────────────────

const FEEDBACK_TYPES = ['click', 'play', 'skip', 'save', 'listen_time'];

function FeedbackTab() {
  const [log, setLog] = useState<AdminFeedbackLog | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [limit, setLimit] = useState('50');
  const [feedbackType, setFeedbackType] = useState('all');

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const type = feedbackType === 'all' ? undefined : feedbackType;
      setLog(await getAdminFeedback(Number(limit) || 50, type));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load feedback');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Filter bar */}
      <Card className="p-4">
        <div className="flex flex-wrap items-end gap-4">
          <div className="space-y-1.5">
            <Label>Type</Label>
            <Select value={feedbackType} onValueChange={setFeedbackType}>
              <SelectTrigger className="w-36">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All types</SelectItem>
                {FEEDBACK_TYPES.map((t) => (
                  <SelectItem key={t} value={t} className="capitalize">{t}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>Limit</Label>
            <Input
              type="number"
              value={limit}
              onChange={(e) => setLimit(e.target.value)}
              className="w-24"
              min={1}
              max={200}
            />
          </div>
          <Button onClick={load} disabled={loading}>
            {loading ? 'Loading…' : 'Load'}
          </Button>
        </div>
      </Card>

      {error && <ErrorBanner message={error} onRetry={load} />}

      {log && (
        <Card className="p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold">Feedback Log</h3>
            <span className="text-sm text-muted-foreground">
              Showing {log.count} of {log.total_in_log} entries
            </span>
          </div>
          {log.entries.length === 0 ? (
            <p className="text-sm text-muted-foreground py-4 text-center">No feedback entries found.</p>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>User ID</TableHead>
                    <TableHead>Track ID</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead className="text-right">Value</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {log.entries.map((entry, i) => (
                    <TableRow key={i}>
                      <TableCell className="text-xs whitespace-nowrap">
                        {new Date(entry.timestamp).toLocaleString()}
                      </TableCell>
                      <TableCell className="font-mono text-xs max-w-32 truncate">{entry.user_id}</TableCell>
                      <TableCell className="font-mono text-xs max-w-32 truncate">{entry.track_id}</TableCell>
                      <TableCell>
                        <Badge variant="secondary" className="capitalize text-xs">{entry.feedback_type}</Badge>
                      </TableCell>
                      <TableCell className="text-right">{entry.value}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </Card>
      )}

      {!log && !loading && !error && (
        <div className="text-center py-12 text-muted-foreground text-sm">
          Select filters and click "Load" to view feedback entries.
        </div>
      )}
    </div>
  );
}

// ── Experiments Tab ───────────────────────────────────────────────────────────

function ExperimentsTab() {
  const [experiments, setExperiments] = useState<{ name: string; status: string }[]>([]);
  const [selectedName, setSelectedName] = useState<string>('');
  const [detail, setDetail] = useState<AdminExperimentDetail | null>(null);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listExperiments()
      .then(setExperiments)
      .finally(() => setLoadingList(false));
  }, []);

  const loadDetail = async (name: string) => {
    if (!name) return;
    setLoadingDetail(true);
    setError(null);
    setDetail(null);
    try {
      setDetail(await getExperimentDetail(name));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load experiment');
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleSelect = (name: string) => {
    setSelectedName(name);
    loadDetail(name);
  };

  return (
    <div className="space-y-4">
      {/* Experiment selector */}
      <Card className="p-4">
        <div className="flex flex-wrap items-end gap-4">
          <div className="space-y-1.5 flex-1 min-w-48">
            <Label>Select Experiment</Label>
            {loadingList ? (
              <Skeleton className="h-10 w-full rounded-md" />
            ) : (
              <Select value={selectedName} onValueChange={handleSelect}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose an experiment…" />
                </SelectTrigger>
                <SelectContent>
                  {experiments.map((exp) => (
                    <SelectItem key={exp.name} value={exp.name}>
                      <span className="font-mono text-sm">{exp.name}</span>
                      <span className="ml-2 text-xs text-muted-foreground capitalize">({exp.status})</span>
                    </SelectItem>
                  ))}
                  {experiments.length === 0 && (
                    <SelectItem value="__none" disabled>No experiments available</SelectItem>
                  )}
                </SelectContent>
              </Select>
            )}
          </div>
          {selectedName && (
            <Button variant="outline" size="sm" onClick={() => loadDetail(selectedName)} disabled={loadingDetail}>
              <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
              Refresh
            </Button>
          )}
        </div>
      </Card>

      {error && <ErrorBanner message={error} onRetry={() => loadDetail(selectedName)} />}

      {loadingDetail && (
        <div className="space-y-3">
          <Skeleton className="h-10 rounded-lg" />
          <Skeleton className="h-48 rounded-lg" />
        </div>
      )}

      {detail && !loadingDetail && (
        <Card className="p-5">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="font-semibold font-mono">{detail.experiment.name}</h3>
            <StatusBadge status={detail.experiment.status} />
          </div>
          <p className="text-xs text-muted-foreground mb-5">
            Generated: {new Date(detail.generated_at).toLocaleString()}
          </p>

          {Object.keys(detail.comparison).length === 0 ? (
            <p className="text-sm text-muted-foreground">No metrics recorded yet for this experiment.</p>
          ) : (() => {
            const variantNames = Object.keys(detail.experiment.variants);
            const metrics = Object.keys(detail.comparison);
            return (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Metric</TableHead>
                      {variantNames.map((v) => (
                        <TableHead key={v} className="text-right font-mono">{v}</TableHead>
                      ))}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {metrics.map((metric) => (
                      <TableRow key={metric}>
                        <TableCell className="font-medium capitalize">{metric.replace(/_/g, ' ')}</TableCell>
                        {variantNames.map((variant) => {
                          const m = detail.comparison[metric]?.[variant];
                          return (
                            <TableCell key={variant} className="text-right text-sm">
                              {m ? (
                                <span>
                                  <span className="font-medium">{m.mean.toFixed(3)}</span>
                                  <span className="text-muted-foreground"> ±{m.std.toFixed(3)}</span>
                                  <span className="text-xs text-muted-foreground ml-1">(n={m.count})</span>
                                </span>
                              ) : (
                                <span className="text-muted-foreground">—</span>
                              )}
                            </TableCell>
                          );
                        })}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            );
          })()}
        </Card>
      )}

      {!selectedName && !loadingList && (
        <div className="text-center py-12 text-muted-foreground text-sm">
          Select an experiment above to view variant comparison results.
        </div>
      )}
    </div>
  );
}

// ── Main Admin Page ───────────────────────────────────────────────────────────

export function Admin() {
  const [loggedIn, setLoggedIn] = useState(isLoggedIn());

  if (!loggedIn) {
    return <LoginForm onSuccess={() => setLoggedIn(true)} />;
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <Tabs defaultValue="overview">
          <TabsList className="mb-6">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="health">System Health</TabsTrigger>
            <TabsTrigger value="feedback">Feedback Log</TabsTrigger>
            <TabsTrigger value="experiments">Experiments</TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <OverviewTab />
          </TabsContent>

          <TabsContent value="health">
            <HealthTab />
          </TabsContent>

          <TabsContent value="feedback">
            <FeedbackTab />
          </TabsContent>

          <TabsContent value="experiments">
            <ExperimentsTab />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
