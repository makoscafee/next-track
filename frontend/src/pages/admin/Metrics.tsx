import { useState, useEffect } from "react";
import { TrendingUp, Clock, Filter } from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import Layout from "../../components/common/Layout";
import Card, {
  CardHeader,
  CardTitle,
  CardContent,
} from "../../components/common/Card";
import type { FeedbackEntry } from "../../types";
import api from "../../services/api";

const FEEDBACK_TYPES = [
  "all",
  "click",
  "play",
  "skip",
  "save",
  "listen_time",
] as const;

export default function AdminMetrics() {
  const [feedbackLog, setFeedbackLog] = useState<FeedbackEntry[]>([]);
  const [selectedType, setSelectedType] = useState<string>("all");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchFeedback = async () => {
      setIsLoading(true);
      try {
        const data = await api.getAdminFeedbackLog(
          100,
          selectedType === "all" ? undefined : selectedType,
        );
        setFeedbackLog(data);
      } catch (error) {
        console.error("Failed to fetch feedback:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchFeedback();
    const interval = setInterval(fetchFeedback, 15000);
    return () => clearInterval(interval);
  }, [selectedType]);

  // Process data for time series chart
  const timeSeriesData = (() => {
    const grouped: Record<string, Record<string, number>> = {};

    feedbackLog.forEach((entry) => {
      const time = new Date(entry.timestamp);
      const key = `${time.getHours()}:${time.getMinutes().toString().padStart(2, "0")}`;

      if (!grouped[key]) {
        grouped[key] = { click: 0, play: 0, skip: 0, save: 0 };
      }

      if (entry.feedback_type in grouped[key]) {
        grouped[key][entry.feedback_type]++;
      }
    });

    return Object.entries(grouped)
      .map(([time, counts]) => ({ time, ...counts }))
      .slice(-20);
  })();

  // Calculate summary stats
  const stats = {
    total: feedbackLog.length,
    clicks: feedbackLog.filter((f) => f.feedback_type === "click").length,
    plays: feedbackLog.filter((f) => f.feedback_type === "play").length,
    saves: feedbackLog.filter((f) => f.feedback_type === "save").length,
    skips: feedbackLog.filter((f) => f.feedback_type === "skip").length,
    conversionRate:
      feedbackLog.length > 0
        ? (
            (feedbackLog.filter((f) => f.feedback_type === "play").length /
              feedbackLog.filter((f) => f.feedback_type === "click").length) *
            100
          ).toFixed(1)
        : 0,
  };

  return (
    <Layout>
      <div className="min-h-screen py-8 px-4">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                <TrendingUp className="w-6 h-6 text-[var(--primary)]" />
                Metrics & Analytics
              </h1>
              <p className="text-[var(--text-muted)] mt-1">
                Track user interactions and recommendation performance
              </p>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            <Card>
              <p className="text-sm text-[var(--text-muted)]">Total Events</p>
              <p className="text-2xl font-bold text-white">{stats.total}</p>
            </Card>
            <Card>
              <p className="text-sm text-[var(--text-muted)]">Clicks</p>
              <p className="text-2xl font-bold text-[var(--primary)]">
                {stats.clicks}
              </p>
            </Card>
            <Card>
              <p className="text-sm text-[var(--text-muted)]">Plays</p>
              <p className="text-2xl font-bold text-[var(--success)]">
                {stats.plays}
              </p>
            </Card>
            <Card>
              <p className="text-sm text-[var(--text-muted)]">Saves</p>
              <p className="text-2xl font-bold text-[var(--accent)]">
                {stats.saves}
              </p>
            </Card>
            <Card>
              <p className="text-sm text-[var(--text-muted)]">Play Rate</p>
              <p className="text-2xl font-bold text-[var(--secondary)]">
                {stats.conversionRate}%
              </p>
            </Card>
          </div>

          {/* Time Series Chart */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Feedback Over Time</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                {timeSeriesData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={timeSeriesData}>
                      <CartesianGrid
                        strokeDasharray="3 3"
                        stroke="rgba(255,255,255,0.1)"
                      />
                      <XAxis
                        dataKey="time"
                        tick={{ fill: "var(--text-muted)", fontSize: 12 }}
                      />
                      <YAxis
                        tick={{ fill: "var(--text-muted)", fontSize: 12 }}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "var(--surface)",
                          border: "1px solid rgba(255,255,255,0.1)",
                          borderRadius: "8px",
                        }}
                      />
                      <Line
                        type="monotone"
                        dataKey="click"
                        stroke="var(--primary)"
                        strokeWidth={2}
                        dot={false}
                      />
                      <Line
                        type="monotone"
                        dataKey="play"
                        stroke="var(--success)"
                        strokeWidth={2}
                        dot={false}
                      />
                      <Line
                        type="monotone"
                        dataKey="save"
                        stroke="var(--accent)"
                        strokeWidth={2}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full flex items-center justify-center text-[var(--text-muted)]">
                    No data to display
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Feedback Log */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Clock className="w-5 h-5 text-[var(--primary)]" />
                Feedback Log
              </CardTitle>
              <div className="flex items-center gap-2">
                <Filter className="w-4 h-4 text-[var(--text-muted)]" />
                <div className="flex gap-1">
                  {FEEDBACK_TYPES.map((type) => (
                    <button
                      key={type}
                      onClick={() => setSelectedType(type)}
                      className={`px-3 py-1 text-xs rounded-full capitalize transition-colors ${
                        selectedType === type
                          ? "bg-[var(--primary)] text-white"
                          : "bg-[var(--surface-light)] text-[var(--text-muted)] hover:text-white"
                      }`}
                    >
                      {type}
                    </button>
                  ))}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="flex justify-center py-8">
                  <div className="w-8 h-8 border-2 border-[var(--primary)] border-t-transparent rounded-full animate-spin" />
                </div>
              ) : feedbackLog.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-white/10">
                        <th className="text-left py-3 px-4 text-sm font-medium text-[var(--text-muted)]">
                          Time
                        </th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-[var(--text-muted)]">
                          Type
                        </th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-[var(--text-muted)]">
                          Track ID
                        </th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-[var(--text-muted)]">
                          User ID
                        </th>
                        <th className="text-right py-3 px-4 text-sm font-medium text-[var(--text-muted)]">
                          Value
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {feedbackLog.map((entry, index) => (
                        <tr
                          key={index}
                          className="border-b border-white/5 hover:bg-white/5 transition-colors"
                        >
                          <td className="py-3 px-4 text-sm text-[var(--text-muted)]">
                            {new Date(entry.timestamp).toLocaleTimeString()}
                          </td>
                          <td className="py-3 px-4">
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
                          </td>
                          <td className="py-3 px-4 text-sm text-white font-mono">
                            {entry.track_id.length > 20
                              ? entry.track_id.substring(0, 20) + "..."
                              : entry.track_id}
                          </td>
                          <td className="py-3 px-4 text-sm text-[var(--text-muted)] font-mono">
                            {entry.user_id.length > 15
                              ? entry.user_id.substring(0, 15) + "..."
                              : entry.user_id}
                          </td>
                          <td className="py-3 px-4 text-sm text-right text-white">
                            {entry.value}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-[var(--text-muted)] text-center py-8">
                  No feedback events recorded yet
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </Layout>
  );
}
