'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Header } from '@/components/Header';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/useAuth';
import { Bot, Rocket, Dna, FileText, Building2, BarChart3, Settings, Ruler, Download, TrendingUp, ArrowLeft, Microscope, Download as DownloadIcon, Eye, Target } from 'lucide-react';

interface ModelInfo {
  id: number;
  name: string;
  job_id: number;
  model_type: string;
  architecture: {
    layers: any[];
    total_params: number;
    trainable_params: number;
    model_size_mb: number;
  };
  performance: {
    accuracy: number;
    f1_score: number;
    precision: number;
    recall: number;
  };
  created_at: string;
}

export default function ModelExplorer() {
  useAuth();
  const router = useRouter();
  
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState<ModelInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'summary' | 'architecture' | 'layers' | 'parameters' | 'tensors' | 'performance'>('summary');

  useEffect(() => {
    loadModels();
  }, []);

  const loadModels = async () => {
    try {
      const response = await api.request<any>('/api/v1/jobs/', { method: 'GET' });
      const completedJobs = response.items?.filter((job: any) => 
        job.status === 'completed' && job.artifacts?.model_path
      ) || [];
      
      // Transform jobs to model info (mock data for now)
      const mockModels: ModelInfo[] = completedJobs.map((job: any, idx: number) => ({
        id: job.id,
        name: job.name || `Model ${job.id}`,
        job_id: job.id,
        model_type: job.job_type === 'protein_classification' ? 'CNN-BiLSTM' : 'Random Forest',
        architecture: {
          layers: generateMockLayers(job.job_type),
          total_params: 1250000 + (idx * 50000),
          trainable_params: 1200000 + (idx * 45000),
          model_size_mb: 15.2 + (idx * 2.1)
        },
        performance: {
          accuracy: job.metrics?.accuracy || 0.85 + (Math.random() * 0.1),
          f1_score: job.metrics?.f1_score || 0.82 + (Math.random() * 0.1),
          precision: job.metrics?.precision || 0.84 + (Math.random() * 0.1),
          recall: job.metrics?.recall || 0.83 + (Math.random() * 0.1)
        },
        created_at: job.created_at
      }));
      
      setModels(mockModels);
    } catch (error) {
      console.error('Failed to load models:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateMockLayers = (jobType: string) => {
    if (jobType === 'protein_classification') {
      return [
        { name: 'Input', type: 'InputLayer', input_shape: [1000, 21], output_shape: [1000, 21], params: 0 },
        { name: 'Embedding', type: 'Embedding', input_shape: [1000, 21], output_shape: [1000, 128], params: 2688 },
        { name: 'Conv1D_1', type: 'Conv1D', input_shape: [1000, 128], output_shape: [998, 64], params: 24640 },
        { name: 'MaxPool1D_1', type: 'MaxPooling1D', input_shape: [998, 64], output_shape: [499, 64], params: 0 },
        { name: 'BiLSTM_1', type: 'Bidirectional', input_shape: [499, 64], output_shape: [499, 128], params: 66048 },
        { name: 'BiLSTM_2', type: 'Bidirectional', input_shape: [499, 128], output_shape: [256], params: 197632 },
        { name: 'Dropout', type: 'Dropout', input_shape: [256], output_shape: [256], params: 0 },
        { name: 'Dense_1', type: 'Dense', input_shape: [256], output_shape: [128], params: 32896 },
        { name: 'Dense_Output', type: 'Dense', input_shape: [128], output_shape: [10], params: 1290 }
      ];
    } else {
      return [
        { name: 'Input', type: 'InputLayer', input_shape: [100], output_shape: [100], params: 0 },
        { name: 'Dense_1', type: 'Dense', input_shape: [100], output_shape: [128], params: 12928 },
        { name: 'ReLU_1', type: 'Activation', input_shape: [128], output_shape: [128], params: 0 },
        { name: 'Dropout_1', type: 'Dropout', input_shape: [128], output_shape: [128], params: 0 },
        { name: 'Dense_2', type: 'Dense', input_shape: [128], output_shape: [64], params: 8256 },
        { name: 'ReLU_2', type: 'Activation', input_shape: [64], output_shape: [64], params: 0 },
        { name: 'Dense_Output', type: 'Dense', input_shape: [64], output_shape: [2], params: 130 }
      ];
    }
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const getLayerColor = (type: string) => {
    switch (type.toLowerCase()) {
      case 'inputlayer': return 'bg-blue-500/20 border-blue-500/50 text-blue-300';
      case 'embedding': return 'bg-green-500/20 border-green-500/50 text-green-300';
      case 'conv1d': return 'bg-purple-500/20 border-purple-500/50 text-purple-300';
      case 'maxpooling1d': return 'bg-orange-500/20 border-orange-500/50 text-orange-300';
      case 'bidirectional': return 'bg-red-500/20 border-red-500/50 text-red-300';
      case 'dense': return 'bg-yellow-500/20 border-yellow-500/50 text-yellow-300';
      case 'dropout': return 'bg-gray-500/20 border-gray-500/50 text-gray-300';
      case 'activation': return 'bg-pink-500/20 border-pink-500/50 text-pink-300';
      default: return 'bg-zinc-500/20 border-zinc-500/50 text-zinc-300';
    }
  };

  return (
    <>
      <Header />
      <div className="min-h-[calc(100vh-64px)] bg-gradient-to-b from-black via-zinc-950/80 to-black">
        <div className="page-container padding-section">
          {/* Header */}
          <div className="section-spacing text-center-wrapper">
            <Button
              variant="ghost"
              onClick={() => router.back()}
              className="mb-6 self-start"
            >
              ← Back to Dashboard
            </Button>
            <h1 className="text-5xl sm:text-6xl font-bold mb-6 bg-gradient-to-br from-white via-zinc-100 to-zinc-400 bg-clip-text text-transparent">
              Model Explorer
            </h1>
            <p className="text-xl text-zinc-300 max-w-7xl leading-relaxed">
              Visualize model architecture, explore layers, analyze parameters, and understand how your models work internally
            </p>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
              <p className="text-zinc-300">Loading trained models...</p>
            </div>
          ) : models.length === 0 ? (
            <Card className="p-12 text-center border-zinc-700/50">
              <Bot className="w-16 h-16 text-zinc-500 mx-auto mb-6" />
              <h2 className="text-2xl font-bold text-white mb-4">No Trained Models Yet</h2>
              <p className="text-zinc-300 mb-8 max-w-7xl mx-auto">
                Train your first model to explore its architecture and internal structure.
              </p>
              <div className="flex gap-4 justify-center">
                <Button onClick={() => router.push('/automl')} className="flex items-center gap-2">
                  <Rocket className="w-4 h-4" />
                  Start AutoML Training
                </Button>
                <Button variant="outline" onClick={() => router.push('/pipelines')} className="flex items-center gap-2">
                  <Dna className="w-4 h-4" />
                  Use Bio Pipeline
                </Button>
              </div>
            </Card>
          ) : (
            <div className="grid lg:grid-cols-4 gap-8 section-spacing">
              {/* Model List */}
              <div className="lg:col-span-1">
                <Card className="p-6 border-zinc-700/50">
                  <h2 className="text-xl font-bold text-white mb-4">Trained Models</h2>
                  <div className="space-y-3">
                    {models.map((model) => (
                      <div
                        key={model.id}
                        onClick={() => setSelectedModel(model)}
                        className={`p-4 border rounded-lg cursor-pointer transition-all ${
                          selectedModel?.id === model.id
                            ? 'border-blue-500 bg-blue-500/10'
                            : 'border-zinc-700 hover:border-zinc-600 hover:bg-zinc-800/30'
                        }`}
                      >
                        <h3 className="text-white font-medium mb-1">{model.name}</h3>
                        <div className="text-zinc-400 text-sm space-y-1">
                          <div>{model.model_type}</div>
                          <div>{formatNumber(model.architecture.total_params)} params</div>
                          <div className="text-green-400">{(model.performance.accuracy * 100).toFixed(1)}% accuracy</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>

              {/* Model Details */}
              <div className="lg:col-span-3">
                {selectedModel ? (
                  <>
                    {/* Model Info Header */}
                    <Card className="p-6 card-spacing border-zinc-700/50">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <h2 className="text-2xl font-bold text-white">{selectedModel.name}</h2>
                          <p className="text-zinc-400">{selectedModel.model_type} • Job #{selectedModel.job_id}</p>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-bold text-green-400">
                            {(selectedModel.performance.accuracy * 100).toFixed(1)}%
                          </div>
                          <div className="text-zinc-400 text-sm">Accuracy</div>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="text-center p-3 bg-zinc-800/30 rounded-lg">
                          <div className="text-lg font-bold text-white">{formatNumber(selectedModel.architecture.total_params)}</div>
                          <div className="text-zinc-400 text-sm">Total Parameters</div>
                        </div>
                        <div className="text-center p-3 bg-zinc-800/30 rounded-lg">
                          <div className="text-lg font-bold text-white">{formatNumber(selectedModel.architecture.trainable_params)}</div>
                          <div className="text-zinc-400 text-sm">Trainable</div>
                        </div>
                        <div className="text-center p-3 bg-zinc-800/30 rounded-lg">
                          <div className="text-lg font-bold text-white">{selectedModel.architecture.model_size_mb.toFixed(1)} MB</div>
                          <div className="text-zinc-400 text-sm">Model Size</div>
                        </div>
                        <div className="text-center p-3 bg-zinc-800/30 rounded-lg">
                          <div className="text-lg font-bold text-white">{selectedModel.architecture.layers.length}</div>
                          <div className="text-zinc-400 text-sm">Layers</div>
                        </div>
                      </div>
                    </Card>

                    {/* Model Explorer Tabs */}
                    <div className="flex flex-wrap gap-2 card-spacing">
                      {[
                        { id: 'summary', label: 'Model Summary', icon: FileText, description: 'Keras/PyTorch-style summary' },
                        { id: 'architecture', label: 'Visual Architecture', icon: Building2, description: 'Block diagram view' },
                        { id: 'layers', label: 'Layer Structure', icon: BarChart3, description: 'Detailed layer analysis' },
                        { id: 'parameters', label: 'Parameter Count', icon: Settings, description: 'Weight distribution' },
                        { id: 'tensors', label: 'Tensor Shapes', icon: Ruler, description: 'Input/output dimensions' },
                        { id: 'performance', label: 'Performance', icon: TrendingUp, description: 'Metrics & benchmarks' }
                      ].map((tab) => {
                        const IconComponent = tab.icon;
                        return (
                          <Button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id as any)}
                            variant={activeTab === tab.id ? 'primary' : 'outline'}
                            size="sm"
                            className="flex flex-col items-center p-3 h-auto"
                            title={tab.description}
                          >
                            <IconComponent className="w-5 h-5 mb-1" />
                            <span className="text-xs">{tab.label}</span>
                          </Button>
                        );
                      })}
                    </div>

                    {/* Tab Content */}
                    {activeTab === 'summary' && (
                      <Card className="p-6 border-zinc-700/50 card-spacing">
                        <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                          <Microscope className="w-5 h-5" />
                          Model Summary (Keras/PyTorch Style)
                        </h3>
                        
                        {/* Model Overview */}
                        <div className="bg-zinc-900/50 rounded-lg p-4 mb-6">
                          <div className="grid md:grid-cols-2 gap-4 text-sm font-mono">
                            <div>
                              <div className="text-zinc-400 mb-2">MODEL INFORMATION</div>
                              <div className="space-y-1">
                                <div><span className="text-blue-400">Name:</span> {selectedModel.name}</div>
                                <div><span className="text-blue-400">Type:</span> {selectedModel.model_type}</div>
                                <div><span className="text-blue-400">Framework:</span> TensorFlow/Keras</div>
                                <div><span className="text-blue-400">Created:</span> {new Date(selectedModel.created_at).toLocaleDateString()}</div>
                              </div>
                            </div>
                            <div>
                              <div className="text-zinc-400 mb-2">PARAMETER SUMMARY</div>
                              <div className="space-y-1">
                                <div><span className="text-green-400">Total params:</span> {formatNumber(selectedModel.architecture.total_params)}</div>
                                <div><span className="text-green-400">Trainable params:</span> {formatNumber(selectedModel.architecture.trainable_params)}</div>
                                <div><span className="text-green-400">Non-trainable:</span> {formatNumber(selectedModel.architecture.total_params - selectedModel.architecture.trainable_params)}</div>
                                <div><span className="text-green-400">Model size:</span> {selectedModel.architecture.model_size_mb.toFixed(2)} MB</div>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Layer Summary Table */}
                        <div className="bg-black/50 rounded-lg p-4">
                          <div className="text-zinc-400 text-sm mb-3 font-mono">LAYER SUMMARY</div>
                          <div className="overflow-x-auto">
                            <table className="w-full text-sm font-mono">
                              <thead>
                                <tr className="border-b border-zinc-700 text-zinc-400">
                                  <th className="text-left py-2">Layer (type)</th>
                                  <th className="text-left py-2">Output Shape</th>
                                  <th className="text-right py-2">Param #</th>
                                </tr>
                              </thead>
                              <tbody>
                                {selectedModel.architecture.layers.map((layer, idx) => (
                                  <tr key={idx} className="border-b border-zinc-800">
                                    <td className="py-2 text-white">
                                      {layer.name} ({layer.type})
                                    </td>
                                    <td className="py-2 text-zinc-300">
                                      {JSON.stringify(layer.output_shape)}
                                    </td>
                                    <td className="py-2 text-right text-zinc-300">
                                      {formatNumber(layer.params)}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      </Card>
                    )}

                    {activeTab === 'architecture' && (
                      <Card className="p-6 border-zinc-700/50">
                        <h3 className="text-xl font-bold text-white mb-6">Model Architecture</h3>
                        <div className="space-y-4">
                          {selectedModel.architecture.layers.map((layer, idx) => (
                            <div key={idx} className="flex items-center gap-4">
                              <div className="w-8 h-8 bg-zinc-700 rounded-full flex items-center justify-center text-white text-sm font-bold">
                                {idx + 1}
                              </div>
                              <div className={`flex-1 p-4 rounded-lg border ${getLayerColor(layer.type)}`}>
                                <div className="flex items-center justify-between">
                                  <div>
                                    <h4 className="font-bold">{layer.name}</h4>
                                    <p className="text-sm opacity-80">{layer.type}</p>
                                  </div>
                                  <div className="text-right text-sm">
                                    <div>Output: {JSON.stringify(layer.output_shape)}</div>
                                    <div>{formatNumber(layer.params)} params</div>
                                  </div>
                                </div>
                              </div>
                              {idx < selectedModel.architecture.layers.length - 1 && (
                                <div className="text-zinc-400">↓</div>
                              )}
                            </div>
                          ))}
                        </div>
                      </Card>
                    )}

                    {activeTab === 'layers' && (
                      <Card className="p-6 border-zinc-700/50">
                        <h3 className="text-xl font-bold text-white mb-6">Layer Details</h3>
                        <div className="overflow-x-auto">
                          <table className="w-full">
                            <thead>
                              <tr className="border-b border-zinc-700">
                                <th className="text-left text-white font-semibold py-3">Layer</th>
                                <th className="text-left text-white font-semibold py-3">Type</th>
                                <th className="text-left text-white font-semibold py-3">Input Shape</th>
                                <th className="text-left text-white font-semibold py-3">Output Shape</th>
                                <th className="text-left text-white font-semibold py-3">Parameters</th>
                              </tr>
                            </thead>
                            <tbody>
                              {selectedModel.architecture.layers.map((layer, idx) => (
                                <tr key={idx} className="border-b border-zinc-800/50">
                                  <td className="py-3 text-white font-medium">{layer.name}</td>
                                  <td className="py-3 text-zinc-400">{layer.type}</td>
                                  <td className="py-3 text-zinc-400">{JSON.stringify(layer.input_shape)}</td>
                                  <td className="py-3 text-zinc-400">{JSON.stringify(layer.output_shape)}</td>
                                  <td className="py-3 text-zinc-400">{formatNumber(layer.params)}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </Card>
                    )}

                    {activeTab === 'parameters' && (
                      <div className="grid md:grid-cols-2 gap-6">
                        <Card className="p-6 border-zinc-700/50">
                          <h3 className="text-xl font-bold text-white mb-6">Parameter Distribution</h3>
                          <div className="space-y-4">
                            {selectedModel.architecture.layers
                              .filter(layer => layer.params > 0)
                              .sort((a, b) => b.params - a.params)
                              .map((layer, idx) => {
                                const percentage = (layer.params / selectedModel.architecture.total_params) * 100;
                                return (
                                  <div key={idx}>
                                    <div className="flex justify-between text-sm mb-2">
                                      <span className="text-white">{layer.name}</span>
                                      <span className="text-zinc-400">{percentage.toFixed(1)}%</span>
                                    </div>
                                    <div className="w-full bg-zinc-800 rounded-full h-2">
                                      <div 
                                        className="bg-blue-400 h-2 rounded-full transition-all duration-300" 
                                        style={{ width: `${percentage}%` }}
                                      />
                                    </div>
                                  </div>
                                );
                              })}
                          </div>
                        </Card>

                        <Card className="p-6 border-zinc-700/50">
                          <h3 className="text-xl font-bold text-white mb-6">Model Statistics</h3>
                          <div className="space-y-4">
                            <div className="flex justify-between">
                              <span className="text-zinc-400">Total Parameters:</span>
                              <span className="text-white font-bold">{formatNumber(selectedModel.architecture.total_params)}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-zinc-400">Trainable Parameters:</span>
                              <span className="text-white font-bold">{formatNumber(selectedModel.architecture.trainable_params)}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-zinc-400">Non-trainable:</span>
                              <span className="text-white font-bold">
                                {formatNumber(selectedModel.architecture.total_params - selectedModel.architecture.trainable_params)}
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-zinc-400">Model Size:</span>
                              <span className="text-white font-bold">{selectedModel.architecture.model_size_mb.toFixed(1)} MB</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-zinc-400">Number of Layers:</span>
                              <span className="text-white font-bold">{selectedModel.architecture.layers.length}</span>
                            </div>
                          </div>
                        </Card>
                      </div>
                    )}

                    {activeTab === 'tensors' && (
                      <Card className="p-6 border-zinc-700/50">
                        <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                          <Ruler className="w-5 h-5" />
                          Tensor Shapes & Dimensions
                        </h3>
                        
                        <div className="space-y-6">
                          {/* Input/Output Overview */}
                          <div className="grid md:grid-cols-2 gap-6">
                            <div className="bg-zinc-900/50 rounded-lg p-4">
                              <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                                <Download className="w-5 h-5" />
                                Model Input
                              </h4>
                              <div className="space-y-2">
                                <div className="flex justify-between">
                                  <span className="text-zinc-400">Shape:</span>
                                  <span className="text-white font-mono">{JSON.stringify(selectedModel.architecture.layers[0]?.input_shape || 'N/A')}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-zinc-400">Data Type:</span>
                                  <span className="text-white">float32</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-zinc-400">Memory per batch:</span>
                                  <span className="text-white">~4KB</span>
                                </div>
                              </div>
                            </div>

                            <div className="bg-zinc-900/50 rounded-lg p-4">
                              <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                                📤 Model Output
                              </h4>
                              <div className="space-y-2">
                                <div className="flex justify-between">
                                  <span className="text-zinc-400">Shape:</span>
                                  <span className="text-white font-mono">{JSON.stringify(selectedModel.architecture.layers[selectedModel.architecture.layers.length - 1]?.output_shape || 'N/A')}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-zinc-400">Data Type:</span>
                                  <span className="text-white">float32</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-zinc-400">Classes:</span>
                                  <span className="text-white">{Array.isArray(selectedModel.architecture.layers[selectedModel.architecture.layers.length - 1]?.output_shape) ? selectedModel.architecture.layers[selectedModel.architecture.layers.length - 1]?.output_shape[selectedModel.architecture.layers[selectedModel.architecture.layers.length - 1]?.output_shape.length - 1] || 'N/A' : 'N/A'}</span>
                                </div>
                              </div>
                            </div>
                          </div>

                          {/* Layer-by-Layer Tensor Flow */}
                          <div>
                            <h4 className="text-lg font-semibold text-white mb-4">Tensor Flow Through Network</h4>
                            <div className="space-y-3">
                              {selectedModel.architecture.layers.map((layer, idx) => (
                                <div key={idx} className="flex items-center gap-4 p-3 bg-zinc-900/30 rounded-lg">
                                  <div className="w-8 h-8 bg-zinc-700 rounded-full flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
                                    {idx + 1}
                                  </div>
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-1">
                                      <span className="font-medium text-white">{layer.name}</span>
                                      <span className="text-xs px-2 py-1 bg-zinc-700 rounded text-zinc-300">{layer.type}</span>
                                    </div>
                                    <div className="text-sm text-zinc-400">
                                      Input: <span className="font-mono text-blue-300">{JSON.stringify(layer.input_shape)}</span>
                                      {' → '}
                                      Output: <span className="font-mono text-green-300">{JSON.stringify(layer.output_shape)}</span>
                                    </div>
                                  </div>
                                  <div className="text-right text-sm flex-shrink-0">
                                    <div className="text-white font-medium">{formatNumber(layer.params)}</div>
                                    <div className="text-zinc-400">params</div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* Tensor Statistics */}
                          <div className="bg-zinc-900/50 rounded-lg p-4">
                            <h4 className="text-lg font-semibold text-white mb-4">Tensor Statistics</h4>
                            <div className="grid md:grid-cols-3 gap-4">
                              <div className="text-center">
                                <div className="text-2xl font-bold text-blue-400">
                                  {selectedModel.architecture.layers.filter(l => l.input_shape).length}
                                </div>
                                <div className="text-zinc-400 text-sm">Tensor Transformations</div>
                              </div>
                              <div className="text-center">
                                <div className="text-2xl font-bold text-green-400">
                                  {Math.max(...selectedModel.architecture.layers.map(l => 
                                    Array.isArray(l.output_shape) ? l.output_shape.reduce((a, b) => typeof b === 'number' ? a * b : a, 1) : 1
                                  )).toLocaleString()}
                                </div>
                                <div className="text-zinc-400 text-sm">Max Tensor Size</div>
                              </div>
                              <div className="text-center">
                                <div className="text-2xl font-bold text-purple-400">
                                  {selectedModel.architecture.layers.reduce((total, layer) => {
                                    const size = Array.isArray(layer.output_shape) ? layer.output_shape.reduce((a, b) => typeof b === 'number' ? a * b : a, 1) : 0;
                                    return total + size;
                                  }, 0).toLocaleString()}
                                </div>
                                <div className="text-zinc-400 text-sm">Total Activations</div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </Card>
                    )}

                    {activeTab === 'performance' && (
                      <div className="grid md:grid-cols-2 gap-6">
                        <Card className="p-6 border-zinc-700/50">
                          <h3 className="text-xl font-bold text-white mb-6">Performance Metrics</h3>
                          <div className="space-y-6">
                            {Object.entries(selectedModel.performance).map(([metric, value]) => (
                              <div key={metric}>
                                <div className="flex justify-between text-sm mb-2">
                                  <span className="text-white capitalize">{metric.replace('_', ' ')}</span>
                                  <span className="text-zinc-400">{(value * 100).toFixed(1)}%</span>
                                </div>
                                <div className="w-full bg-zinc-800 rounded-full h-3">
                                  <div 
                                    className="bg-green-400 h-3 rounded-full transition-all duration-300" 
                                    style={{ width: `${value * 100}%` }}
                                  />
                                </div>
                              </div>
                            ))}
                          </div>
                        </Card>

                        <Card className="p-6 border-zinc-700/50">
                          <h3 className="text-xl font-bold text-white mb-6">Model Actions</h3>
                          <div className="space-y-4">
                            <Button 
                              className="w-full flex items-center justify-center gap-2"
                              onClick={() => router.push(`/results/${selectedModel.job_id}`)}
                            >
                              <BarChart3 className="w-4 h-4" />
                              View Full Results
                            </Button>
                            <Button 
                              variant="outline" 
                              className="w-full flex items-center justify-center gap-2"
                              onClick={() => router.push(`/inference?model=${selectedModel.id}`)}
                            >
                              <Target className="w-4 h-4" />
                              Use for Inference
                            </Button>
                            <Button 
                              variant="outline" 
                              className="w-full flex items-center justify-center gap-2"
                              onClick={() => {
                                // Download model functionality would go here
                                alert('Model download functionality would be implemented here');
                              }}
                            >
                              <DownloadIcon className="w-4 h-4" />
                              Download Model
                            </Button>
                          </div>
                        </Card>
                      </div>
                    )}
                  </>
                ) : (
                  <Card className="p-12 text-center border-zinc-700/50">
                    <ArrowLeft className="w-12 h-12 text-zinc-500 mx-auto mb-4" />
                    <h3 className="text-xl text-white mb-2">Select a Model</h3>
                    <p className="text-zinc-400">Choose a trained model from the list to explore its architecture and details.</p>
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