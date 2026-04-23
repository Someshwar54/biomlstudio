'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Header } from '@/components/Header';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/useAuth';
import { Dna, Calculator, Folder, Rocket, Target, Bot, Zap, CheckCircle2 } from 'lucide-react';

interface Pipeline {
  id: string;
  name: string;
  description: string;
  type: 'protein' | 'dna' | 'rna';
  features: string[];
  models: string[];
  applications: string[];
  icon: string;
}

export default function Pipelines() {
  useAuth();
  const router = useRouter();
  
  const [selectedPipeline, setSelectedPipeline] = useState<Pipeline | null>(null);
  const [datasets, setDatasets] = useState<any[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadDatasets();
  }, []);

  const loadDatasets = async () => {
    try {
      // First load from API
      const response = await api.get<any>('/datasets/');
      let apiDatasets = response.items || [];
      
      // Check localStorage for recent uploads
      const savedDatasets = localStorage.getItem('availableDatasets');
      if (savedDatasets) {
        try {
          const localDatasets = JSON.parse(savedDatasets);
          // Merge with API datasets, avoiding duplicates
          localDatasets.forEach((local: any) => {
            if (!apiDatasets.find((api: any) => api.id === local.id)) {
              apiDatasets.push({
                id: local.id,
                name: local.name,
                dataset_type: local.type,
                size: local.size,
                created_at: local.uploadedAt
              });
            }
          });
        } catch (error) {
          console.error('Error parsing saved datasets:', error);
        }
      }
      
      setDatasets(apiDatasets);
    } catch (error) {
      console.error('Failed to load datasets:', error);
      // If API fails, try to load from localStorage only
      const savedDatasets = localStorage.getItem('availableDatasets');
      if (savedDatasets) {
        try {
          const localDatasets = JSON.parse(savedDatasets);
          setDatasets(localDatasets.map((local: any) => ({
            id: local.id,
            name: local.name,
            dataset_type: local.type,
            size: local.size,
            created_at: local.uploadedAt
          })));
        } catch (error) {
          console.error('Error parsing saved datasets:', error);
        }
      }
    }
  };

  const pipelines: Pipeline[] = [
    {
      id: 'protein_structure',
      name: 'Protein Structure Prediction/Classification',
      description: 'Advanced protein analysis using ProtBERT and ESM2 embeddings for structure and function prediction',
      type: 'protein',
      icon: 'dna',
      features: [
        'ProtBERT embeddings',
        'ESM2 transformations', 
        'Amino acid composition',
        'Hydrophobicity patterns',
        'Secondary structure motifs',
        'Functional domains'
      ],
      models: ['CNN', 'BiLSTM', 'Transformer', 'Graph Neural Networks'],
      applications: [
        'Secondary structure prediction',
        'Protein family classification',
        'Enzyme classification (EC numbers)',
        'Binding site prediction',
        'Protein function annotation'
      ]
    },
    {
      id: 'dna_sequence',
      name: 'DNA Sequence Analysis',
      description: 'Comprehensive DNA analysis with k-mer and CNN-based encoding for genomic insights',
      type: 'dna',
      icon: 'calculator',
      features: [
        'K-mer representation',
        'One-hot encoding',
        'Sequence motifs',
        'GC content analysis', 
        'Regulatory elements',
        'Evolutionary conservation'
      ],
      models: ['CNN', 'RNN', 'BiLSTM', 'Attention Networks'],
      applications: [
        'Promoter region prediction',
        'Gene classification',
        'Splice site detection', 
        'Mutation impact prediction',
        'Disease association analysis'
      ]
    }
  ];

  const startPipeline = async () => {
    if (!selectedPipeline || !selectedDataset) return;

    setLoading(true);
    try {
      const config = {
        dataset_id: selectedDataset,
        task_type: selectedPipeline.id,
        target_column: 'auto_detect',
        encoding_method: selectedPipeline.type === 'protein' ? 'protbert' : 'kmer',
        kmer_size: 3,
        test_size: 0.2,
        val_size: 0.1,
        optimize_hyperparams: true,
        n_models: 3,
        generate_report: true
      };

      const job = await api.startWorkflow(config);
      
      if (job && job.job_id) {
        router.push(`/running/${job.job_id}`);
      } else {
        console.error('Failed to start workflow: Invalid job response', job);
        alert('Failed to start pipeline. Please try again.');
      }
    } catch (error) {
      console.error('Failed to start pipeline:', error);
    } finally {
      setLoading(false);
    }
  };

  if (selectedPipeline) {
    return (
      <>
        <Header />
        <div className="min-h-[calc(100vh-64px)] page-container bg-linear-to-b from-black via-zinc-950/80 to-black">
          <div className="max-w-7xl mx-auto px-6 py-16">
            {/* Back Button */}
            <Button
              variant="ghost"
              onClick={() => setSelectedPipeline(null)}
              className="mb-8 text-lg px-6 py-3"
            >
              ← Back to Pipeline Selection
            </Button>

            {/* Selected Pipeline Header */}
            <div className="text-center mb-12">
              <div className="mb-6">
                {selectedPipeline.icon === 'dna' ? (
                  <Dna className="w-16 h-16 text-green-400 mx-auto" />
                ) : (
                  <Calculator className="w-16 h-16 text-blue-400 mx-auto" />
                )}
              </div>
              <h1 className="text-4xl font-bold text-white mb-4">{selectedPipeline.name}</h1>
              <p className="text-xl text-zinc-300 max-w-7xl mx-auto leading-relaxed">
                {selectedPipeline.description}
              </p>
            </div>

            {/* Pipeline Configuration */}
            <Card className="p-8 card-spacing">
              <h2 className="text-2xl font-bold text-white mb-6">Configure Your Analysis</h2>
              
              {/* Features */}
              <div className="mb-8 mt-6">
                <h3 className="text-lg font-semibold text-white mb-4">Available Features:</h3>
                <div className="grid md:grid-cols-3 gap-4">
                  {selectedPipeline.features.map((feature, idx) => (
                    <div key={idx} className="p-4 bg-zinc-800/50 border border-zinc-700/50 rounded-lg">
                      <div className="font-medium text-white text-sm">{feature}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Models */}
              <div className="mb-8">
                <h3 className="text-lg font-semibold text-white mb-4">AI Models Available:</h3>
                <div className="grid md:grid-cols-2 gap-4">
                  {selectedPipeline.models.map((model, idx) => (
                    <div key={idx} className="p-4 bg-zinc-800/50 border border-zinc-700/50 rounded-lg">
                      <div className="font-medium text-white">{model}</div>
                      <div className="text-sm text-zinc-400 mt-1">
                        {model === 'CNN' ? 'Convolutional Neural Networks - Best for pattern recognition' :
                         model === 'RNN' ? 'Recurrent Neural Networks - Ideal for sequence analysis' :
                         model === 'BiLSTM' ? 'Bidirectional LSTM - Advanced sequence modeling' :
                         model === 'Transformer' ? 'Attention-based model - State-of-the-art performance' :
                         'Advanced neural network architecture'}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Applications */}
              <div className="mb-8">
                <h3 className="text-lg font-semibold text-white mb-4">What You Can Predict:</h3>
                <ul className="grid md:grid-cols-2 gap-2">
                  {selectedPipeline.applications.map((app, idx) => (
                    <li key={idx} className="flex items-center text-zinc-300">
                      <CheckCircle2 className="w-4 h-4 text-green-400 mr-3" />
                      {app}
                    </li>
                  ))}
                </ul>
              </div>
            </Card>

            {/* Dataset Selection */}
            <Card className="p-8 card-spacing">
              <h2 className="text-2xl font-bold text-white mb-6">Choose Your Dataset</h2>
              
              {datasets.length > 0 ? (
                <div className="space-y-4 mb-8">
                  {datasets
                    .filter(dataset => 
                      dataset.dataset_type === 'general' || 
                      dataset.dataset_type === selectedPipeline.type
                    )
                    .map((dataset) => (
                      <div
                        key={dataset.id}
                        className={`p-4 border rounded-lg cursor-pointer transition-all ${
                          selectedDataset === dataset.id
                            ? 'border-blue-500 bg-blue-500/10'
                            : 'border-zinc-700/50 hover:border-zinc-600/50'
                        }`}
                        onClick={() => setSelectedDataset(dataset.id)}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="font-medium text-white">{dataset.name}</div>
                            <div className="text-sm text-zinc-400">
                              {dataset.dataset_type} • {dataset.size || 'Unknown size'}
                            </div>
                          </div>
                          {selectedDataset === dataset.id && (
                            <div className="text-blue-400">✓ Selected</div>
                          )}
                        </div>
                      </div>
                    ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <Folder className="w-12 h-12 text-zinc-500 mx-auto mb-4" />
                  <h3 className="text-xl font-bold text-white mb-2">No suitable datasets found</h3>
                  <p className="text-zinc-400 mb-6">
                    You need a {selectedPipeline.type === 'protein' ? 'protein sequence (FASTA)' : 'DNA sequence (FASTA)'} dataset for this pipeline.
                  </p>
                  <div className="space-y-3">
                    <Button onClick={() => router.push('/upload')} size="lg">
                      <Folder className="w-4 h-4 mr-2" />
                      Upload {selectedPipeline.type === 'protein' ? 'Protein' : 'DNA'} Dataset
                    </Button>
                    <div className="text-sm text-zinc-500">
                      <span>or</span>
                    </div>
                    <Button 
                      variant="outline" 
                      onClick={() => router.push('/datasets')} 
                      size="sm"
                    >
                      View All Datasets
                    </Button>
                  </div>
                </div>
              )}

              {/* Start Analysis Button */}
              {datasets.length > 0 && (
                <div className="flex justify-center pt-8">
                  <Button
                    onClick={startPipeline}
                    disabled={!selectedDataset || loading}
                    size="lg"
                    className="px-12 py-4 text-lg"
                  >
                    {loading ? (
                      <>
                        <div className="animate-spin rounded-full h-5 w-5 border-2 border-white/20 border-t-white mr-3"></div>
                        Starting Analysis...
                      </>
                    ) : (
                      <>
                        <Rocket className="w-4 h-4 mr-2" />
                        Start {selectedPipeline.name}
                      </>
                    )}
                  </Button>
                </div>
              )}
            </Card>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Header />
        <div className="min-h-[calc(100vh-64px)] page-container bg-linear-to-b from-black via-zinc-950/80 to-black">
          <div className="max-w-7xl mx-auto px-6 py-16 padding-section">
          {/* Header */}
          <div className="text-center mb-16">
            <Button
              variant="ghost"
              onClick={() => router.back()}
              className="mb-8 self-start text-lg px-6 py-3"
            >
              ← Back to Dashboard
            </Button>
            <h1 className="text-6xl font-bold mb-8 bg-linear-to-br from-white via-zinc-100 to-zinc-400 bg-clip-text text-transparent">
              Domain-Specific Pipelines
            </h1>
            <p className="text-xl text-zinc-300 max-w-7xl mx-auto leading-relaxed mb-4">
              Specialized bioinformatics pipelines with advanced ML models and biological embeddings
            </p>
            <p className="text-lg text-zinc-400 max-w-7xl mx-auto mb-6">
              Choose your analysis type and follow our guided workflow - perfect for beginners!
            </p>
            {datasets.length > 0 && (
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-900/50 border border-blue-500/30 rounded-full">
                <span className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></span>
                <span className="text-blue-300 font-medium text-sm">
                  ✓ {datasets.length} dataset{datasets.length > 1 ? 's' : ''} available for analysis
                </span>
              </div>
            )}
          </div>

          {/* Pipeline Selection */}
          <div className="grid lg:grid-cols-2 gap-8 section-spacing">
            {pipelines.map((pipeline) => (
              <Card 
                key={pipeline.id}
                className="p-8 border-zinc-700/50 hover:border-blue-500/50 transition-all cursor-pointer group hover:shadow-2xl hover:shadow-blue-500/10"
              >
                <div 
                  className="w-full h-full" 
                  onClick={() => setSelectedPipeline(pipeline)}
                >
                  <div className="text-center mb-6">
                  <div className="mb-4">
                    {pipeline.icon === 'dna' ? (
                      <Dna className="w-16 h-16 text-green-400 mx-auto group-hover:scale-110 transition-transform" />
                    ) : (
                      <Calculator className="w-16 h-16 text-blue-400 mx-auto group-hover:scale-110 transition-transform" />
                    )}
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-3 group-hover:text-blue-300 transition-colors">
                    {pipeline.name}
                  </h3>
                  <p className="text-zinc-400 leading-relaxed text-lg">
                    {pipeline.description}
                  </p>
                </div>

                <div className="space-y-6">
                  <div>
                    <h4 className="text-lg font-semibold text-white mb-3 flex items-center">
                      <span className="w-2 h-2 bg-blue-400 rounded-full mr-3"></span>
                      What You Can Predict:
                    </h4>
                    <ul className="space-y-2 ml-5">
                      {pipeline.applications.slice(0, 3).map((app, idx) => (
                        <li key={idx} className="text-zinc-300 flex items-start">
                          <CheckCircle2 className="w-4 h-4 text-green-400 mr-2 mt-1" />
                          <span>{app}</span>
                        </li>
                      ))}
                      {pipeline.applications.length > 3 && (
                        <li className="text-zinc-400 text-sm ml-4">
                          +{pipeline.applications.length - 3} more applications
                        </li>
                      )}
                    </ul>
                  </div>

                  <div>
                    <h4 className="text-lg font-semibold text-white mb-3 flex items-center">
                      <span className="w-2 h-2 bg-purple-400 rounded-full mr-3"></span>
                      Key Features:
                    </h4>
                    <div className="grid grid-cols-2 gap-2 ml-5">
                      {pipeline.features.slice(0, 4).map((feature, idx) => (
                        <span key={idx} className="text-sm px-2 py-1 bg-zinc-800/50 text-zinc-300 rounded border border-zinc-700/50">
                          {feature}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                  <div className="mt-8 pt-6 border-t border-zinc-800/50">
                    <Button size="lg" className="w-full text-lg py-4 bg-linear-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700">
                      Choose {pipeline.type.toUpperCase()} Analysis →
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {/* Info Section */}
          <Card className="p-8 bg-zinc-900/50 border-zinc-800/50 card-spacing">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-white mb-6">Why Choose Domain-Specific Pipelines?</h2>
              <div className="grid md:grid-cols-3 gap-8 mt-8">
                <div className="text-center">
                  <Target className="w-10 h-10 text-red-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-white mb-2">Optimized for Biology</h3>
                  <p className="text-zinc-400 text-sm">
                    Each pipeline uses specialized embeddings and features designed for biological sequences
                  </p>
                </div>
                <div className="text-center">
                  <Bot className="w-10 h-10 text-purple-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-white mb-2">Advanced AI Models</h3>
                  <p className="text-zinc-400 text-sm">
                    State-of-the-art transformers, CNNs, and graph networks for maximum accuracy
                  </p>
                </div>
                <div className="text-center">
                  <Zap className="w-10 h-10 text-yellow-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-white mb-2">No Code Required</h3>
                  <p className="text-zinc-400 text-sm">
                    Simple point-and-click interface makes advanced bioinformatics accessible to everyone
                  </p>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </>
  );
}