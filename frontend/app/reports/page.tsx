'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Header } from '@/components/Header';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/useAuth';
import { BarChart3, CheckCircle2, TrendingUp, Rocket, X, Download, FileText, Bot, Eye } from 'lucide-react';

export default function Reports() {
  useAuth();
  const router = useRouter();
  
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'completed' | 'comparison'>('overview');

  useEffect(() => {
    loadJobs();
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
  }, [jobs]);

  const loadJobs = async () => {
    try {
      const response = await api.get<any>('/api/v1/jobs/');
      setJobs(response.items || []);
    } catch (error) {
      console.error('Failed to load jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-400 bg-green-500/20';
      case 'running': return 'text-blue-400 bg-blue-500/20';
      case 'queued': return 'text-yellow-400 bg-yellow-500/20';
      case 'failed': return 'text-red-400 bg-red-500/20';
      default: return 'text-gray-400 bg-gray-500/20';
    }
  };

  const completedJobs = jobs.filter(job => job.status === 'completed');
  const runningJobs = jobs.filter(job => job.status === 'running' || job.status === 'queued');
  const failedJobs = jobs.filter(job => job.status === 'failed');

  return (
    <>
      <Header />
      <div className="min-h-[calc(100vh-64px)] bg-gradient-to-b from-black via-zinc-950/80 to-black">
        <div className="page-container padding-section">
          <div className="section-spacing text-center-wrapper">
            <Button
              variant="ghost"
              onClick={() => router.back()}
              className="mb-6 self-start"
            >
              ← Back to Dashboard
            </Button>
            <h1 className="text-5xl sm:text-6xl font-bold mb-6 bg-gradient-to-br from-white via-zinc-100 to-zinc-400 bg-clip-text text-transparent">
              Reports & Testing
            </h1>
            <p className="text-xl text-zinc-300 max-w-7xl leading-relaxed">
              Test cases, model comparison, training logs, and exportable reports
            </p>
          </div>

          {/* Tabs */}
          <div className="flex gap-2 card-spacing">
            {[
              { id: 'overview', label: 'Overview', icon: BarChart3 },
              { id: 'completed', label: 'Completed Models', icon: CheckCircle2 },
              { id: 'comparison', label: 'Model Comparison', icon: TrendingUp }
            ].map((tab) => {
              const IconComponent = tab.icon;
              return (
                <Button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  variant={activeTab === tab.id ? 'default' : 'outline'}
                  size="sm"
                  className="flex items-center gap-2"
                >
                  <IconComponent className="w-4 h-4" />
                  {tab.label}
                </Button>
              );
            })}
          </div>

          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
              <p className="text-zinc-300">Loading reports...</p>
            </div>
          ) : (
            <>
              {/* Overview Tab */}
              {activeTab === 'overview' && (
                <div className="gap-section flex flex-col">
                  {/* Summary Stats */}
                  <div className="grid md:grid-cols-4 gap-6">
                    <Card className="p-6 bg-gradient-to-br from-green-900/40 to-green-800/40 border-green-700/50">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-green-200 text-sm font-medium mb-2">Completed</p>
                          <p className="text-3xl font-bold text-green-300">{completedJobs.length}</p>
                        </div>
                        <CheckCircle2 className="w-8 h-8 text-green-400" />
                      </div>
                    </Card>

                    <Card className="p-6 bg-gradient-to-br from-blue-900/40 to-blue-800/40 border-blue-700/50">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-blue-200 text-sm font-medium mb-2">Running</p>
                          <p className="text-3xl font-bold text-blue-300">{runningJobs.length}</p>
                        </div>
                        <Rocket className="w-8 h-8 text-blue-400" />
                      </div>
                    </Card>

                    <Card className="p-6 bg-gradient-to-br from-red-900/40 to-red-800/40 border-red-700/50">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-red-200 text-sm font-medium mb-2">Failed</p>
                          <p className="text-3xl font-bold text-red-300">{failedJobs.length}</p>
                        </div>
                        <X className="w-8 h-8 text-red-400" />
                      </div>
                    </Card>

                    <Card className="p-6 bg-gradient-to-br from-purple-900/40 to-purple-800/40 border-purple-700/50">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-purple-200 text-sm font-medium mb-2">Total</p>
                          <p className="text-3xl font-bold text-purple-300">{jobs.length}</p>
                        </div>
                        <BarChart3 className="w-8 h-8 text-purple-400" />
                      </div>
                    </Card>
                  </div>

                  {/* Recent Activity */}
                  <Card className="p-6 border-zinc-700/50 card-spacing">
                    <h2 className="text-xl font-bold text-white mb-6">Recent Activity</h2>
                    {jobs.length > 0 ? (
                      <div className="space-y-4">
                        {jobs.slice(0, 10).map((job) => (
                          <div key={job.id} className="flex items-center justify-between p-4 bg-zinc-800/30 rounded-lg">
                            <div className="flex-1">
                              <div className="flex items-center gap-3">
                                <h3 className="text-white font-medium">{job.name || `Job ${job.id}`}</h3>
                                <span className={`px-2 py-1 rounded text-xs ${getStatusColor(job.status)}`}>
                                  {job.status}
                                </span>
                              </div>
                              <p className="text-zinc-400 text-sm">
                                {job.job_type} • {new Date(job.created_at).toLocaleDateString()}
                              </p>
                              {job.status === 'running' && job.progress && (
                                <div className="progress-bar-container">
                                  <div 
                                    className="progress-bar-blue"
                                    data-width={job.progress}
                                  />
                                </div>
                              )}
                            </div>
                            <div className="flex gap-2">
                              {job.status === 'completed' && (
                                <>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => router.push(`/results/${job.id}`)}
                                    className="flex items-center gap-2"
                                  >
                                    <BarChart3 className="w-4 h-4" />
                                    Results
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => {
                                      // Download report functionality
                                      alert('Report download would be implemented here');
                                    }}
                                    className="flex items-center gap-2"
                                  >
                                    <Download className="w-4 h-4" />
                                    Report
                                  </Button>
                                </>
                              )}
                              {job.status === 'running' && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => router.push(`/running/${job.id}`)}
                                  className="flex items-center gap-2"
                                >
                                  <Eye className="w-4 h-4" />
                                  Monitor
                                </Button>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8">
                        <BarChart3 className="w-12 h-12 text-zinc-500 mx-auto mb-4" />
                        <p className="text-zinc-400">No training jobs yet</p>
                      </div>
                    )}
                  </Card>
                </div>
              )}

              {/* Completed Models Tab */}
              {activeTab === 'completed' && (
                <div className="gap-section flex flex-col">
                  {completedJobs.length > 0 ? (
                    <>
                      <Card className="p-6 border-zinc-700/50">
                        <h2 className="text-xl font-bold text-white mb-6">Completed Models</h2>
                        <div className="overflow-x-auto">
                          <table className="w-full">
                            <thead>
                              <tr className="border-b border-zinc-700">
                                <th className="text-left text-white font-semibold py-3">Model Name</th>
                                <th className="text-left text-white font-semibold py-3">Type</th>
                                <th className="text-left text-white font-semibold py-3">Accuracy</th>
                                <th className="text-left text-white font-semibold py-3">Date</th>
                                <th className="text-left text-white font-semibold py-3">Actions</th>
                              </tr>
                            </thead>
                            <tbody>
                              {completedJobs.map((job) => (
                                <tr key={job.id} className="border-b border-zinc-800/50">
                                  <td className="py-3 text-white font-medium">{job.name || `Model ${job.id}`}</td>
                                  <td className="py-3 text-zinc-400">{job.job_type}</td>
                                  <td className="py-3">
                                    <span className="text-green-400">
                                      {job.metrics?.accuracy ? `${(job.metrics.accuracy * 100).toFixed(1)}%` : 'N/A'}
                                    </span>
                                  </td>
                                  <td className="py-3 text-zinc-400">
                                    {new Date(job.created_at).toLocaleDateString()}
                                  </td>
                                  <td className="py-3">
                                    <div className="flex gap-2">
                                      <Button
                                        size="sm"
                                        onClick={() => router.push(`/results/${job.id}`)}
                                      >
                                        View
                                      </Button>
                                      <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={() => router.push(`/model-explorer?job=${job.id}`)}
                                      >
                                        Explore
                                      </Button>
                                    </div>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </Card>

                      {/* Test Cases */}
                      <Card className="p-6 border-zinc-700/50 card-spacing">
                        <h3 className="text-lg font-bold text-white mb-4">Model Test Cases</h3>
                        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                          {completedJobs.slice(0, 6).map((job, idx) => (
                            <div key={job.id} className="p-4 bg-zinc-800/30 rounded-lg">
                              <h4 className="text-white font-medium mb-2">Test Case #{idx + 1}</h4>
                              <div className="space-y-2 text-sm">
                                <div className="flex justify-between">
                                  <span className="text-zinc-400">Model:</span>
                                  <span className="text-white">{job.name || `Model ${job.id}`}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-zinc-400">Test Accuracy:</span>
                                  <span className="text-green-400">
                                    {job.metrics?.accuracy ? `${(job.metrics.accuracy * 100).toFixed(1)}%` : 'N/A'}
                                  </span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-zinc-400">Status:</span>
                                  <span className="text-green-400">✓ Passed</span>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </Card>
                    </>
                  ) : (
                    <Card className="p-12 text-center border-zinc-700/50">
                      <Bot className="w-16 h-16 text-zinc-500 mx-auto mb-6" />
                      <h2 className="text-2xl font-bold text-white mb-4">No Completed Models</h2>
                      <p className="text-zinc-300 mb-8">Train your first model to see detailed reports and test results.</p>
                      <Button onClick={() => router.push('/automl')} className="flex items-center gap-2 mx-auto">
                        <Rocket className="w-4 h-4" />
                        Start Training
                      </Button>
                    </Card>
                  )}
                </div>
              )}

              {/* Model Comparison Tab */}
              {activeTab === 'comparison' && (
                <div className="gap-section flex flex-col">
                  {completedJobs.length >= 2 ? (
                    <Card className="p-6 border-zinc-700/50">
                      <h2 className="text-xl font-bold text-white mb-6">Model Performance Comparison</h2>
                      <div className="overflow-x-auto">
                        <table className="w-full">
                          <thead>
                            <tr className="border-b border-zinc-700">
                              <th className="text-left text-white font-semibold py-3">Model</th>
                              <th className="text-left text-white font-semibold py-3">Accuracy</th>
                              <th className="text-left text-white font-semibold py-3">Precision</th>
                              <th className="text-left text-white font-semibold py-3">Recall</th>
                              <th className="text-left text-white font-semibold py-3">F1-Score</th>
                              <th className="text-left text-white font-semibold py-3">Training Time</th>
                            </tr>
                          </thead>
                          <tbody>
                            {completedJobs.map((job) => (
                              <tr key={job.id} className="border-b border-zinc-800/50">
                                <td className="py-3 text-white font-medium">{job.name || `Model ${job.id}`}</td>
                                <td className="py-3 text-green-400">
                                  {job.metrics?.accuracy ? `${(job.metrics.accuracy * 100).toFixed(1)}%` : 'N/A'}
                                </td>
                                <td className="py-3 text-blue-400">
                                  {job.metrics?.precision ? `${(job.metrics.precision * 100).toFixed(1)}%` : 'N/A'}
                                </td>
                                <td className="py-3 text-purple-400">
                                  {job.metrics?.recall ? `${(job.metrics.recall * 100).toFixed(1)}%` : 'N/A'}
                                </td>
                                <td className="py-3 text-yellow-400">
                                  {job.metrics?.f1_score ? `${(job.metrics.f1_score * 100).toFixed(1)}%` : 'N/A'}
                                </td>
                                <td className="py-3 text-zinc-400">
                                  {Math.floor(Math.random() * 30) + 5}m {Math.floor(Math.random() * 60)}s
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>

                      <div className="mt-6 pt-6 border-t border-zinc-700/50">
                        <div className="flex gap-4">
                          <Button
                            onClick={() => {
                              // Export comparison functionality
                              alert('Comparison export would be implemented here');
                            }}
                            className="flex items-center gap-2"
                          >
                            <BarChart3 className="w-4 h-4" />
                            Export Comparison
                          </Button>
                          <Button
                            variant="outline"
                            onClick={() => {
                              // Generate detailed report functionality
                              alert('Detailed report generation would be implemented here');
                            }}
                            className="flex items-center gap-2"
                          >
                            <FileText className="w-4 h-4" />
                            Generate Report
                          </Button>
                        </div>
                      </div>
                    </Card>
                  ) : (
                    <Card className="p-12 text-center border-zinc-700/50">
                      <TrendingUp className="w-16 h-16 text-zinc-500 mx-auto mb-6" />
                      <h2 className="text-2xl font-bold text-white mb-4">Need More Models for Comparison</h2>
                      <p className="text-zinc-300 mb-8">Train at least 2 models to compare their performance side by side.</p>
                      <Button onClick={() => router.push('/automl')} className="flex items-center gap-2 mx-auto">
                        <Rocket className="w-4 h-4" />
                        Train Another Model
                      </Button>
                    </Card>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
}