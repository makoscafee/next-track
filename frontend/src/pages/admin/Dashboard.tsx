import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  BarChart3,
  Activity,
  Users,
  Music,
  Database,
  CheckCircle,
  XCircle,
  Clock,
  LogOut,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import Layout from "../../components/common/Layout";
import Card, {
  CardHeader,
  CardTitle,
  CardContent,
} from "../../components/common/Card";
import Button from "../../components/common/Button";
import type { AdminStats, FeedbackEntry, SystemHealth } from "../../types";
import api from "../../services/api";

const COLORS = ["#8b5cf6", "#06b6d4", "#f472b6", "#22c55e", "#f59e0b"];

export default function AdminDashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [recentFeedback, setRecentFeedback] = useState<FeedbackEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsData, healthData, feedbackData] = await Promise.all([
          api.getAdminStats(),
          api.getSystemHealth(),
          api.getAdminFeedbackLog(10),
        ]);
        setStats(statsData);
        setHealth(healthData);
        setRecentFeedback(feedbackData);
      } catch (error) {
        console.error("Failed to fetch admin data:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    api.logout();
    navigate("/admin/login");
  };

  if (isLoading) {
    return (
      <Layout>
        <div className="min-h-screen flex items-center justify-center">
          <div className="w-16 h-16 border-4 border-[var(--primary)] border-t-transparent rounded-full animate-spin" />
        </div>
      </Layout>
    );
  }

  const feedbackChartData = stats?.feedback.by_type
    ? Object.entries(stats.feedback.by_type).map(([type, count]) => ({
        name: type,
        value: count,
      }))
    : [];

  const experimentChartData =
    stats?.experiments.map((exp) => ({
      name: exp.name,
      observations: exp.total_observations,
      variants: exp.variants,
    })) || [];

  return (
    <Layout>
      <div className="min-h-screen py-8 px-4">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-2xl font-bold text-white">Admin Dashboard</h1>
              <p className="text-[var(--text-muted)]">
                System overview and analytics
              </p>
            </div>
            <Button
              variant="ghost"
              onClick={handleLogout}
              leftIcon={<LogOut className="w-4 h-4" />}
            >
              Logout
            </Button>
          </div>

          {/* Health Status */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-[var(--primary)]" />
                System Health
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {health?.components &&
                  Object.entries(health.components).map(([name, component]) => (
                    <div
                      key={name}
                      className="flex items-center gap-3 p-3 bg-[var(--surface-light)] rounded-lg"
                    >
                      {component.status === "healthy" ? (
                        <CheckCircle className="w-5 h-5 text-[var(--success)]" />
                      ) : (
                        <XCircle className="w-5 h-5 text-[var(--error)]" />
                      )}
                      <div>
                        <p className="text-sm font-medium text-white capitalize">
                          {name.replace(/_/g, " ")}
                        </p>
                        <p className="text-xs text-[var(--text-muted)]">
                          {component.status}
                        </p>
                      </div>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <Card>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-[var(--primary)]/20 flex items-center justify-center">
                  <Music className="w-6 h-6 text-[var(--primary)]" />
                </div>
                <div>
                  <p className="text-sm text-[var(--text-muted)]">
                    Tracks (CB)
                  </p>
                  <p className="text-2xl font-bold text-white">
                    {stats?.models.content_based.n_tracks?.toLocaleString() ||
                      0}
                  </p>
                </div>
              </div>
            </Card>

            <Card>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-[var(--secondary)]/20 flex items-center justify-center">
                  <Users className="w-6 h-6 text-[var(--secondary)]" />
                </div>
                <div>
                  <p className="text-sm text-[var(--text-muted)]">Users (CF)</p>
                  <p className="text-2xl font-bold text-white">
                    {stats?.models.collaborative.n_users?.toLocaleString() || 0}
                  </p>
                </div>
              </div>
            </Card>

            <Card>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-[var(--accent)]/20 flex items-center justify-center">
                  <BarChart3 className="w-6 h-6 text-[var(--accent)]" />
                </div>
                <div>
                  <p className="text-sm text-[var(--text-muted)]">
                    Experiments
                  </p>
                  <p className="text-2xl font-bold text-white">
                    {stats?.experiments.length || 0}
                  </p>
                </div>
              </div>
            </Card>

            <Card>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-[var(--success)]/20 flex items-center justify-center">
                  <Database className="w-6 h-6 text-[var(--success)]" />
                </div>
                <div>
                  <p className="text-sm text-[var(--text-muted)]">Feedback</p>
                  <p className="text-2xl font-bold text-white">
                    {stats?.feedback.total || 0}
                  </p>
                </div>
              </div>
            </Card>
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {/* Experiment Observations */}
            <Card>
              <CardHeader>
                <CardTitle>Experiment Observations</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={experimentChartData}>
                      <CartesianGrid
                        strokeDasharray="3 3"
                        stroke="rgba(255,255,255,0.1)"
                      />
                      <XAxis
                        dataKey="name"
                        tick={{ fill: "var(--text-muted)", fontSize: 12 }}
                        axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
                      />
                      <YAxis
                        tick={{ fill: "var(--text-muted)", fontSize: 12 }}
                        axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "var(--surface)",
                          border: "1px solid rgba(255,255,255,0.1)",
                          borderRadius: "8px",
                        }}
                      />
                      <Bar
                        dataKey="observations"
                        fill="var(--primary)"
                        radius={[4, 4, 0, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Feedback Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Feedback Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  {feedbackChartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={feedbackChartData}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={80}
                          paddingAngle={5}
                          dataKey="value"
                          label={({ name, percent }) =>
                            `${name} (${((percent ?? 0) * 100).toFixed(0)}%)`
                          }
                          labelLine={{ stroke: "var(--text-muted)" }}
                        >
                          {feedbackChartData.map((_, index) => (
                            <Cell
                              key={`cell-${index}`}
                              fill={COLORS[index % COLORS.length]}
                            />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "var(--surface)",
                            border: "1px solid rgba(255,255,255,0.1)",
                            borderRadius: "8px",
                          }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-full flex items-center justify-center text-[var(--text-muted)]">
                      No feedback data yet
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Recent Feedback */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="w-5 h-5 text-[var(--primary)]" />
                Recent Feedback
              </CardTitle>
            </CardHeader>
            <CardContent>
              {recentFeedback.length > 0 ? (
                <div className="space-y-2">
                  {recentFeedback.map((entry, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 bg-[var(--surface-light)] rounded-lg"
                    >
                      <div className="flex items-center gap-3">
                        <span
                          className={`px-2 py-1 text-xs rounded-full ${
                            entry.feedback_type === "play"
                              ? "bg-[var(--success)]/20 text-[var(--success)]"
                              : entry.feedback_type === "save"
                                ? "bg-[var(--accent)]/20 text-[var(--accent)]"
                                : entry.feedback_type === "skip"
                                  ? "bg-[var(--error)]/20 text-[var(--error)]"
                                  : "bg-[var(--primary)]/20 text-[var(--primary)]"
                          }`}
                        >
                          {entry.feedback_type}
                        </span>
                        <span className="text-sm text-white">
                          {entry.track_id}
                        </span>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-[var(--text-muted)]">
                          {new Date(entry.timestamp).toLocaleTimeString()}
                        </p>
                        <p className="text-xs text-[var(--text-muted)]">
                          {entry.user_id}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-[var(--text-muted)] text-center py-4">
                  No feedback recorded yet
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </Layout>
  );
}
