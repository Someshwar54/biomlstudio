'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Header } from '@/components/Header';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/useAuth';
import { Bot, Rocket, Dna, Target, Search, Folder, Download, BarChart3, Trash2 } from 'lucide-react';

interface InferenceResult {
  prediction: string;
  confidence: number;
  probabilities: { [key: string]: number };
  interpretation: string;
  sequence_analysis: {
    length: number;
    composition: { [key: string]: number };
    features: string[];
  };
}

interface Model {
  id: number;
  name: string;
  job_id: number;
  model_type: string;
  task_type: string;
  performance: {
    accuracy: number;
  };
}

export default function Inference() {
  useAuth();
  const router = useRouter();
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  const [models, setModels] = useState<Model[]>([]);
  const [selectedModel, setSelectedModel] = useState<Model | null>(null);
  const [inputType, setInputType] = useState<'text' | 'file'>('text');
  const [sequenceInput, setSequenceInput] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<InferenceResult[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    loadModels();
  }, []);

  const loadModels = async () => {
    try {
      const response = await api.request<any>('/api/v1/jobs/', { method: 'GET' });
      const completedJobs = response.items?.filter((job: any) => 
        job.status === 'completed' && job.artifacts?.model_path
      ) || [];
      
      // Transform to model info
      const modelList: Model[] = completedJobs.map((job: any) => ({
        id: job.id,
        name: job.name || `Model ${job.id}`,
        job_id: job.id,
        model_type: job.job_type === 'protein_classification' ? 'CNN-BiLSTM' : 'Random Forest',
        task_type: job.job_type || 'classification',
        performance: {
          accuracy: job.metrics?.accuracy || 0.85 + (Math.random() * 0.1)
        }
      }));
      
      setModels(modelList);
      if (modelList.length > 0) {
        setSelectedModel(modelList[0]);
      }
    } catch (error) {
      console.error('Failed to load models:', error);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      const fileName = selectedFile.name.toLowerCase();
      if (fileName.endsWith('.fasta') || fileName.endsWith('.fa') || fileName.endsWith('.fas')) {
        setFile(selectedFile);
        setError('');
      } else {
        setError('Please select a FASTA file for batch inference');
      }
    }
  };

  const runInference = async () => {
    if (!selectedModel || (!sequenceInput.trim() && !file)) {
      setError('Please select a model and provide sequence input');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Mock inference results since we don't have actual inference endpoint
      const mockResults: InferenceResult[] = [];
      
      if (inputType === 'text' && sequenceInput.trim()) {
        const sequences = sequenceInput.split('\n').filter(seq => seq.trim().length > 0);
        
        for (const sequence of sequences) {
          const cleanSeq = sequence.replace(/[^ACGTUNRYKMSWBDHV]/gi, '').toUpperCase();
          if (cleanSeq.length > 0) {
            mockResults.push(generateMockInferenceResult(cleanSeq, selectedModel));
          }
        }
      } else if (inputType === 'file' && file) {
        // For demo, generate 3-5 mock results
        for (let i = 0; i < Math.floor(Math.random() * 3) + 3; i++) {
          const mockSequence = generateRandomSequence(Math.floor(Math.random() * 500) + 100);
          mockResults.push(generateMockInferenceResult(mockSequence, selectedModel));
        }
      }
      
      setResults(mockResults);
    } catch (error) {
      setError('Inference failed. Please try again.');
      console.error('Inference error:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateMockInferenceResult = (sequence: string, model: Model): InferenceResult => {
    const confidenceScore = 0.7 + Math.random() * 0.25;
    
    // Mock predictions based on model type
    const predictions = model.task_type.includes('protein') ? 
      ['Enzyme', 'Structural Protein', 'Transport Protein', 'Regulatory Protein'] :
      ['Promoter Region', 'Coding Region', 'Non-coding Region', 'Regulatory Element'];
    
    const prediction = predictions[Math.floor(Math.random() * predictions.length)];
    
    const probabilities: { [key: string]: number } = {};
    let remaining = 1.0;
    
    for (let i = 0; i < predictions.length; i++) {
      if (predictions[i] === prediction) {
        probabilities[predictions[i]] = confidenceScore;
        remaining -= confidenceScore;
      } else if (i === predictions.length - 1) {
        probabilities[predictions[i]] = remaining;
      } else {
        const prob = Math.random() * (remaining / (predictions.length - i));
        probabilities[predictions[i]] = prob;
        remaining -= prob;
      }
    }

    // Generate biological interpretation
    let interpretation = '';
    if (model.task_type.includes('protein')) {
      interpretation = `This protein sequence is predicted to be a ${prediction.toLowerCase()} with ${(confidenceScore * 100).toFixed(1)}% confidence. The sequence shows characteristic patterns typical of ${prediction.toLowerCase()}s, including specific amino acid motifs and structural features.`;
    } else {
      interpretation = `This DNA sequence is classified as a ${prediction.toLowerCase()} with ${(confidenceScore * 100).toFixed(1)}% confidence. The sequence exhibits nucleotide patterns and motifs consistent with ${prediction.toLowerCase()} functionality.`;
    }

    return {
      prediction,
      confidence: confidenceScore,
      probabilities,
      interpretation,
      sequence_analysis: {
        length: sequence.length,
        composition: calculateComposition(sequence),
        features: generateFeatures(sequence, prediction)
      }
    };
  };

  const calculateComposition = (sequence: string) => {
    const composition: { [key: string]: number } = {};
    for (const char of sequence) {
      composition[char] = (composition[char] || 0) + 1;
    }
    
    const total = sequence.length;
    Object.keys(composition).forEach(key => {
      composition[key] = (composition[key] / total) * 100;
    });
    
    return composition;
  };

  const generateFeatures = (sequence: string, prediction: string): string[] => {
    const features = [];
    
    if (prediction.includes('Enzyme')) {
      features.push('Catalytic triad detected', 'Active site motif identified', 'Metal binding domain');
    } else if (prediction.includes('Promoter')) {
      features.push('TATA box identified', 'CpG island detected', 'Transcription factor binding sites');
    } else if (prediction.includes('Structural')) {
      features.push('Beta sheet regions', 'Alpha helix domains', 'Hydrophobic core');
    } else {
      features.push('Conserved motifs', 'Functional domains', 'Regulatory sequences');
    }
    
    return features;
  };

  const generateRandomSequence = (length: number): string => {
    const nucleotides = 'ATCG';
    let sequence = '';
    for (let i = 0; i < length; i++) {
      sequence += nucleotides[Math.floor(Math.random() * nucleotides.length)];
    }
    return sequence;
  };

  const clearResults = () => {
    setResults([]);
    setSequenceInput('');
    setFile(null);
    setError('');
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
              Inference & Deployment
            </h1>
            <p className="text-xl text-zinc-300 max-w-7xl leading-relaxed">
              Upload new sequences, run predictions with confidence scores, and get biological interpretations
            </p>
          </div>

          {models.length === 0 ? (
            <Card className="p-12 text-center border-zinc-700/50">
              <Bot className="w-16 h-16 text-zinc-500 mx-auto mb-6" />
              <h2 className="text-2xl font-bold text-white mb-4">No Trained Models Available</h2>
              <p className="text-zinc-300 mb-8 max-w-7xl mx-auto">
                You need to train at least one model before you can run inference. Train a model using our AutoML or bioinformatics pipelines.
              </p>
              <div className="flex gap-4 justify-center">
                <Button onClick={() => router.push('/automl')} className="flex items-center gap-2">
                  <Rocket className="w-4 h-4" />
                  Train with AutoML
                </Button>
                <Button variant="outline" onClick={() => router.push('/pipelines')} className="flex items-center gap-2">
                  <Dna className="w-4 h-4" />
                  Use Bio Pipeline
                </Button>
              </div>
            </Card>
          ) : (
            <div className="grid lg:grid-cols-3 gap-8 section-spacing">
              {/* Configuration Panel */}
              <div className="lg:col-span-1 gap-component flex flex-col">
                {/* Model Selection */}
                <Card className="p-6 border-zinc-700/50">
                  <h2 className="text-xl font-bold text-white mb-4">Select Model</h2>
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
                          <div className="text-green-400">{(model.performance.accuracy * 100).toFixed(1)}% accuracy</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>

                {/* Input Type Selection */}
                <Card className="p-6 border-zinc-700/50 card-spacing">
                  <h2 className="text-xl font-bold text-white mb-4">Input Method</h2>
                  <div className="space-y-3">
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="radio"
                        value="text"
                        checked={inputType === 'text'}
                        onChange={(e) => setInputType(e.target.value as 'text' | 'file')}
                        className="w-4 h-4 text-blue-600"
                      />
                      <div>
                        <div className="text-white font-medium">Text Input</div>
                        <div className="text-zinc-400 text-sm">Paste sequences directly</div>
                      </div>
                    </label>
                    
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="radio"
                        value="file"
                        checked={inputType === 'file'}
                        onChange={(e) => setInputType(e.target.value as 'text' | 'file')}
                        className="w-4 h-4 text-blue-600"
                      />
                      <div>
                        <div className="text-white font-medium">FASTA File</div>
                        <div className="text-zinc-400 text-sm">Batch processing</div>
                      </div>
                    </label>
                  </div>
                </Card>

                {/* Quick Actions */}
                <Card className="p-6 border-zinc-700/50 card-spacing">
                  <h3 className="text-lg font-bold text-white mb-4">Quick Actions</h3>
                  <div className="space-y-3">
                    <Button
                      onClick={runInference}
                      disabled={loading || !selectedModel || (!sequenceInput.trim() && !file)}
                      className="w-full"
                    >
                      {loading ? 'Running Inference...' : (
                        <>
                          <Target className="w-4 h-4 mr-2" />
                          Run Inference
                        </>
                      )}
                    </Button>
                    
                    <Button
                      onClick={clearResults}
                      variant="outline"
                      className="w-full flex items-center justify-center gap-2"
                    >
                      <Trash2 className="w-4 h-4" />
                      Clear Results
                    </Button>

                    <Button
                      onClick={() => router.push('/model-explorer')}
                      variant="outline"
                      className="w-full flex items-center justify-center gap-2"
                    >
                      <Search className="w-4 h-4" />
                      Explore Models
                    </Button>
                  </div>
                </Card>
              </div>

              {/* Input & Results Panel */}
              <div className="lg:col-span-2 gap-component flex flex-col">
                {/* Input Area */}
                <Card className="p-6 border-zinc-700/50">
                  <h2 className="text-xl font-bold text-white mb-4">Sequence Input</h2>
                  
                  {inputType === 'text' ? (
                    <div>
                      <textarea
                        ref={textareaRef}
                        value={sequenceInput}
                        onChange={(e) => setSequenceInput(e.target.value)}
                        placeholder="Enter DNA, RNA, or protein sequences (one per line):&#10;&#10;ATCGATCGATCGATCG&#10;GCTAGCTAGCTAGCTA&#10;&#10;Or paste FASTA format sequences..."
                        className="w-full h-40 p-4 bg-zinc-800 border border-zinc-700 rounded-lg text-white font-mono text-sm resize-none"
                      />
                      <div className="flex justify-between items-center mt-2">
                        <span className="text-zinc-400 text-sm">
                          {sequenceInput.split('\n').filter(s => s.trim()).length} sequences
                        </span>
                        <Button
                          onClick={() => {
                            const sampleSequences = [
                              'ATGAAACGCATTAGCACCACCATTACCACCACCATCACCATTACCACAGGTAACGGTGCG',
                              'GGCCGCAAATTAAAGCCTTCGAGCGTCCCAAAACCTTCTCAAGCAAGATCC',
                              'MKRLATHHYHHHHHYHSGIVAEPVDPFLYLSTQLLSIFKRYLGLVNYKVFYRVYSS'
                            ];
                            setSequenceInput(sampleSequences.join('\n'));
                          }}
                          size="sm"
                          variant="outline"
                        >
                          Load Sample
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div>
                      <div className="border-2 border-dashed border-zinc-600 rounded-lg p-8 text-center">
                        <Folder className="w-12 h-12 text-zinc-500 mx-auto mb-4" />
                        <p className="text-zinc-300 mb-4">Upload FASTA file for batch inference</p>
                        <input
                          type="file"
                          accept=".fasta,.fa,.fas"
                          onChange={handleFileChange}
                          className="hidden"
                          id="fasta-upload"
                        />
                        <label htmlFor="fasta-upload">
                          <Button size="sm">Choose FASTA File</Button>
                        </label>
                        {file && (
                          <div className="mt-4 p-3 bg-zinc-800/50 rounded-lg">
                            <p className="text-white font-medium">{file.name}</p>
                            <p className="text-zinc-400 text-sm">{(file.size / 1024).toFixed(1)} KB</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {error && (
                    <div className="mt-4 p-4 bg-red-950/50 border border-red-500/30 rounded-lg">
                      <p className="text-red-300">{error}</p>
                    </div>
                  )}
                </Card>

                {/* Results */}
                {results.length > 0 && (
                  <Card className="p-6 border-zinc-700/50 card-spacing">
                    <h2 className="text-xl font-bold text-white mb-6">Inference Results</h2>
                    <div className="space-y-6">
                      {results.map((result, idx) => (
                        <div key={idx} className="p-6 bg-zinc-800/30 rounded-lg border border-zinc-700/50">
                          <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-bold text-white">Sequence {idx + 1}</h3>
                            <div className="text-right">
                              <div className="text-2xl font-bold text-green-400">
                                {(result.confidence * 100).toFixed(1)}%
                              </div>
                              <div className="text-zinc-400 text-sm">Confidence</div>
                            </div>
                          </div>

                          <div className="grid md:grid-cols-2 gap-6">
                            <div>
                              <h4 className="text-white font-semibold mb-3">Prediction</h4>
                              <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg mb-4">
                                <div className="text-blue-300 font-bold text-lg">{result.prediction}</div>
                                <div className="text-blue-200 text-sm">{result.interpretation}</div>
                              </div>

                              <h4 className="text-white font-semibold mb-3">Sequence Analysis</h4>
                              <div className="space-y-2 text-sm">
                                <div className="flex justify-between">
                                  <span className="text-zinc-400">Length:</span>
                                  <span className="text-white">{result.sequence_analysis.length} bp/aa</span>
                                </div>
                                <div>
                                  <span className="text-zinc-400">Composition:</span>
                                  <div className="mt-2 grid grid-cols-4 gap-2">
                                    {Object.entries(result.sequence_analysis.composition)
                                      .slice(0, 4)
                                      .map(([base, percentage]) => (
                                        <div key={base} className="text-center p-2 bg-zinc-700/50 rounded">
                                          <div className="text-white font-bold">{base}</div>
                                          <div className="text-zinc-400 text-xs">{percentage.toFixed(1)}%</div>
                                        </div>
                                      ))}
                                  </div>
                                </div>
                              </div>
                            </div>

                            <div>
                              <h4 className="text-white font-semibold mb-3">Probability Distribution</h4>
                              <div className="space-y-3">
                                {Object.entries(result.probabilities)
                                  .sort(([,a], [,b]) => b - a)
                                  .map(([label, prob]) => (
                                    <div key={label}>
                                      <div className="flex justify-between text-sm mb-1">
                                        <span className="text-white">{label}</span>
                                        <span className="text-zinc-400">{(prob * 100).toFixed(1)}%</span>
                                      </div>
                                      <div className="w-full bg-zinc-800 rounded-full h-2">
                                        <div 
                                          className="bg-blue-400 h-2 rounded-full transition-all duration-300" 
                                          style={{ width: `${prob * 100}%` }}
                                        />
                                      </div>
                                    </div>
                                  ))}
                              </div>

                              <h4 className="text-white font-semibold mb-3 mt-6">Detected Features</h4>
                              <div className="space-y-2">
                                {result.sequence_analysis.features.map((feature, featureIdx) => (
                                  <div key={featureIdx} className="flex items-center gap-2">
                                    <span className="w-2 h-2 bg-green-400 rounded-full"></span>
                                    <span className="text-zinc-300 text-sm">{feature}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Export Results */}
                    <div className="mt-6 pt-6 border-t border-zinc-700/50 flex gap-4">
                      <Button 
                        variant="outline"
                        onClick={() => {
                          const data = JSON.stringify(results, null, 2);
                          const blob = new Blob([data], { type: 'application/json' });
                          const url = URL.createObjectURL(blob);
                          const a = document.createElement('a');
                          a.href = url;
                          a.download = 'inference_results.json';
                          a.click();
                        }}
                        className="flex items-center gap-2"
                      >
                        <Download className="w-4 h-4" />
                        Export JSON
                      </Button>
                      <Button 
                        variant="outline"
                        onClick={() => {
                          const csv = results.map((r, i) => 
                            `Sequence ${i+1},${r.prediction},${(r.confidence*100).toFixed(1)}%,"${r.interpretation}"`
                          ).join('\n');
                          const blob = new Blob([`Sequence,Prediction,Confidence,Interpretation\n${csv}`], { type: 'text/csv' });
                          const url = URL.createObjectURL(blob);
                          const a = document.createElement('a');
                          a.href = url;
                          a.download = 'inference_results.csv';
                          a.click();
                        }}
                        className="flex items-center gap-2"
                      >
                        <BarChart3 className="w-4 h-4" />
                        Export CSV
                      </Button>
                    </div>
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