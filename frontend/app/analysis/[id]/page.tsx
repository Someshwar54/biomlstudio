'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Header } from '@/components/Header';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/useAuth';
import { Lightbulb, Search, Dna, Microscope, FlaskConical, Rocket, RotateCcw, Folder, CheckCircle2, AlertTriangle, X, Circle } from 'lucide-react';

interface AnalysisData {
  dataset_id: number;
  dataset_type: string;
  basic_stats: any;
  quality_analysis?: any;
  missing_data?: any;
  recommendations?: string[];
  column_info?: any;
  detailed_stats?: any;
  correlation_analysis?: any;
  distribution_analysis?: any;
  outlier_analysis?: any;
}

interface VisualizationData {
  dataset_id: number;
  plots: { [key: string]: string };
  plot_descriptions?: { [key: string]: string };
}

export default function AnalysisPage() {
  useAuth();
  const params = useParams();
  const router = useRouter();
  const datasetId = parseInt(params.id as string);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dataset, setDataset] = useState<any>(null);
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
  const [visualizations, setVisualizations] = useState<VisualizationData | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'quality' | 'detailed' | 'correlation' | 'visualizations'>('overview');

  useEffect(() => {
    loadAnalysisData();
  }, [datasetId]);

  const loadAnalysisData = async () => {
    setLoading(true);
    setError('');

    try {
      // Load dataset info
      const datasetInfo = await api.getDataset(datasetId);
      setDataset(datasetInfo);

      // Load analysis
      const analysisData = await api.analyzeDataset(datasetId);
      setAnalysis(analysisData);

      // Load visualizations
      const vizData = await api.visualizeDataset(datasetId);
      setVisualizations(vizData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analysis');
    } finally {
      setLoading(false);
    }
  };

  const renderBasicStats = () => {
    if (!analysis?.basic_stats) return null;

    const stats = analysis.basic_stats;

    return (
      <div className="space-y-6">
        {/* Primary Statistics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {stats.total_rows && (
            <Card className="text-center">
              <div className="p-4">
                <div className="text-3xl font-bold mb-2 text-blue-400">{stats.total_rows.toLocaleString()}</div>
                <div className="text-sm text-zinc-400 font-medium">Total Rows</div>
              </div>
            </Card>
          )}
          {stats.total_columns && (
            <Card className="text-center">
              <div className="p-4">
                <div className="text-3xl font-bold mb-2 text-green-400">{stats.total_columns}</div>
                <div className="text-sm text-zinc-400 font-medium">Total Columns</div>
              </div>
            </Card>
          )}
          {stats.sequence_count && (
            <Card className="text-center">
              <div className="p-4">
                <div className="text-3xl font-bold mb-2 text-purple-400">{stats.sequence_count.toLocaleString()}</div>
                <div className="text-sm text-zinc-400 font-medium">Sequences</div>
              </div>
            </Card>
          )}
          {stats.mean && (
            <Card className="text-center">
              <div className="p-4">
                <div className="text-3xl font-bold mb-2 text-yellow-400">{(stats.mean * 100).toFixed(1)}%</div>
                <div className="text-sm text-zinc-400 font-medium">GC Content</div>
              </div>
            </Card>
          )}
        </div>

        {/* Sequence Length Statistics */}
        {(stats.avg_sequence_length || stats.min_sequence_length || stats.max_sequence_length) && (
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Sequence Length Distribution</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {stats.min_sequence_length && (
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-400 mb-1">{stats.min_sequence_length}</div>
                  <div className="text-sm text-zinc-400">Minimum Length</div>
                </div>
              )}
              {stats.avg_sequence_length && (
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-400 mb-1">{Math.round(stats.avg_sequence_length)}</div>
                  <div className="text-sm text-zinc-400">Average Length</div>
                </div>
              )}
              {stats.max_sequence_length && (
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-400 mb-1">{stats.max_sequence_length}</div>
                  <div className="text-sm text-zinc-400">Maximum Length</div>
                </div>
              )}
            </div>
            {stats.avg_sequence_length && stats.min_sequence_length && stats.max_sequence_length && (
              <div className="mt-4 pt-4 border-t border-zinc-700">
                <div className="flex justify-between text-sm text-zinc-400">
                  <span>Length Variation:</span>
                  <span>{((stats.max_sequence_length - stats.min_sequence_length) / stats.avg_sequence_length * 100).toFixed(1)}% of average</span>
                </div>
              </div>
            )}
          </Card>
        )}

        {/* Additional Statistics for CSV datasets */}
        {dataset?.dataset_type === 'csv' && analysis?.column_info && (
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Dataset Overview</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="text-center p-3 bg-zinc-800 rounded-lg">
                <div className="text-xl font-bold text-blue-400 mb-1">
                  {Object.keys(analysis.column_info.data_types || {}).filter(col => 
                    ['int64', 'float64', 'int32', 'float32'].includes(analysis.column_info.data_types[col])
                  ).length}
                </div>
                <div className="text-sm text-zinc-400">Numeric Columns</div>
              </div>
              <div className="text-center p-3 bg-zinc-800 rounded-lg">
                <div className="text-xl font-bold text-green-400 mb-1">
                  {Object.keys(analysis.column_info.data_types || {}).filter(col => 
                    analysis.column_info.data_types[col] === 'object'
                  ).length}
                </div>
                <div className="text-sm text-zinc-400">Text Columns</div>
              </div>
              <div className="text-center p-3 bg-zinc-800 rounded-lg">
                <div className="text-xl font-bold text-purple-400 mb-1">
                  {Object.values(analysis.column_info.missing_values || {}).reduce((sum: number, info: any) => sum + info.count, 0)}
                </div>
                <div className="text-sm text-zinc-400">Missing Values</div>
              </div>
              <div className="text-center p-3 bg-zinc-800 rounded-lg">
                <div className="text-xl font-bold text-yellow-400 mb-1">
                  {(Object.values(analysis.column_info.unique_counts || {}) as number[]).reduce((sum: number, count: number) => Math.max(sum, count), 0)}
                </div>
                <div className="text-sm text-zinc-400">Max Unique Values</div>
              </div>
            </div>
          </Card>
        )}
      </div>
    );
  };

  const renderQualityAnalysis = () => {
    if (!analysis?.quality_analysis) {
      return (
        <Card>
          <p className="text-zinc-400">No quality analysis available for this dataset type.</p>
        </Card>
      );
    }

    const qa = analysis.quality_analysis;

    return (
      <div className="gap-section flex flex-col">
        <Card className="card-spacing">
          <h3 className="text-lg font-semibold mb-5">Quality Summary</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-zinc-400">Total Sequences</p>
              <p className="text-2xl font-bold">{qa.total_sequences}</p>
            </div>
            <div>
              <p className="text-sm text-zinc-400">Sequences with Issues</p>
              <p className="text-2xl font-bold text-yellow-500">{qa.sequences_with_issues}</p>
            </div>
          </div>
        </Card>

        {qa.ambiguous_bases && (
          <Card className="card-spacing">
            <h3 className="text-lg font-semibold mb-5">Ambiguous Bases</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-zinc-400">Total Count</p>
                <p className="text-xl font-bold">{qa.ambiguous_bases.total_count}</p>
              </div>
              <div>
                <p className="text-sm text-zinc-400">Sequences Affected</p>
                <p className="text-xl font-bold">{qa.ambiguous_bases.sequences_affected}</p>
              </div>
              <div>
                <p className="text-sm text-zinc-400">Percentage</p>
                <p className="text-xl font-bold">{qa.ambiguous_bases.percentage.toFixed(2)}%</p>
              </div>
            </div>
          </Card>
        )}

        {qa.gaps && (
          <Card className="card-spacing">
            <h3 className="text-lg font-semibold mb-5">Gaps</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-zinc-400">Total Count</p>
                <p className="text-xl font-bold">{qa.gaps.total_count}</p>
              </div>
              <div>
                <p className="text-sm text-zinc-400">Sequences Affected</p>
                <p className="text-xl font-bold">{qa.gaps.sequences_affected}</p>
              </div>
              <div>
                <p className="text-sm text-zinc-400">Percentage</p>
                <p className="text-xl font-bold">{qa.gaps.percentage.toFixed(2)}%</p>
              </div>
            </div>
          </Card>
        )}

        {qa.issues && qa.issues.length > 0 && (
          <Card className="card-spacing">
            <h3 className="text-lg font-semibold mb-5">Detected Issues</h3>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {qa.issues.map((issue: any, idx: number) => (
                <div key={idx} className="p-3 bg-zinc-800 rounded border border-zinc-700">
                  <p className="text-sm font-medium text-zinc-300">
                    Sequence {issue.sequence_index + 1}
                  </p>
                  <ul className="mt-2 space-y-1">
                    {issue.problems.map((problem: string, pIdx: number) => (
                      <li key={pIdx} className="text-sm text-zinc-400 ml-4 list-disc">
                        {problem}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    );
  };

  const renderMissingData = () => {
    if (!analysis?.missing_data && !analysis?.column_info?.missing_values) {
      return null;
    }

    const missingData = analysis.missing_data;
    const missingValues = analysis.column_info?.missing_values;

    return (
      <Card className="card-spacing">
        <h3 className="text-lg font-semibold mb-5">Missing Data Analysis</h3>
        
        {missingData && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            {missingData.empty_sequences > 0 && (
              <div>
                <p className="text-sm text-zinc-400">Empty Sequences</p>
                <p className="text-xl font-bold text-red-500">{missingData.empty_sequences}</p>
              </div>
            )}
            {missingData.sequences_with_all_N > 0 && (
              <div>
                <p className="text-sm text-zinc-400">All N Sequences</p>
                <p className="text-xl font-bold text-red-500">{missingData.sequences_with_all_N}</p>
              </div>
            )}
            {missingData.sequences_mostly_gaps > 0 && (
              <div>
                <p className="text-sm text-zinc-400">Mostly Gaps</p>
                <p className="text-xl font-bold text-yellow-500">{missingData.sequences_mostly_gaps}</p>
              </div>
            )}
          </div>
        )}

        {missingValues && Object.keys(missingValues).length > 0 && (
          <div>
            <h4 className="text-md font-medium mb-3">Missing Values by Column</h4>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {Object.entries(missingValues).map(([col, info]: [string, any]) => (
                <div key={col} className="flex items-center justify-between p-2 bg-zinc-800 rounded">
                  <span className="text-sm font-medium">{col}</span>
                  <div className="flex items-center gap-4">
                    <span className="text-sm text-zinc-400">{info.count} missing</span>
                    <span className="text-sm font-bold text-yellow-500">
                      {info.percentage.toFixed(1)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>
    );
  };

  const renderRecommendations = () => {
    if (!analysis?.recommendations || analysis.recommendations.length === 0) {
      return null;
    }

    return (
      <Card className="card-spacing">
        <h3 className="text-lg font-semibold mb-5">Recommendations</h3>
        <ul className="space-y-2">
          {analysis.recommendations.map((rec, idx) => (
            <li key={idx} className="flex items-start gap-3">
              <span className="text-blue-500 mt-1">•</span>
              <span className="text-sm text-zinc-300">{rec}</span>
            </li>
          ))}
        </ul>
      </Card>
    );
  };

  const renderDetailedAnalysis = () => {
    if (!analysis?.column_info && !analysis?.detailed_stats) {
      return (
        <Card>
          <p className="text-zinc-400">Detailed analysis not available.</p>
        </Card>
      );
    }

    return (
      <div className="gap-section flex flex-col">
        {/* Column Information */}
        {analysis?.column_info && (
          <Card className="card-spacing">
            <h3 className="text-lg font-semibold mb-5">Column Analysis</h3>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b border-zinc-700">
                    <th className="text-left py-3 px-4 font-semibold text-zinc-300">Column</th>
                    <th className="text-left py-3 px-4 font-semibold text-zinc-300">Type</th>
                    <th className="text-left py-3 px-4 font-semibold text-zinc-300">Non-Null Count</th>
                    <th className="text-left py-3 px-4 font-semibold text-zinc-300">Missing %</th>
                    <th className="text-left py-3 px-4 font-semibold text-zinc-300">Unique Values</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(analysis.column_info.data_types || {}).map(([col, type]) => (
                    <tr key={col} className="border-b border-zinc-800 hover:bg-zinc-800/30">
                      <td className="py-3 px-4 font-medium">{col}</td>
                      <td className="py-3 px-4 text-zinc-400">{type as string}</td>
                      <td className="py-3 px-4 text-zinc-400">
                        {analysis.column_info.non_null_counts?.[col] || 'N/A'}
                      </td>
                      <td className="py-3 px-4 text-zinc-400">
                        {analysis.column_info.missing_values?.[col]?.percentage?.toFixed(1) || '0'}%
                      </td>
                      <td className="py-3 px-4 text-zinc-400">
                        {analysis.column_info.unique_counts?.[col] || 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}

        {/* Data Sample Preview */}
        <Card className="card-spacing">
          <h3 className="text-lg font-semibold mb-5">Data Sample Preview</h3>
          <div className="p-4 bg-zinc-800 rounded-lg mb-4">
            <p className="text-sm text-zinc-400 mb-2">
              Preview of the first few {dataset?.dataset_type === 'fasta' ? 'sequences' : 'rows'} in your dataset
            </p>
            <div className="text-xs text-zinc-500 font-mono bg-zinc-900 p-3 rounded overflow-x-auto">
              {dataset?.dataset_type === 'fasta' ? (
                <>
                  &gt;Sample_Sequence_1<br/>
                  ATCGATCGATCGATCGATCGATCGATCG...<br/>
                  &gt;Sample_Sequence_2<br/>
                  GCTAGCTAGCTAGCTAGCTAGCTAGCTA...<br/>
                  &gt;Sample_Sequence_3<br/>
                  TTAATTAATTAATTAATTAATTAATTAA...
                </>
              ) : (
                <>
                  Column1,Column2,Column3,...<br/>
                  Value1,Value2,Value3,...<br/>
                  Value4,Value5,Value6,...<br/>
                  Value7,Value8,Value9,...
                </>
              )}
            </div>
          </div>
        </Card>

        {/* Statistical Summary */}
        {analysis?.detailed_stats && (
          <Card className="card-spacing">
            <h3 className="text-lg font-semibold mb-5">Statistical Summary</h3>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b border-zinc-700">
                    <th className="text-left py-3 px-4 font-semibold text-zinc-300">Column</th>
                    <th className="text-left py-3 px-4 font-semibold text-zinc-300">Mean</th>
                    <th className="text-left py-3 px-4 font-semibold text-zinc-300">Std Dev</th>
                    <th className="text-left py-3 px-4 font-semibold text-zinc-300">Min</th>
                    <th className="text-left py-3 px-4 font-semibold text-zinc-300">25%</th>
                    <th className="text-left py-3 px-4 font-semibold text-zinc-300">50%</th>
                    <th className="text-left py-3 px-4 font-semibold text-zinc-300">75%</th>
                    <th className="text-left py-3 px-4 font-semibold text-zinc-300">Max</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(analysis.detailed_stats).map(([col, stats]: [string, any]) => (
                    <tr key={col} className="border-b border-zinc-800 hover:bg-zinc-800/30">
                      <td className="py-3 px-4 font-medium">{col}</td>
                      <td className="py-3 px-4 text-zinc-400">{stats.mean?.toFixed(3) || 'N/A'}</td>
                      <td className="py-3 px-4 text-zinc-400">{stats.std?.toFixed(3) || 'N/A'}</td>
                      <td className="py-3 px-4 text-zinc-400">{stats.min?.toFixed(3) || 'N/A'}</td>
                      <td className="py-3 px-4 text-zinc-400">{stats['25%']?.toFixed(3) || 'N/A'}</td>
                      <td className="py-3 px-4 text-zinc-400">{stats['50%']?.toFixed(3) || 'N/A'}</td>
                      <td className="py-3 px-4 text-zinc-400">{stats['75%']?.toFixed(3) || 'N/A'}</td>
                      <td className="py-3 px-4 text-zinc-400">{stats.max?.toFixed(3) || 'N/A'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}

        {/* Distribution Analysis */}
        {analysis?.distribution_analysis && (
          <Card className="card-spacing">
            <h3 className="text-lg font-semibold mb-5">Distribution Analysis</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(analysis.distribution_analysis).map(([col, dist]: [string, any]) => (
                <div key={col} className="p-4 bg-zinc-800 rounded-lg">
                  <h4 className="font-medium mb-3">{col}</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-zinc-400">Skewness:</span>
                      <span className={`font-medium ${Math.abs(dist.skewness) > 1 ? 'text-yellow-500' : 'text-green-500'}`}>
                        {dist.skewness?.toFixed(3) || 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-400">Kurtosis:</span>
                      <span className={`font-medium ${Math.abs(dist.kurtosis) > 3 ? 'text-yellow-500' : 'text-green-500'}`}>
                        {dist.kurtosis?.toFixed(3) || 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-400">Distribution:</span>
                      <span className="font-medium text-blue-400">
                        {dist.distribution_type || 'Unknown'}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Outlier Analysis */}
        {analysis?.outlier_analysis && (
          <Card className="card-spacing">
            <h3 className="text-lg font-semibold mb-5">Outlier Detection</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(analysis.outlier_analysis).map(([col, outliers]: [string, any]) => (
                <div key={col} className="p-4 bg-zinc-800 rounded-lg">
                  <h4 className="font-medium mb-3">{col}</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-zinc-400">Total Outliers:</span>
                      <span className={`font-medium ${outliers.count > 0 ? 'text-yellow-500' : 'text-green-500'}`}>
                        {outliers.count}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-400">Percentage:</span>
                      <span className={`font-medium ${outliers.percentage > 5 ? 'text-red-500' : 'text-green-500'}`}>
                        {outliers.percentage?.toFixed(2)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-400">Method:</span>
                      <span className="font-medium text-blue-400">
                        {outliers.method || 'IQR'}
                      </span>
                    </div>
                  </div>
                  {outliers.values && outliers.values.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-zinc-700">
                      <span className="text-zinc-400 text-xs">Sample outliers:</span>
                      <div className="mt-1 text-xs text-zinc-300 max-h-20 overflow-y-auto">
                        {outliers.values.slice(0, 5).map((val: number, idx: number) => (
                          <div key={idx}>{val.toFixed(3)}</div>
                        ))}
                        {outliers.values.length > 5 && (
                          <div className="text-zinc-500">... and {outliers.values.length - 5} more</div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    );
  };

  const renderCorrelationAnalysis = () => {
    if (!analysis?.correlation_analysis) {
      return (
        <Card>
          <p className="text-zinc-400">Correlation analysis not available for this dataset type.</p>
        </Card>
      );
    }

    const corr = analysis.correlation_analysis;

    return (
      <div className="gap-section flex flex-col">
        {/* High Correlations */}
        {corr.high_correlations && corr.high_correlations.length > 0 && (
          <Card className="card-spacing">
            <h3 className="text-lg font-semibold mb-5">High Correlations (|r| {'>'} 0.7)</h3>
            <div className="space-y-3">
              {corr.high_correlations.map((pair: any, idx: number) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-zinc-800 rounded-lg">
                  <div className="flex items-center gap-3">
                    <span className="font-medium">{pair.feature1}</span>
                    <span className="text-zinc-400">↔</span>
                    <span className="font-medium">{pair.feature2}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`font-bold ${
                      Math.abs(pair.correlation) > 0.9 ? 'text-red-500' : 
                      Math.abs(pair.correlation) > 0.8 ? 'text-yellow-500' : 'text-blue-500'
                    }`}>
                      {pair.correlation.toFixed(3)}
                    </span>
                    <span className="text-xs text-zinc-400">
                      {Math.abs(pair.correlation) > 0.9 ? 'Very High' : 
                       Math.abs(pair.correlation) > 0.8 ? 'High' : 'Moderate'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Correlation Matrix Summary */}
        {corr.matrix_summary && (
          <Card className="card-spacing">
            <h3 className="text-lg font-semibold mb-5">Correlation Matrix Summary</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-zinc-800 rounded-lg text-center">
                <p className="text-2xl font-bold text-red-500">{corr.matrix_summary.high_correlations}</p>
                <p className="text-sm text-zinc-400">High Correlations</p>
                <p className="text-xs text-zinc-500">(|r| {'>'} 0.7)</p>
              </div>
              <div className="p-4 bg-zinc-800 rounded-lg text-center">
                <p className="text-2xl font-bold text-yellow-500">{corr.matrix_summary.moderate_correlations}</p>
                <p className="text-sm text-zinc-400">Moderate Correlations</p>
                <p className="text-xs text-zinc-500">(0.3 &lt; |r| &lt; 0.7)</p>
              </div>
              <div className="p-4 bg-zinc-800 rounded-lg text-center">
                <p className="text-2xl font-bold text-green-500">{corr.matrix_summary.low_correlations}</p>
                <p className="text-sm text-zinc-400">Low Correlations</p>
                <p className="text-xs text-zinc-500">(|r| &lt; 0.3)</p>
              </div>
            </div>
          </Card>
        )}

        {/* Feature Relationships */}
        {corr.feature_relationships && Object.keys(corr.feature_relationships).length > 0 && (
          <Card className="card-spacing">
            <h3 className="text-lg font-semibold mb-5">Feature Relationships</h3>
            <div className="space-y-4">
              {Object.entries(corr.feature_relationships).map(([feature, relationships]: [string, any]) => (
                <div key={feature} className="p-4 bg-zinc-800 rounded-lg">
                  <h4 className="font-medium mb-3">{feature}</h4>
                  <div className="space-y-2">
                    {relationships.strongest_positive && (
                      <div className="flex justify-between text-sm">
                        <span className="text-green-400">Strongest Positive:</span>
                        <span>{relationships.strongest_positive.feature} ({relationships.strongest_positive.correlation.toFixed(3)})</span>
                      </div>
                    )}
                    {relationships.strongest_negative && (
                      <div className="flex justify-between text-sm">
                        <span className="text-red-400">Strongest Negative:</span>
                        <span>{relationships.strongest_negative.feature} ({relationships.strongest_negative.correlation.toFixed(3)})</span>
                      </div>
                    )}
                    <div className="flex justify-between text-sm">
                      <span className="text-zinc-400">Avg Correlation:</span>
                      <span>{relationships.average_correlation?.toFixed(3) || 'N/A'}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    );
  };

  const renderVisualizations = () => {
    if (!visualizations?.plots) {
      return (
        <Card>
          <p className="text-zinc-400">No visualizations available.</p>
        </Card>
      );
    }

    return (
      <div className="gap-section flex flex-col">
        {Object.entries(visualizations.plots).map(([plotName, plotData]) => (
          <Card key={plotName} className="card-spacing">
            <h3 className="text-lg font-semibold mb-5 capitalize">
              {plotName.replace(/_/g, ' ')}
            </h3>
            {visualizations.plot_descriptions?.[plotName] && (
              <p className="text-sm text-zinc-400 mb-4">
                {visualizations.plot_descriptions[plotName]}
              </p>
            )}
            <div className="bg-white rounded-lg p-4">
              <img
                src={`data:image/png;base64,${plotData}`}
                alt={plotName}
                className="w-full h-auto"
              />
            </div>
          </Card>
        ))}
      </div>
    );
  };

  if (loading) {
    return (
      <>
        <Header />
        <div className="min-h-screen bg-black flex-center-col">
          <div className="text-center-wrapper">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-white mb-4"></div>
            <p className="text-zinc-400">Analyzing dataset...</p>
          </div>
        </div>
      </>
    );
  }

  if (error) {
    return (
      <>
        <Header />
        <div className="min-h-screen bg-black flex-center-col p-8">
          <Card className="centered-card">
            <h2 className="text-xl font-bold text-red-500 mb-4">Error</h2>
            <p className="text-zinc-400 mb-6">{error}</p>
            <Button onClick={() => router.push('/')}>
              Back to Home
            </Button>
          </Card>
        </div>
      </>
    );
  }

  return (
    <>
      <Header />
      <div className="min-h-screen bg-gradient-to-b from-black via-zinc-950 to-black page-section">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="section-spacing text-center-wrapper">
            <Button
              variant="ghost"
              onClick={() => router.back()}
              className="mb-6 self-start"
            >
              ← Back
            </Button>
            <h1 className="text-5xl sm:text-6xl font-bold mb-6 bg-gradient-to-br from-white via-zinc-100 to-zinc-400 bg-clip-text text-transparent">Dataset Analysis</h1>
            {dataset && (
              <div className="flex items-center justify-center gap-4 text-zinc-400 flex-wrap mt-2">
                <span>{dataset.name}</span>
                <span>•</span>
                <span className="capitalize">{dataset.dataset_type}</span>
                <span>•</span>
                <span>{(dataset.file_size / 1024).toFixed(2)} KB</span>
              </div>
            )}
          </div>

          {/* Tabs */}
          <div className="flex gap-2 card-spacing border-b border-zinc-800 overflow-x-auto">
            <button
              className={`pb-3 px-4 font-medium transition-colors whitespace-nowrap ${
                activeTab === 'overview'
                  ? 'text-white border-b-2 border-white'
                  : 'text-zinc-400 hover:text-zinc-300'
              }`}
              onClick={() => setActiveTab('overview')}
            >
              Overview
            </button>
            <button
              className={`pb-3 px-4 font-medium transition-colors whitespace-nowrap ${
                activeTab === 'detailed'
                  ? 'text-white border-b-2 border-white'
                  : 'text-zinc-400 hover:text-zinc-300'
              }`}
              onClick={() => setActiveTab('detailed')}
            >
              Detailed Stats
            </button>
            <button
              className={`pb-3 px-4 font-medium transition-colors whitespace-nowrap ${
                activeTab === 'correlation'
                  ? 'text-white border-b-2 border-white'
                  : 'text-zinc-400 hover:text-zinc-300'
              }`}
              onClick={() => setActiveTab('correlation')}
            >
              Correlations
            </button>
            <button
              className={`pb-3 px-4 font-medium transition-colors whitespace-nowrap ${
                activeTab === 'quality'
                  ? 'text-white border-b-2 border-white'
                  : 'text-zinc-400 hover:text-zinc-300'
              }`}
              onClick={() => setActiveTab('quality')}
            >
              Quality Analysis
            </button>
            <button
              className={`pb-3 px-4 font-medium transition-colors whitespace-nowrap ${
                activeTab === 'visualizations'
                  ? 'text-white border-b-2 border-white'
                  : 'text-zinc-400 hover:text-zinc-300'
              }`}
              onClick={() => setActiveTab('visualizations')}
            >
              Visualizations
            </button>
          </div>

          {/* Tab Content */}
          {activeTab === 'overview' && (
            <div className="gap-section flex flex-col">
              {/* Dataset Health Dashboard */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 card-spacing">
                {/* Health Score */}
                <Card className="p-6 bg-gradient-to-br from-blue-900/20 to-blue-800/20 border-blue-800/30">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-semibold mb-1">Health Score</h3>
                      <p className="text-sm text-zinc-400">Overall quality</p>
                    </div>
                    <div className="text-right">
                      <div className="text-3xl font-bold mb-1">
                        {(() => {
                          let score = 100;
                          const missing = analysis?.column_info?.missing_values;
                          if (missing) {
                            const totalMissing = Object.values(missing).reduce((sum: number, info: any) => sum + info.percentage, 0);
                            const avgMissing = totalMissing / Object.keys(missing).length;
                            score -= avgMissing;
                          }
                          
                          const quality = analysis?.quality_analysis;
                          if (quality?.sequences_with_issues && quality?.total_sequences) {
                            const issueRate = (quality.sequences_with_issues / quality.total_sequences) * 100;
                            score -= issueRate;
                          }
                          
                          score = Math.max(0, Math.min(100, score));
                          const color = score >= 90 ? 'text-green-400' : score >= 70 ? 'text-yellow-400' : 'text-red-400';
                          return <span className={color}>{Math.round(score)}</span>;
                        })()}
                      </div>
                      <div className="text-xs text-zinc-400">/ 100</div>
                    </div>
                  </div>
                </Card>

                {/* Completeness */}
                <Card className="p-6 bg-gradient-to-br from-green-900/20 to-green-800/20 border-green-800/30">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-semibold mb-1">Completeness</h3>
                      <p className="text-sm text-zinc-400">Data coverage</p>
                    </div>
                    <div className="text-right">
                      <div className="text-3xl font-bold mb-1">
                        {(() => {
                          const missing = analysis?.column_info?.missing_values;
                          if (missing) {
                            const totalCells = Object.keys(missing).length * (analysis?.basic_stats?.total_rows || 1);
                            const totalMissing = Object.values(missing).reduce((sum: number, info: any) => sum + info.count, 0);
                            const completeness = ((totalCells - totalMissing) / totalCells) * 100;
                            const color = completeness >= 95 ? 'text-green-400' : completeness >= 80 ? 'text-yellow-400' : 'text-red-400';
                            return <span className={color}>{completeness.toFixed(1)}%</span>;
                          }
                          return <span className="text-green-400">100%</span>;
                        })()}
                      </div>
                      <div className="text-xs text-zinc-400">complete</div>
                    </div>
                  </div>
                </Card>

                {/* Data Consistency */}
                <Card className="p-6 bg-gradient-to-br from-purple-900/20 to-purple-800/20 border-purple-800/30">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-semibold mb-1">Consistency</h3>
                      <p className="text-sm text-zinc-400">Data uniformity</p>
                    </div>
                    <div className="text-right">
                      <div className="text-3xl font-bold mb-1">
                        {(() => {
                          const quality = analysis?.quality_analysis;
                          if (quality?.total_sequences && quality?.sequences_with_issues) {
                            const consistency = ((quality.total_sequences - quality.sequences_with_issues) / quality.total_sequences) * 100;
                            const color = consistency >= 95 ? 'text-green-400' : consistency >= 80 ? 'text-yellow-400' : 'text-red-400';
                            return <span className={color}>{consistency.toFixed(1)}%</span>;
                          }
                          return <span className="text-green-400">100%</span>;
                        })()}
                      </div>
                      <div className="text-xs text-zinc-400">consistent</div>
                    </div>
                  </div>
                </Card>
              </div>

              <h2 className="text-2xl font-semibold mb-6">Dataset Overview</h2>
              {renderBasicStats()}

              {/* Quick Insights */}
              <Card className="p-6 bg-zinc-900/50 border-zinc-700 card-spacing">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Lightbulb className="w-5 h-5 text-blue-400" />
                  Quick Insights
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {analysis?.basic_stats?.total_rows && (
                    <div className="p-3 bg-zinc-800 rounded-lg">
                      <div className="text-sm text-zinc-400 mb-1">Dataset Size</div>
                      <div className="font-medium">
                        {analysis.basic_stats.total_rows < 1000 ? 'Small dataset - Consider data augmentation' :
                         analysis.basic_stats.total_rows < 10000 ? 'Medium dataset - Good for most ML tasks' :
                         'Large dataset - Excellent for complex models'}
                      </div>
                    </div>
                  )}
                  {dataset?.dataset_type && (
                    <div className="p-3 bg-zinc-800 rounded-lg">
                      <div className="text-sm text-zinc-400 mb-1">Data Type</div>
                      <div className="font-medium capitalize">
                        {dataset.dataset_type === 'fasta' ? 'Biological sequences - Suitable for genomic analysis' :
                         'Structured data - Good for traditional ML approaches'}
                      </div>
                    </div>
                  )}
                  {analysis?.column_info?.missing_values && (
                    <div className="p-3 bg-zinc-800 rounded-lg">
                      <div className="text-sm text-zinc-400 mb-1">Data Quality</div>
                      <div className="font-medium">
                        {(() => {
                          const totalMissing = Object.values(analysis.column_info.missing_values).reduce((sum: number, info: any) => sum + info.count, 0);
                          if (totalMissing === 0) return '✅ No missing values detected';
                          if (totalMissing < 50) return 'Minor missing values - Easy to handle';
                          return 'Significant missing values - Requires preprocessing';
                        })()}
                      </div>
                    </div>
                  )}
                  {analysis?.basic_stats?.sequence_count && (
                    <div className="p-3 bg-zinc-800 rounded-lg">
                      <div className="text-sm text-zinc-400 mb-1">Sequence Complexity</div>
                      <div className="font-medium">
                        {analysis.basic_stats.avg_sequence_length < 100 ? 'Short sequences - Good for pattern analysis' :
                         analysis.basic_stats.avg_sequence_length < 1000 ? 'Medium sequences - Balanced complexity' :
                         'Long sequences - High complexity analysis'}
                      </div>
                    </div>
                  )}
                </div>
              </Card>

              {renderMissingData()}
              {renderRecommendations()}
            </div>
          )}

          {activeTab === 'detailed' && (
            <div className="gap-section flex flex-col">
              <h2 className="text-2xl font-semibold mb-6">Detailed Analysis</h2>
              {renderDetailedAnalysis()}
            </div>
          )}

          {activeTab === 'correlation' && (
            <div className="gap-section flex flex-col">
              <h2 className="text-2xl font-semibold mb-6">Correlation Analysis</h2>
              {renderCorrelationAnalysis()}
            </div>
          )}

          {activeTab === 'quality' && (
            <div className="gap-section flex flex-col">
              <h2 className="text-2xl font-semibold mb-6">Quality Metrics</h2>
              {renderQualityAnalysis()}
            </div>
          )}

          {activeTab === 'visualizations' && (
            <div className="gap-section flex flex-col">
              <h2 className="text-2xl font-semibold mb-6">Data Visualizations</h2>
              {renderVisualizations()}
            </div>
          )}

          {/* Analysis Summary & Next Steps */}
          <Card className="p-8 bg-gradient-to-r from-zinc-900 to-zinc-800 border-zinc-700 mt-8">
            <h3 className="text-2xl font-semibold mb-6 text-center">Analysis Summary & Next Steps</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
              {/* Key Findings */}
              <div>
                <h4 className="text-lg font-semibold mb-4 text-blue-400 flex items-center gap-2">
                  <Search className="w-5 h-5" />
                  Key Findings
                </h4>
                <div className="space-y-3">
                  <div className="flex items-start gap-3">
                    <span className="text-green-400 mt-1">✓</span>
                    <span className="text-sm">
                      Dataset contains {analysis?.basic_stats?.total_rows?.toLocaleString() || 'N/A'} records
                      {dataset?.dataset_type === 'fasta' && analysis?.basic_stats?.sequence_count && 
                        ` with ${analysis.basic_stats.sequence_count.toLocaleString()} sequences`
                      }
                    </span>
                  </div>
                  {analysis?.column_info?.missing_values && (
                    <div className="flex items-start gap-3">
                      <span className={`mt-1 ${
                        Object.values(analysis.column_info.missing_values).some((info: any) => info.percentage > 10) 
                          ? 'text-yellow-400' 
                          : 'text-green-400'
                      }`}>
                        {Object.values(analysis.column_info.missing_values).some((info: any) => info.percentage > 10) ? '⚠' : '✓'}
                      </span>
                      <span className="text-sm">
                        {Object.values(analysis.column_info.missing_values).some((info: any) => info.percentage > 10)
                          ? 'Some columns have significant missing values'
                          : 'Missing data is minimal and manageable'
                        }
                      </span>
                    </div>
                  )}
                  {analysis?.quality_analysis && (
                    <div className="flex items-start gap-3">
                      <span className={`mt-1 ${
                        analysis.quality_analysis.sequences_with_issues > 0 ? 'text-yellow-400' : 'text-green-400'
                      }`}>
                        {analysis.quality_analysis.sequences_with_issues > 0 ? '⚠' : '✓'}
                      </span>
                      <span className="text-sm">
                        {analysis.quality_analysis.sequences_with_issues > 0
                          ? `${analysis.quality_analysis.sequences_with_issues} sequences have quality issues`
                          : 'All sequences pass quality checks'
                        }
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Recommendations */}
              <div>
                <h4 className="text-lg font-semibold mb-4 text-green-400 flex items-center gap-2">
                  <Lightbulb className="w-5 h-5" />
                  Recommendations
                </h4>
                <div className="space-y-3">
                  {analysis?.recommendations?.slice(0, 3).map((rec, idx) => (
                    <div key={idx} className="flex items-start gap-3">
                      <span className="text-blue-400 mt-1">→</span>
                      <span className="text-sm">{rec}</span>
                    </div>
                  )) || (
                    <div className="text-sm text-zinc-400">
                      Your dataset looks good! Proceed to model configuration.
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Readiness Assessment */}
            <div className="text-center p-6 bg-zinc-800 rounded-lg mb-6 mt-6">
              <h4 className="text-lg font-semibold mb-3">ML Readiness Assessment</h4>
              <div className="text-3xl font-bold mb-2">
                {(() => {
                  const issues = [];
                  if (analysis?.column_info?.missing_values) {
                    const hasMajorMissing = Object.values(analysis.column_info.missing_values)
                      .some((info: any) => info.percentage > 20);
                    if (hasMajorMissing) issues.push('missing_data');
                  }
                  if (analysis?.quality_analysis?.sequences_with_issues > 0) {
                    issues.push('quality_issues');
                  }
                  if (analysis?.basic_stats?.total_rows < 100) {
                    issues.push('small_dataset');
                  }

                  if (issues.length === 0) {
                    return <span className="text-green-400 flex items-center gap-2"><CheckCircle2 className="w-5 h-5" /> Ready</span>;
                  } else if (issues.length <= 1) {
                    return <span className="text-yellow-400 flex items-center gap-2"><AlertTriangle className="w-5 h-5" /> Minor Issues</span>;
                  } else {
                    return <span className="text-red-400 flex items-center gap-2"><X className="w-5 h-5" /> Needs Work</span>;
                  }
                })()}
              </div>
              <p className="text-sm text-zinc-400">
                {analysis?.column_info?.missing_values && 
                 analysis?.basic_stats?.total_rows >= 100 &&
                 (!analysis?.quality_analysis?.sequences_with_issues || analysis.quality_analysis.sequences_with_issues === 0)
                  ? "Your dataset is well-prepared for machine learning!"
                  : "Consider addressing the identified issues before proceeding."
                }
              </p>
            </div>
          </Card>

          {/* Action Buttons */}
          <div className="component-spacing flex flex-col sm:flex-row gap-4 justify-center pt-6">
            <Button onClick={() => router.push(`/automl?datasetId=${datasetId}`)} size="lg" className="px-8 flex items-center gap-2">
              <Rocket className="w-4 h-4" />
              Start AutoML Training
            </Button>
            <Button variant="outline" onClick={loadAnalysisData} size="lg" className="px-8 flex items-center gap-2">
              <RotateCcw className="w-4 h-4" />
              Refresh Analysis
            </Button>
            <Button variant="ghost" onClick={() => router.push('/')} size="lg" className="px-8 flex items-center gap-2">
              <Folder className="w-4 h-4" />
              Back to Datasets
            </Button>
          </div>
        </div>
      </div>
    </>
  );
}
