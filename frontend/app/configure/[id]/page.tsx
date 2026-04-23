'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Select } from '@/components/ui/Select';
import { Header } from '@/components/Header';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/useAuth';
import { Dataset, DatasetPreview } from '@/types/api';
import { X } from 'lucide-react';

export default function ConfigurePage() {
  useAuth();
  const router = useRouter();
  const params = useParams();
  const datasetId = Number(params.id);

  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [preview, setPreview] = useState<DatasetPreview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [taskType, setTaskType] = useState('general_classification');
  const [targetColumn, setTargetColumn] = useState('label');
  const [encodingMethod, setEncodingMethod] = useState('kmer');
  const [kmerSize, setKmerSize] = useState(3);
  const [testSize, setTestSize] = useState(0.2);
  const [valSize, setValSize] = useState(0.1);
  const [optimizeHyperparams, setOptimizeHyperparams] = useState(false);
  const [nModels, setNModels] = useState(3);
  const [generateReport, setGenerateReport] = useState(true);

  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadData();
  }, [datasetId]);

  const loadData = async () => {
    try {
      const [datasetData, previewData] = await Promise.all([
        api.getDataset(datasetId),
        api.previewDataset(datasetId, 5),
      ]);

      setDataset(datasetData);
      setPreview(previewData);

      setLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dataset');
      setLoading(false);
    }
  };

  const handleStartWorkflow = async () => {
    if (!targetColumn) {
      setError('Please enter a target column');
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      const result = await api.startWorkflow({
        dataset_id: datasetId,
        task_type: taskType,
        target_column: targetColumn,
        encoding_method: encodingMethod,
        kmer_size: kmerSize,
        test_size: testSize,
        val_size: valSize,
        optimize_hyperparams: optimizeHyperparams,
        n_models: nModels,
        generate_report: generateReport,
      });

      router.push(`/running/${result.job_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start training');
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <>
        <Header />
        <div className="min-h-[calc(100vh-64px)] bg-gradient-to-b from-black via-zinc-950/90 to-black flex-center-col">
          <div className="text-center-wrapper">
            <div className="animate-spin rounded-full h-12 w-12 border-2 border-white/20 border-t-white mx-auto mb-4"></div>
            <div className="text-zinc-300 text-lg font-medium">Loading dataset...</div>
          </div>
        </div>
      </>
    );
  }

  if (!dataset || !preview) {
    return (
      <>
        <Header />
        <div className="min-h-[calc(100vh-64px)] bg-gradient-to-b from-black via-zinc-950/90 to-black flex-center-col px-4">
          <Card className="centered-card text-center">
            <X className="w-16 h-16 text-red-400 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-white mb-2">Dataset Not Found</h2>
            <p className="text-red-400 mb-6">{error || 'The requested dataset could not be loaded.'}</p>
            <Button onClick={() => router.push('/')} variant="outline">
              Return Home
            </Button>
          </Card>
        </div>
      </>
    );
  }

  return (
    <>
      <Header />
      <div className="min-h-[calc(100vh-64px)] bg-gradient-to-b from-black via-zinc-950/90 to-black">
        <div className="page-container page-section">
          <div className="section-spacing text-center-wrapper">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-6 tracking-tight bg-gradient-to-br from-white via-zinc-100 to-zinc-400 bg-clip-text text-transparent">Configure Training</h1>
            <p className="text-zinc-400 text-lg lg:text-xl max-w-3xl leading-relaxed">Set up your machine learning pipeline with custom parameters and optimization settings</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-section section-spacing">
            {/* Dataset Overview */}
            <div>
              <Card>
                <h2 className="text-2xl font-bold mb-7 text-white">Dataset Overview</h2>
              <div className="space-y-4 mb-8 mt-4">
                <div className="flex justify-between items-center py-2 border-b border-zinc-800">
                  <span className="text-zinc-400">Dataset Name</span>
                  <span className="font-medium">{dataset.name}</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-zinc-800">
                  <span className="text-zinc-400">Total Samples</span>
                  <span className="font-medium">{preview.total_rows}</span>
                </div>
                <div className="flex justify-between items-center py-2">
                  <span className="text-zinc-400">Features</span>
                  <span className="font-medium">{preview.columns?.length || (preview.preview_data.length > 0 ? Object.keys(preview.preview_data[0]).length : 0)}</span>
                </div>
              </div>

              <h3 className="text-sm font-semibold text-zinc-400 mb-4 uppercase tracking-wide">Data Preview</h3>
              <div className="overflow-x-auto -mx-8 px-8">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-zinc-800">
                      {(preview.columns || (preview.preview_data.length > 0 ? Object.keys(preview.preview_data[0]) : [])).map((col) => (
                        <th key={col} className="text-left px-3 py-3 text-zinc-400 font-medium">
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {preview.preview_data.map((row, i) => {
                      const columns = preview.columns || Object.keys(row);
                      return (
                        <tr key={i} className="border-b border-zinc-800/50">
                          {columns.map((col) => (
                            <td key={col} className="px-3 py-3 text-zinc-300">
                              {String(row[col] ?? '')}
                            </td>
                          ))}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </Card>
          </div>

          <div>
            <Card className="!p-10 lg:!p-12">
              <h2 className="text-3xl font-bold mb-8">Training Configuration</h2>

              <div className="gap-component flex flex-col">
                <Select
                  label="Task Type"
                  value={taskType}
                  onChange={(e) => setTaskType(e.target.value)}
                >
                  <option value="general_classification">General Classification</option>
                  <option value="protein_classification">Protein Classification</option>
                  <option value="dna_classification">DNA Classification</option>
                  <option value="rna_classification">RNA Classification</option>
                  <option value="gene_expression">Gene Expression Analysis</option>
                  <option value="regression">Regression</option>
                </Select>

                <div>
                  <label className="text-sm font-medium text-zinc-300 mb-3 block">
                    Target Column Name
                  </label>
                  <input
                    type="text"
                    value={targetColumn}
                    onChange={(e) => setTargetColumn(e.target.value)}
                    className="w-full px-5 py-4 bg-zinc-900 border border-zinc-800 rounded-lg focus:outline-none focus:ring-2 focus:ring-white/20 transition-all min-h-[52px]"
                    placeholder="label"
                  />
                </div>

                <Select
                  label="Encoding Method"
                  value={encodingMethod}
                  onChange={(e) => setEncodingMethod(e.target.value)}
                >
                  <option value="kmer">K-mer Encoding</option>
                  <option value="onehot">One-Hot Encoding</option>
                  <option value="integer">Integer Encoding</option>
                </Select>

                {encodingMethod === 'kmer' && (
                  <div>
                    <label className="text-sm font-medium text-zinc-300 mb-3 block">
                      K-mer Size: <span className="text-white font-bold">{kmerSize}</span>
                    </label>
                    <input
                      type="range"
                      min="2"
                      max="6"
                      value={kmerSize}
                      onChange={(e) => setKmerSize(parseInt(e.target.value))}
                      className="w-full"
                      aria-label="K-mer size slider"
                    />
                    <div className="flex justify-between text-xs text-zinc-500 mt-1">
                      <span>2</span>
                      <span>6</span>
                    </div>
                  </div>
                )}

                <div>
                  <label className="text-sm font-medium text-zinc-300 mb-3 block">
                    Number of Models: <span className="text-white font-bold">{nModels}</span>
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="9"
                    value={nModels}
                    onChange={(e) => setNModels(parseInt(e.target.value))}
                    className="w-full"
                    aria-label="Number of models slider"
                  />
                  <div className="flex justify-between text-xs text-zinc-500 mt-1">
                    <span>1</span>
                    <span>9</span>
                  </div>
                  <p className="text-xs text-zinc-500 mt-2">
                    AutoML will evaluate and train the top {nModels} models
                  </p>
                </div>

                <details className="border border-zinc-800 rounded-xl overflow-hidden">
                  <summary className="cursor-pointer p-4 text-sm font-semibold hover:bg-zinc-900/50 transition-colors">
                    Advanced Options
                  </summary>
                  <div className="p-4 pt-2 space-y-4 bg-zinc-950/30">
                    <div>
                      <label className="text-sm font-medium text-zinc-300 mb-3 block">
                        Test Split: <span className="text-white font-bold">{(testSize * 100).toFixed(0)}%</span>
                      </label>
                      <input
                        type="range"
                        min="0.1"
                        max="0.3"
                        step="0.05"
                        value={testSize}
                        onChange={(e) => setTestSize(parseFloat(e.target.value))}
                        className="w-full"
                        aria-label="Test split slider"
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium text-zinc-300 mb-3 block">
                        Validation Split: <span className="text-white font-bold">{(valSize * 100).toFixed(0)}%</span>
                      </label>
                      <input
                        type="range"
                        min="0.05"
                        max="0.2"
                        step="0.05"
                        value={valSize}
                        onChange={(e) => setValSize(parseFloat(e.target.value))}
                        className="w-full"
                        aria-label="Validation split slider"
                      />
                    </div>
                    <label className="flex items-center gap-3 cursor-pointer p-4 rounded-lg hover:bg-zinc-900/50 transition-colors">
                      <input
                        type="checkbox"
                        checked={optimizeHyperparams}
                        onChange={(e) => setOptimizeHyperparams(e.target.checked)}
                        className="w-5 h-5"
                      />
                      <span className="text-sm">Optimize Hyperparameters (takes longer, better results)</span>
                    </label>
                    <label className="flex items-center gap-3 cursor-pointer p-4 rounded-lg hover:bg-zinc-900/50 transition-colors">
                      <input
                        type="checkbox"
                        checked={generateReport}
                        onChange={(e) => setGenerateReport(e.target.checked)}
                        className="w-5 h-5"
                      />
                      <span className="text-sm">Generate PDF Report</span>
                    </label>
                  </div>
                </details>
              </div>

              {error && (
                <div className="mt-6 mb-4 p-5 bg-red-950/30 border border-red-800/50 rounded-xl text-red-400 text-sm">
                  {error}
                </div>
              )}

              <div className="mt-8 flex gap-4 pt-6">
                <Button variant="secondary" onClick={() => router.push('/')} size="lg">
                  Back
                </Button>
                <Button
                  onClick={handleStartWorkflow}
                  disabled={!targetColumn || submitting}
                  className="flex-1"
                  size="lg"
                >
                  {submitting ? 'Starting Training...' : 'Run Analysis'}
                </Button>
              </div>
            </Card>
          </div>
          </div>
        </div>
      </div>
    </>
  );
}
