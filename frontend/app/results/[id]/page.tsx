'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { MetricCard } from '@/components/ui/MetricCard';
import { Header } from '@/components/Header';
import SHAPVisualization from '@/components/SHAPVisualization';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/useAuth';
import { Job, JobResults } from '@/types/api';
import { Sparkles } from 'lucide-react';

export default function ResultsPage() {
  useAuth();
  const router = useRouter();
  const params = useParams();
  const jobId = Number(params.id);

  const [job, setJob] = useState<Job | null>(null);
  const [results, setResults] = useState<JobResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadResults();
  }, [jobId]);

  const loadResults = async () => {
    try {
      const resultsData = await api.getWorkflowResults(jobId);
      setJob(resultsData as any);
      setResults(resultsData.results as any);
      setLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load results');
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <>
        <Header />
        <div className="min-h-[calc(100vh-64px)] bg-gradient-to-b from-black via-zinc-950/90 to-black flex-center-col">
          <div className="text-center-wrapper">
            <div className="animate-spin rounded-full h-12 w-12 border-2 border-white/20 border-t-white mx-auto mb-4"></div>
            <div className="text-zinc-300 text-lg font-medium">Loading results...</div>
          </div>
        </div>
      </>
    );
  }

  if (error || !results) {
    return (
      <>
        <Header />
        <div className="min-h-screen bg-black flex-center-col px-4">
          <div className="centered-card rounded-lg border border-red-900/60 bg-red-950/40 px-4 py-3 text-sm text-red-200">
            {error || 'Results not found'}
          </div>
        </div>
      </>
    );
  }

  const metrics = results.metrics || {};
  const featureImportanceObj = results.feature_importance || {};
  const featureImportance = Object.entries(featureImportanceObj)
    .map(([feature, importance]) => ({
      feature,
      importance: importance as number,
    }))
    .sort((a, b) => b.importance - a.importance);

  const confusionMatrix = results.confusion_matrix || [];
  const sequenceStats = results.sequence_stats || null;

  const isClassification = metrics.accuracy !== undefined;
  const maxImportance =
    featureImportance.length > 0
      ? Math.max(...featureImportance.map((f) => f.importance))
      : 1;

  return (
    <>
      <Header />
      <div className="min-h-[calc(100vh-64px)] bg-gradient-to-b from-black via-zinc-950/90 to-black">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 page-section padding-section">
          <div className="gap-section flex flex-col">
            {/* Page Header */}
            <div className="flex flex-col lg:flex-row justify-between items-start gap-6 lg:gap-8 section-spacing">
              <div className="flex-1">
                <h1 className="text-4xl sm:text-5xl lg:text-5xl font-bold bg-gradient-to-br from-white via-zinc-100 to-zinc-400 bg-clip-text text-transparent mb-4">
                  Training Results
                </h1>
                <div className="space-y-2">
                  {job?.name && (
                    <p className="text-lg text-zinc-400">
                      <span className="text-zinc-300 font-medium">{job.name}</span>
                    </p>
                  )}
                  <p className="text-base text-zinc-400">
                    Best performing model:{' '}
                    <span className="font-semibold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                      {results.best_model || 'RandomForest'}
                    </span>
                  </p>
                </div>
              </div>
              <div className="flex flex-col sm:flex-row gap-3 lg:gap-4">
                <Button
                  variant="secondary"
                  onClick={() => window.open(api.getWorkflowModelDownloadUrl(jobId))}
                  size="md"
                  className="min-w-[160px]"
                >
                  Download Model
                </Button>
                <Button
                  onClick={() =>
                    window.open(api.getWorkflowReportDownloadUrl(jobId), '_blank')
                  }
                  size="md"
                  className="min-w-[160px]"
                >
                  Download Report
                </Button>
              </div>
            </div>

          {/* Sequence stats */}
          {sequenceStats && (
            <Card className="p-7 sm:p-8 lg:p-9 border-zinc-800/70 bg-zinc-950/70 card-spacing">
              <h2 className="text-lg sm:text-xl font-semibold text-zinc-50 mb-6">
                Sequence data summary
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="rounded-lg bg-black/40 border border-zinc-800 px-4 py-3">
                  <p className="text-xs text-zinc-500 mb-1">Total sequences</p>
                  <p className="text-2xl font-semibold text-zinc-50">
                    {sequenceStats.total_sequences}
                  </p>
                </div>
                <div className="rounded-lg bg-black/40 border border-zinc-800 px-4 py-3">
                  <p className="text-xs text-zinc-500 mb-1">Average length</p>
                  <p className="text-2xl font-semibold text-zinc-50">
                    {sequenceStats.avg_length?.toFixed(0) || 0}{' '}
                    <span className="text-sm text-zinc-500">bp</span>
                  </p>
                </div>
                <div className="rounded-lg bg-black/40 border border-zinc-800 px-4 py-3">
                  <p className="text-xs text-zinc-500 mb-1">Sequence type</p>
                  <p className="text-2xl font-semibold text-zinc-50 capitalize">
                    {sequenceStats.sequence_type}
                  </p>
                </div>
              </div>
            </Card>
          )}

          {/* Model comparison */}
          {results.models_trained && results.models_trained.length > 0 && (
            <Card className="p-7 sm:p-8 lg:p-9 border-zinc-800/70  card-spacing">
              <div className="space-y-6">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between ">
                <div>
                  <h2 className="text-lg sm:text-xl font-semibold text-zinc-50">
                    Model comparison
                  </h2>
                  <p className="text-xs sm:text-sm text-zinc-500 mt-1">
                    Performance of all trained models • Total training time:{' '}
                    {results.training_time?.toFixed(2) || 0}s
                  </p>
                </div>
              </div>
              <div className="overflow-x-auto rounded-lg border border-zinc-800">
                <table className="w-full text-sm">
                  <thead className="bg-black/40">
                    <tr>
                      <th className="text-left py-3 px-4 font-medium text-zinc-400">
                        Model
                      </th>
                      <th className="text-left py-3 px-4 font-medium text-zinc-400">
                        Type
                      </th>
                      <th className="text-right py-3 px-4 font-medium text-zinc-400">
                        Train score
                      </th>
                      <th className="text-right py-3 px-4 font-medium text-zinc-400">
                        Val score
                      </th>
                      <th className="text-right py-3 px-4 font-medium text-zinc-400">
                        Time (s)
                      </th>
                      <th className="text-center py-3 px-4 font-medium text-zinc-400">
                        Rank
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.models_trained
                      .sort(
                        (a, b) =>
                          (b.metrics?.primary_score || 0) -
                          (a.metrics?.primary_score || 0),
                      )
                      .map((model, idx) => (
                        <tr
                          key={idx}
                          className={`border-t border-zinc-800/70 text-xs sm:text-sm ${
                            model.is_best ? 'bg-white/5' : 'hover:bg-zinc-900/60'
                          }`}
                        >
                          <td className="py-3 px-4">
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-zinc-100">
                                {model.model_name}
                              </span>
                              {model.is_best && (
                                <span className="px-2 py-0.5 text-[10px] font-semibold bg-emerald-500/15 text-emerald-300 rounded-full border border-emerald-400/30">
                                  BEST
                                </span>
                              )}
                            </div>
                          </td>
                          <td className="py-3 px-4 text-zinc-400">
                            {model.model_type}
                          </td>
                          <td className="py-3 px-4 text-right font-mono text-zinc-100">
                            {model.metrics?.train_score?.toFixed(4) || '—'}
                          </td>
                          <td className="py-3 px-4 text-right font-mono">
                            <span
                              className={
                                model.metrics?.val_score &&
                                model.metrics.val_score > 0.85
                                  ? 'text-emerald-300'
                                  : 'text-zinc-100'
                              }
                            >
                              {model.metrics?.val_score?.toFixed(4) || '—'}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-right font-mono text-zinc-400">
                            {model.training_time?.toFixed(2) || 0}
                          </td>
                          <td className="py-3 px-4 text-center">
                            {idx === 0 ? (
                              <span className="text-yellow-300">1</span>
                            ) : idx === 1 ? (
                              <span className="text-zinc-300">2</span>
                            ) : idx === 2 ? (
                              <span className="text-orange-300">3</span>
                            ) : (
                              <span className="text-zinc-600">—</span>
                            )}
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs sm:text-sm">
                <div className="rounded-lg bg-black/40 border border-zinc-800 px-4 py-3">
                  <p className="text-zinc-500 mb-1">Best model</p>
                  <p className="font-medium text-zinc-100">
                    {results.best_model}
                  </p>
                </div>
                <div className="rounded-lg bg-black/40 border border-zinc-800 px-4 py-3">
                  <p className="text-zinc-500 mb-1">Models trained</p>
                  <p className="font-medium text-zinc-100">
                    {results.models_trained.length}
                  </p>
                </div>
                <div className="rounded-lg bg-black/40 border border-zinc-800 px-4 py-3">
                  <p className="text-zinc-500 mb-1">Fastest model</p>
                  <p className="font-medium text-zinc-100">
                    {
                      results.models_trained.reduce((fastest, model) =>
                        model.training_time < fastest.training_time
                          ? model
                          : fastest,
                      ).model_name
                    }
                  </p>
                </div>
              </div>
              </div>
            </Card>
          )}

          {/* Metrics cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 card-spacing mt-6">
            {isClassification ? (
              <>
                <MetricCard
                  label="Accuracy"
                  value={metrics.accuracy || 0}
                  good={(metrics.accuracy || 0) > 0.85}
                />
                <MetricCard
                  label="F1 score"
                  value={metrics.f1_score || 0}
                  good={(metrics.f1_score || 0) > 0.8}
                />
                <MetricCard
                  label="Precision"
                  value={metrics.precision || 0}
                  good={(metrics.precision || 0) > 0.8}
                />
                <MetricCard
                  label="Recall"
                  value={metrics.recall || 0}
                  good={(metrics.recall || 0) > 0.8}
                />
              </>
            ) : (
              <>
                <MetricCard
                  label="R² score"
                  value={metrics.r2 || 0}
                  good={(metrics.r2 || 0) > 0.8}
                />
                <MetricCard label="MSE" value={metrics.mse || 0} />
                <MetricCard label="RMSE" value={metrics.rmse || 0} />
              </>
            )}
          </div>

          {/* Feature importance + confusion matrix */}
          {/* <div className="grid grid-cols-1 lg:grid-cols-2 gap-section card-spacing">
            <Card className="p-7 sm:p-8 lg:p-9 border-zinc-800/70 bg-zinc-950/70">
              <h2 className="text-lg sm:text-xl font-semibold text-zinc-50 mb-6">
                Top features
              </h2>
              <p className="text-xs sm:text-sm text-zinc-500 mb-5">
                Features that most influence the model&apos;s predictions
              </p>
              <div className="space-y-3">
                {featureImportance.slice(0, 10).map((item, i) => (
                  <div key={i}>
                    <div className="flex justify-between text-xs sm:text-sm mb-1.5">
                      <span className="font-medium text-zinc-100 truncate max-w-[55%]">
                        {item.feature}
                      </span>
                      <span className="text-zinc-400 font-mono">
                        {item.importance.toFixed(3)}
                      </span>
                    </div>
                    <div className="w-full bg-zinc-900 rounded-full h-1.5">
                      <div
                        className="bg-zinc-100 h-1.5 rounded-full transition-all"
                        style={{
                          width: `${(item.importance / maxImportance) * 100}%`,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {isClassification && confusionMatrix.length > 0 && (
              <Card className="p-7 sm:p-8 lg:p-9 border-zinc-800/70 bg-zinc-950/70">
                <h2 className="text-lg sm:text-xl font-semibold text-zinc-50 mb-6">
                  Confusion matrix
                </h2>
                <p className="text-xs sm:text-sm text-zinc-500 mb-5">
                  Actual vs predicted classifications
                </p>
                <div className="overflow-x-auto">
                  <table className="border-collapse mx-auto">
                    <tbody>
                      {confusionMatrix.map((row, i) => (
                        <tr key={i}>
                          {row.map((cell, j) => {
                            const max = Math.max(...confusionMatrix.flat());
                            const intensity = max ? cell / max : 0;
                            return (
                              <td
                                key={j}
                                className="p-4 text-center border border-zinc-800 text-xs sm:text-sm text-zinc-100 transition-transform hover:scale-[1.03]"
                                style={{
                                  backgroundColor: `rgba(255, 255, 255, ${
                                    intensity * 0.2
                                  })`,
                                }}
                              >
                                {cell}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            )}
          </div> */}

          {/* Summary */}
          <Card className="p-7 sm:p-8 lg:p-9 border-zinc-800/70 bg-zinc-950/70 card-spacing">
            <h2 className="text-lg sm:text-xl font-semibold text-zinc-50 mb-6">
              Summary
            </h2>
            <ul className="space-y-2.5 text-xs sm:text-sm text-zinc-300 list-disc list-inside">
              {isClassification ? (
                <>
                  <li>
                    The model correctly classified{' '}
                    {((metrics.accuracy || 0) * 100).toFixed(1)}% of samples
                    with {((
                      metrics.precision || 0
                    ) * 100).toFixed(1)}
                    % precision.
                  </li>
                  <li>
                    Top contributing features:{' '}
                    {featureImportance
                      .slice(0, 3)
                      .map((f) => f.feature)
                      .join(', ')}
                    .
                  </li>
                  {sequenceStats && (
                    <li>
                      Analyzed {sequenceStats.total_sequences}{' '}
                      {sequenceStats.sequence_type} sequences with an average
                      length of {sequenceStats.avg_length.toFixed(0)} base
                      pairs.
                    </li>
                  )}
                </>
              ) : (
                <>
                  <li>
                    The model achieved an R² score of{' '}
                    {(metrics.r2 || 0).toFixed(3)}, explaining{' '}
                    {((metrics.r2 || 0) * 100).toFixed(1)}% of variance.
                  </li>
                  <li>
                    Top contributing features:{' '}
                    {featureImportance
                      .slice(0, 3)
                      .map((f) => f.feature)
                      .join(', ')}
                    .
                  </li>
                </>
              )}
            </ul>
          </Card>

          {/* Biological insights */}
          {sequenceStats &&
            featureImportance.some((f) => f.feature.startsWith('kmer_')) && (
              <Card className="p-7 sm:p-8 lg:p-9 border-zinc-800/70 bg-zinc-950/70 card-spacing">
                <h2 className="text-lg sm:text-xl font-semibold text-zinc-50 mb-6">
                  Biological insights
                </h2>
                <div className="space-y-5">
                  <div>
                    <h3 className="text-sm sm:text-base font-semibold text-zinc-100 mb-2">
                      Key sequence patterns
                    </h3>
                    <p className="text-xs sm:text-sm text-zinc-500 mb-3">
                      K-mer analysis identified the following motifs as most
                      predictive:
                    </p>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                      {featureImportance
                        .filter((f) => f.feature.startsWith('kmer_'))
                        .slice(0, 6)
                        .map((f, i) => (
                          <div
                            key={i}
                            className="bg-black/40 p-3 rounded-lg border border-zinc-800"
                          >
                            <div className="font-mono text-zinc-50 font-semibold text-base mb-1">
                              {f.feature.replace('kmer_', '')}
                            </div>
                            <div className="text-xs text-zinc-400">
                              Importance: {(f.importance * 100).toFixed(1)}%
                            </div>
                          </div>
                        ))}
                    </div>
                  </div>

                  <div className="pt-3 border-t border-zinc-800">
                    <h3 className="text-sm sm:text-base font-semibold text-zinc-100 mb-2">
                      Interpretation
                    </h3>
                    <p className="text-xs sm:text-sm text-zinc-400 leading-relaxed">
                      These sequence patterns show strong association with the
                      target variable, suggesting potential functional or
                      structural significance.{' '}
                      {sequenceStats.sequence_type === 'dna' &&
                        'These DNA motifs may represent regulatory elements, binding sites, or conserved regions.'}
                      {sequenceStats.sequence_type === 'protein' &&
                        'These protein patterns may indicate functional domains or structural motifs.'}
                    </p>
                  </div>
                </div>
              </Card>
            )}

          {/* SHAP section */}
          {results.shap_explanations && results.shap_explanations.success && (
            <SHAPVisualization shapData={results.shap_explanations} />
          )}

            {/* Footer Actions */}
            <div className="flex justify-center pt-8 mt-8 border-t border-zinc-800/50">
              <Button 
                onClick={() => router.push('/')} 
                variant="outline" 
                size="lg"
                className="min-w-[200px] flex items-center gap-2"
              >
                <Sparkles className="w-4 h-4" />
                Run New Analysis
              </Button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
