import { useState, useEffect } from "react";
import { FlaskConical, ChevronDown, ChevronUp, Users } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import Layout from "../../components/common/Layout";
import Card from "../../components/common/Card";
import type { Experiment, ExperimentResults } from "../../types";
import api from "../../services/api";

export default function AdminExperiments() {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [expandedExperiment, setExpandedExperiment] = useState<string | null>(
    null,
  );
  const [experimentDetails, setExperimentDetails] = useState<
    Record<string, ExperimentResults>
  >({});
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchExperiments = async () => {
      try {
        const data = await api.getExperiments();
        setExperiments(data);
      } catch (error) {
        console.error("Failed to fetch experiments:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchExperiments();
  }, []);

  const handleExpandExperiment = async (name: string) => {
    if (expandedExperiment === name) {
      setExpandedExperiment(null);
      return;
    }

    setExpandedExperiment(name);

    if (!experimentDetails[name]) {
      try {
        const details = await api.getExperiment(name);
        setExperimentDetails((prev) => ({ ...prev, [name]: details }));
      } catch (error) {
        console.error("Failed to fetch experiment details:", error);
      }
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "running":
        return "bg-[var(--success)]/20 text-[var(--success)]";
      case "paused":
        return "bg-[var(--warning)]/20 text-[var(--warning)]";
      case "completed":
        return "bg-[var(--primary)]/20 text-[var(--primary)]";
      default:
        return "bg-[var(--surface-light)] text-[var(--text-muted)]";
    }
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

  return (
    <Layout>
      <div className="min-h-screen py-8 px-4">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-white flex items-center gap-2">
              <FlaskConical className="w-6 h-6 text-[var(--primary)]" />
              A/B Test Experiments
            </h1>
            <p className="text-[var(--text-muted)] mt-1">
              Monitor and analyze recommendation strategy experiments
            </p>
          </div>

          {/* Experiments List */}
          <div className="space-y-4">
            {experiments.map((experiment) => {
              const isExpanded = expandedExperiment === experiment.name;
              const details = experimentDetails[experiment.name];

              return (
                <Card key={experiment.name} className="overflow-hidden">
                  {/* Experiment Header */}
                  <button
                    onClick={() => handleExpandExperiment(experiment.name)}
                    className="w-full flex items-center justify-between p-4 text-left hover:bg-white/5 transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-xl bg-[var(--primary)]/20 flex items-center justify-center">
                        <FlaskConical className="w-5 h-5 text-[var(--primary)]" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-white">
                          {experiment.name}
                        </h3>
                        <p className="text-sm text-[var(--text-muted)]">
                          {experiment.description}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <span
                        className={`px-3 py-1 text-xs font-medium rounded-full capitalize ${getStatusColor(
                          experiment.status,
                        )}`}
                      >
                        {experiment.status}
                      </span>
                      <div className="flex items-center gap-1 text-[var(--text-muted)]">
                        <Users className="w-4 h-4" />
                        <span className="text-sm">
                          {experiment.variants.length} variants
                        </span>
                      </div>
                      {isExpanded ? (
                        <ChevronUp className="w-5 h-5 text-[var(--text-muted)]" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-[var(--text-muted)]" />
                      )}
                    </div>
                  </button>

                  {/* Expanded Details */}
                  {isExpanded && details && (
                    <div className="border-t border-white/10 p-6">
                      {/* Variants */}
                      <div className="mb-6">
                        <h4 className="text-sm font-medium text-white mb-3">
                          Variants
                        </h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          {Object.entries(details.variants).map(
                            ([variantName, variant]) => (
                              <div
                                key={variantName}
                                className="p-4 bg-[var(--surface-light)] rounded-xl"
                              >
                                <div className="flex items-center justify-between mb-2">
                                  <span className="font-medium text-white">
                                    {variantName}
                                  </span>
                                  <span className="text-sm text-[var(--text-muted)]">
                                    {(variant.weight * 100).toFixed(0)}% traffic
                                  </span>
                                </div>
                                {variant.config &&
                                  Object.keys(variant.config).length > 0 && (
                                    <div className="space-y-1">
                                      {Object.entries(variant.config).map(
                                        ([key, value]) => (
                                          <div
                                            key={key}
                                            className="flex justify-between text-xs"
                                          >
                                            <span className="text-[var(--text-muted)]">
                                              {key}
                                            </span>
                                            <span className="text-white">
                                              {String(value)}
                                            </span>
                                          </div>
                                        ),
                                      )}
                                    </div>
                                  )}
                              </div>
                            ),
                          )}
                        </div>
                      </div>

                      {/* Metrics Comparison */}
                      {(() => {
                        const metricsData: {
                          metric: string;
                          [key: string]: string | number;
                        }[] = [];
                        const allMetrics = new Set<string>();

                        Object.values(details.variants).forEach((variant) => {
                          Object.keys(variant.metrics || {}).forEach((m) =>
                            allMetrics.add(m),
                          );
                        });

                        allMetrics.forEach((metric) => {
                          const row: {
                            metric: string;
                            [key: string]: string | number;
                          } = { metric };
                          Object.entries(details.variants).forEach(
                            ([variantName, variant]) => {
                              const stats = variant.metrics?.[metric];
                              row[variantName] = stats?.mean || 0;
                            },
                          );
                          metricsData.push(row);
                        });

                        if (metricsData.length === 0) {
                          return (
                            <p className="text-[var(--text-muted)] text-center py-4">
                              No metrics recorded yet
                            </p>
                          );
                        }

                        const variantNames = Object.keys(details.variants);
                        const colors = [
                          "#8b5cf6",
                          "#06b6d4",
                          "#f472b6",
                          "#22c55e",
                        ];

                        return (
                          <div>
                            <h4 className="text-sm font-medium text-white mb-3">
                              Metrics Comparison
                            </h4>
                            <div className="h-64">
                              <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={metricsData}>
                                  <CartesianGrid
                                    strokeDasharray="3 3"
                                    stroke="rgba(255,255,255,0.1)"
                                  />
                                  <XAxis
                                    dataKey="metric"
                                    tick={{
                                      fill: "var(--text-muted)",
                                      fontSize: 12,
                                    }}
                                  />
                                  <YAxis
                                    tick={{
                                      fill: "var(--text-muted)",
                                      fontSize: 12,
                                    }}
                                  />
                                  <Tooltip
                                    contentStyle={{
                                      backgroundColor: "var(--surface)",
                                      border: "1px solid rgba(255,255,255,0.1)",
                                      borderRadius: "8px",
                                    }}
                                  />
                                  <Legend />
                                  {variantNames.map((name, i) => (
                                    <Bar
                                      key={name}
                                      dataKey={name}
                                      fill={colors[i % colors.length]}
                                      radius={[4, 4, 0, 0]}
                                    />
                                  ))}
                                </BarChart>
                              </ResponsiveContainer>
                            </div>
                          </div>
                        );
                      })()}
                    </div>
                  )}
                </Card>
              );
            })}
          </div>

          {experiments.length === 0 && (
            <Card className="text-center py-8">
              <FlaskConical className="w-12 h-12 text-[var(--text-muted)] mx-auto mb-4" />
              <p className="text-[var(--text-muted)]">
                No experiments configured
              </p>
            </Card>
          )}
        </div>
      </div>
    </Layout>
  );
}
