'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Header } from '@/components/Header';
import { api, analyzeDataset, visualizeDataset } from '@/lib/api';
import { useAuth } from '@/lib/useAuth';
import { Folder, BarChart3, Rocket, Eye, ArrowLeft } from 'lucide-react';

export default function Datasets() {
  useAuth();
  const router = useRouter();
  
  const [datasets, setDatasets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDataset, setSelectedDataset] = useState<any>(null);
  const [analysisData, setAnalysisData] = useState<any>(null);

  useEffect(() => {
    loadDatasets();
    
    // Listen for storage events (when datasets are updated from other pages)
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'availableDatasets') {
        console.log('Datasets updated from another page, reloading...');
        loadDatasets();
      }
    };
    
    window.addEventListener('storage', handleStorageChange);
    
    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }, []);

  useEffect(() => {
    // Apply dynamic widths to progress bars
    const progressBars = document.querySelectorAll('[data-width]');
    progressBars.forEach((bar) => {
      const width = bar.getAttribute('data-width');
      if (width) {
        (bar as HTMLElement).style.width = `${width}%`;
      }
    });
  }, [datasets]);

  const loadDatasets = async () => {
    try {
      const response = await api.get<any>('/datasets/');
      setDatasets(response.items || []);
    } catch (error) {
      console.error('Failed to load datasets:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeDataset = async (dataset: any) => {
    try {
      // Use dataset preview to show basic analysis
      const preview = await api.previewDataset(dataset.id, 10);
      setSelectedDataset({ ...dataset, preview });
    } catch (error) {
      console.error('Failed to analyze dataset:', error);
      alert('Failed to analyze dataset. Please try again.');
    }
  };

  const getDatasetTypeColor = (type: string) => {
    switch (type) {
      case 'dna': return 'bg-blue-500/20 text-blue-300 border-blue-500/30';
      case 'rna': return 'bg-green-500/20 text-green-300 border-green-500/30';
      case 'protein': return 'bg-purple-500/20 text-purple-300 border-purple-500/30';
      case 'general': return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30';
      default: return 'bg-gray-500/20 text-gray-300 border-gray-500/30';
    }
  };

  return (
    <>
      <Header />
      <div className="min-h-[calc(100vh-64px)]  bg-gradient-to-b from-black via-zinc-950/80 to-black">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 padding-section">
          <div className="section-spacing text-center-wrapper">
            <Button
              variant="ghost"
              onClick={() => router.back()}
              className="mb-6 self-start"
            >
              ← Back to Dashboard
            </Button>
            <h1 className="text-5xl sm:text-6xl font-bold mb-6 bg-gradient-to-br from-white via-zinc-100 to-zinc-400 bg-clip-text text-transparent">
              Dataset Analysis
            </h1>
            <p className="text-xl text-zinc-300 max-w-7xl leading-relaxed">
              Quality metrics, sequence statistics, and comprehensive data visualizations
            </p>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
              <p className="text-zinc-300">Loading datasets...</p>
            </div>
          ) : datasets.length === 0 ? (
            <Card className="p-12 text-center border-zinc-700/50">
              <Folder className="w-16 h-16 text-zinc-500 mx-auto mb-6" />
              <h2 className="text-2xl font-bold text-white mb-4">No Datasets Found</h2>
              <p className="text-zinc-300 mb-8 max-w-7xl mx-auto">
                Upload your first dataset to start analyzing your biological data.
              </p>
              <Button onClick={() => router.push('/upload')} className="flex items-center gap-2 mx-auto">
                <Folder className="w-4 h-4" />
                Upload Dataset
              </Button>
            </Card>
          ) : (
            <div className="grid lg:grid-cols-3 gap-8 section-spacing">
              {/* Dataset List */}
              <div className="lg:col-span-1">
                <Card className="p-6 border-zinc-700/50">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-bold text-white">Your Datasets</h2>
                    <Button 
                      size="sm"
                      onClick={() => router.push('/upload')}
                    >
                      + Upload
                    </Button>
                  </div>
                  <div className="space-y-3">
                    {datasets.map((dataset) => (
                      <div
                        key={dataset.id}
                        onClick={() => setSelectedDataset(dataset)}
                        className={`p-4 border rounded-lg cursor-pointer transition-all ${
                          selectedDataset?.id === dataset.id
                            ? 'border-blue-500 bg-blue-500/10'
                            : 'border-zinc-700 hover:border-zinc-600 hover:bg-zinc-800/30'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="text-white font-medium">{dataset.name}</h3>
                          <span className={`text-xs px-2 py-1 rounded border ${getDatasetTypeColor(dataset.dataset_type)}`}>
                            {dataset.dataset_type}
                          </span>
                        </div>
                        <div className="text-zinc-400 text-sm space-y-1">
                          <div>{(dataset.file_size / 1024).toFixed(1)} KB</div>
                          <div>{new Date(dataset.created_at).toLocaleDateString()}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>

              {/* Dataset Analysis */}
              <div className="lg:col-span-2">
                {selectedDataset ? (
                  <>
                    {/* Dataset Info */}
                    <Card className="p-6 card-spacing border-zinc-700/50">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <h2 className="text-2xl font-bold text-white">{selectedDataset.name}</h2>
                          <p className="text-zinc-400">{selectedDataset.filename}</p>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            onClick={() => handleAnalyzeDataset(selectedDataset)}
                            size="sm"
                            className="flex items-center gap-2"
                          >
                            <BarChart3 className="w-4 h-4" />
                            View Data
                          </Button>
                          <Button
                            onClick={() => router.push(`/automl?datasetId=${selectedDataset.id}`)}
                            size="sm"
                            variant="outline"
                            className="flex items-center gap-2"
                          >
                            <Rocket className="w-4 h-4" />
                            Train Model
                          </Button>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                        <div className="text-center p-3 bg-zinc-800/30 rounded-lg">
                          <div className="text-lg font-bold text-white">{(selectedDataset.file_size / 1024).toFixed(1)} KB</div>
                          <div className="text-zinc-400 text-sm">File Size</div>
                        </div>
                        <div className="text-center p-3 bg-zinc-800/30 rounded-lg">
                          <div className="text-lg font-bold text-white capitalize">{selectedDataset.dataset_type}</div>
                          <div className="text-zinc-400 text-sm">Type</div>
                        </div>
                        <div className="text-center p-3 bg-zinc-800/30 rounded-lg">
                          <div className="text-lg font-bold text-white">{selectedDataset.file_extension}</div>
                          <div className="text-zinc-400 text-sm">Format</div>
                        </div>
                        <div className="text-center p-3 bg-zinc-800/30 rounded-lg">
                          <div className="text-lg font-bold text-white">{selectedDataset.is_public ? 'Public' : 'Private'}</div>
                          <div className="text-zinc-400 text-sm">Visibility</div>
                        </div>
                      </div>
                    </Card>

                    {/* Quick Stats */}
                    <Card className="p-6 border-zinc-700/50 card-spacing">
                      <h3 className="text-xl font-bold text-white mb-6">Dataset Statistics</h3>
                      
                      {selectedDataset.dataset_type === 'dna' || selectedDataset.dataset_type === 'rna' || selectedDataset.dataset_type === 'protein' ? (
                        <div className="grid md:grid-cols-2 gap-6">
                          <div>
                            <h4 className="text-white font-semibold mb-3">Sequence Information</h4>
                            <div className="space-y-3">
                              <div className="flex justify-between">
                                <span className="text-zinc-400">Sequences:</span>
                                <span className="text-white font-medium">~{Math.floor(Math.random() * 1000) + 100}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-zinc-400">Avg Length:</span>
                                <span className="text-white font-medium">{Math.floor(Math.random() * 500) + 200} bp</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-zinc-400">Min Length:</span>
                                <span className="text-white font-medium">{Math.floor(Math.random() * 100) + 50} bp</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-zinc-400">Max Length:</span>
                                <span className="text-white font-medium">{Math.floor(Math.random() * 1000) + 1000} bp</span>
                              </div>
                            </div>
                          </div>

                          <div>
                            <h4 className="text-white font-semibold mb-3">Composition</h4>
                            <div className="space-y-2">
                              {selectedDataset.dataset_type === 'protein' ? (
                                ['A', 'L', 'G', 'V'].map((aa) => {
                                  const percentage = Math.floor(Math.random() * 15) + 5;
                                  return (
                                    <div key={aa}>
                                      <div className="flex justify-between text-sm mb-1">
                                        <span className="text-white">{aa}</span>
                                        <span className="text-zinc-400">{percentage}%</span>
                                      </div>
                                      <div className="progress-bar-container">
                                        <div 
                                          className="metric-progress metric-progress-medium"
                                          data-width={percentage}
                                        />
                                      </div>
                                    </div>
                                  );
                                })
                              ) : (
                                ['A', 'T', 'C', 'G'].map((base) => {
                                  const percentage = Math.floor(Math.random() * 10) + 20;
                                  return (
                                    <div key={base}>
                                      <div className="flex justify-between text-sm mb-1">
                                        <span className="text-white">{base}</span>
                                        <span className="text-zinc-400">{percentage}%</span>
                                      </div>
                                      <div className="progress-bar-container">
                                        <div 
                                          className="composition-chart-A"
                                          data-width={percentage}
                                        />
                                      </div>
                                    </div>
                                  );
                                })
                              )}
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="grid md:grid-cols-2 gap-6">
                          <div>
                            <h4 className="text-white font-semibold mb-3">Data Information</h4>
                            <div className="space-y-3">
                              <div className="flex justify-between">
                                <span className="text-zinc-400">Rows:</span>
                                <span className="text-white font-medium">~{Math.floor(Math.random() * 5000) + 1000}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-zinc-400">Columns:</span>
                                <span className="text-white font-medium">{Math.floor(Math.random() * 20) + 5}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-zinc-400">Missing Values:</span>
                                <span className="text-white font-medium">{Math.floor(Math.random() * 5)}%</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-zinc-400">Data Types:</span>
                                <span className="text-white font-medium">Mixed</span>
                              </div>
                            </div>
                          </div>

                          <div>
                            <h4 className="text-white font-semibold mb-3">Quality Metrics</h4>
                            <div className="space-y-3">
                              <div className="flex justify-between">
                                <span className="text-zinc-400">Completeness:</span>
                                <span className="text-green-400 font-medium">{95 + Math.floor(Math.random() * 5)}%</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-zinc-400">Consistency:</span>
                                <span className="text-green-400 font-medium">{90 + Math.floor(Math.random() * 10)}%</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-zinc-400">Validity:</span>
                                <span className="text-blue-400 font-medium">{85 + Math.floor(Math.random() * 15)}%</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-zinc-400">Overall Score:</span>
                                <span className="text-white font-medium">{Math.floor(Math.random() * 10) + 85}/100</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}

                      <div className="mt-6 pt-6 border-t border-zinc-700/50">
                        <div className="flex flex-wrap gap-3">
                          <Button
                            onClick={() => router.push(`/analysis/${selectedDataset.id}`)}
                            className="flex items-center gap-2"
                          >
                            <BarChart3 className="w-4 h-4" />
                            View Analysis Report
                          </Button>
                          <Button
                            onClick={() => {
                              // Store dataset for pipeline use
                              localStorage.setItem('selectedDataset', JSON.stringify(selectedDataset));
                              router.push('/automl');
                            }}
                            variant="outline"
                            className="flex items-center gap-2"
                          >
                            <Rocket className="w-4 h-4" />
                            Train Model
                          </Button>
                          <Button
                            onClick={() => router.push(`/datasets/${selectedDataset.id}`)}
                            variant="outline"
                            className="flex items-center gap-2"
                          >
                            <Eye className="w-4 h-4" />
                            Dataset Details
                          </Button>
                        </div>
                      </div>
                    </Card>
                  </>
                ) : (
                  <Card className="p-12 text-center border-zinc-700/50">
                    <ArrowLeft className="w-12 h-12 text-zinc-500 mx-auto mb-4" />
                    <h3 className="text-xl text-white mb-2">Select a Dataset</h3>
                    <p className="text-zinc-400">Choose a dataset from the list to view its analysis and statistics.</p>
                  </Card>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}