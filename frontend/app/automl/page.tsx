'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Header } from '@/components/Header';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/useAuth';
import { Folder, Brain, Search, RotateCcw, ArrowLeftRight, Target, TreePine, Zap, Ruler, Calculator, Lightbulb, Rocket, CheckCircle2, BarChart3 } from 'lucide-react';

interface AutoMLConfig {
  dataset_id: number;
  task_type: string;
  target_column: string;
  models: string[];
  hyperparameters: {
    test_size: number;
    val_size: number;
    max_trials: number;
    timeout_hours: number;
  };
  preprocessing: {
    scale_features: boolean;
    handle_missing: boolean;
    feature_selection: boolean;
  };
}

export default function AutoML() {
  useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  
  const [datasets, setDatasets] = useState<any[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<number | null>(null);
  const [datasetColumns, setDatasetColumns] = useState<string[]>([]);
  const [config, setConfig] = useState<AutoMLConfig>({
    dataset_id: 0,
    task_type: 'classification',
    target_column: '',
    models: ['random_forest', 'xgboost', 'neural_network'],
    hyperparameters: {
      test_size: 0.2,
      val_size: 0.1,
      max_trials: 50,
      timeout_hours: 2
    },
    preprocessing: {
      scale_features: true,
      handle_missing: true,
      feature_selection: true
    }
  });
  const [loading, setLoading] = useState(false);
  const [starting, setStarting] = useState(false);

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
    // Check for datasetId parameter in URL to auto-select dataset
    const datasetIdParam = searchParams.get('datasetId');
    if (datasetIdParam && datasets.length > 0) {
      const datasetId = parseInt(datasetIdParam);
      const foundDataset = datasets.find((d: any) => d.id === datasetId);
      if (foundDataset) {
        setSelectedDataset(datasetId);
        setConfig(prev => ({ ...prev, dataset_id: datasetId }));
      }
    }
  }, [searchParams, datasets]);

  useEffect(() => {
    if (selectedDataset) {
      loadDatasetColumns();
    }
  }, [selectedDataset]);

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
      
      // Check for datasetId parameter in URL
      const urlParams = new URLSearchParams(window.location.search);
      const datasetParam = urlParams.get('datasetId');
      if (datasetParam) {
        const datasetId = parseInt(datasetParam);
        const foundDataset = apiDatasets.find((d: any) => d.id === datasetId);
        if (foundDataset) {
          setSelectedDataset(datasetId);
          setConfig(prev => ({ ...prev, dataset_id: datasetId }));
        }
      } else {
        // Auto-select most recent dataset if available
        const lastDataset = localStorage.getItem('lastUploadedDataset');
        if (lastDataset && apiDatasets.length > 0) {
          try {
            const datasetInfo = JSON.parse(lastDataset);
            const foundDataset = apiDatasets.find((d: any) => d.id === datasetInfo.id);
            if (foundDataset) {
              setSelectedDataset(datasetInfo.id);
            }
          } catch (error) {
            console.error('Error parsing last dataset:', error);
          }
        }
      }
    } catch (error) {
      console.error('Failed to load datasets:', error);
      // If API fails, try to load from localStorage only
      const savedDatasets = localStorage.getItem('availableDatasets');
      if (savedDatasets) {
        try {
          const localDatasets = JSON.parse(savedDatasets);
          const formattedDatasets = localDatasets.map((local: any) => ({
            id: local.id,
            name: local.name,
            dataset_type: local.type,
            size: local.size,
            created_at: local.uploadedAt
          }));
          setDatasets(formattedDatasets);
          
          // Auto-select the most recent one
          if (formattedDatasets.length > 0) {
            setSelectedDataset(formattedDatasets[0].id);
          }
        } catch (error) {
          console.error('Error parsing saved datasets:', error);
        }
      }
    }
  };

  const loadDatasetColumns = async () => {
    if (!selectedDataset) return;
    
    setLoading(true);
    console.log('Loading columns for dataset ID:', selectedDataset);
    try {
      const preview = await api.previewDataset(selectedDataset, 5);
      console.log('Full preview response:', preview);
      console.log('Preview data:', preview.data);
      console.log('Available columns:', preview.columns);
      console.log('Data length:', preview.data?.length);
      
      // If preview.columns is empty but data exists, extract columns from first row
      let columns = preview.columns || [];
      if ((!columns || columns.length === 0) && preview.data && preview.data.length > 0) {
        columns = Object.keys(preview.data[0]);
        console.log('Extracted columns from data:', columns);
      }
      
      setDatasetColumns(columns);
      console.log('Final columns set:', columns);
    } catch (error) {
      console.error('Failed to load dataset columns:', error);
      console.error('Error details:', error);
    } finally {
      setLoading(false);
    }
  };

  const availableModels = [
    { id: 'random_forest', name: 'Random Forest', description: 'Ensemble method with feature importance' },
    { id: 'xgboost', name: 'XGBoost', description: 'Gradient boosting for high performance' },
    { id: 'neural_network', name: 'Neural Network', description: 'Deep learning for complex patterns' },
    { id: 'svm', name: 'Support Vector Machine', description: 'Kernel-based classification' },
    { id: 'logistic_regression', name: 'Logistic Regression', description: 'Linear baseline model' },
    { id: 'naive_bayes', name: 'Naive Bayes', description: 'Probabilistic classifier' }
  ];

  const startAutoML = async () => {
    if (!selectedDataset || !config.target_column) return;

    setStarting(true);
    try {
      const jobConfig = {
        dataset_id: selectedDataset,
        task_type: config.task_type,
        target_column: config.target_column,
        encoding_method: 'auto',
        kmer_size: 3,
        test_size: config.hyperparameters.test_size,
        val_size: config.hyperparameters.val_size,
        optimize_hyperparams: true,
        n_models: config.models.length,
        generate_report: true
      };

      const job = await api.startWorkflow(jobConfig);
      
      if (job && job.job_id) {
        router.push(`/running/${job.job_id}`);
      } else {
        console.error('Failed to start AutoML: Invalid job response', job);
        alert('Failed to start training. Please try again.');
      }
    } catch (error) {
      console.error('Failed to start AutoML:', error);
    } finally {
      setStarting(false);
    }
  };

  return (
    <>
      <Header />
      <div className="min-h-[calc(100vh-64px)] bg-linear-to-b from-black via-zinc-950/80 to-black">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 padding-section">
          {/* Header */}
          <div className="section-spacing text-center-wrapper">
            <Button
              variant="ghost"
              onClick={() => router.back()}
              className="mb-6 self-start"
            >
              ← Back to Dashboard
            </Button>
            <h1 className="text-5xl sm:text-6xl font-bold mb-6 bg-linear-to-br from-white via-zinc-100 to-zinc-400 bg-clip-text text-transparent">
              Automated ML Model Builder
            </h1>
            <p className="text-xl text-zinc-300 max-w-7xl leading-relaxed">
              One-click machine learning with automatic model selection, hyperparameter tuning, and live training visualization
            </p>
          </div>

          <div className="grid lg:grid-cols-3 gap-8">
            {/* Configuration Panel */}
            <div className="lg:col-span-2 gap-section flex flex-col">
              {/* Step 1: Dataset Selection */}
              <Card className="p-6 border-zinc-700/50">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center font-bold">1</div>
                  <h2 className="text-xl font-bold text-white">Select Your Dataset</h2>
                </div>
                <p className="text-zinc-400 mb-6">Choose a dataset to train your machine learning model on</p>
                {datasets.length > 0 ? (
                  <div className="grid md:grid-cols-2 gap-4">
                    {datasets.map((dataset) => (
                      <div
                        key={dataset.id}
                        onClick={() => setSelectedDataset(dataset.id)}
                        className={`p-4 border rounded-lg cursor-pointer transition-all ${
                          selectedDataset === dataset.id
                            ? 'border-blue-500 bg-blue-500/10'
                            : 'border-zinc-700 hover:border-zinc-600 hover:bg-zinc-800/30'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="text-white font-medium">{dataset.name}</h3>
                          <span className="text-xs text-zinc-500 capitalize bg-zinc-700/50 px-2 py-1 rounded">
                            {dataset.dataset_type}
                          </span>
                        </div>
                        <p className="text-zinc-400 text-sm">
                          {(dataset.file_size / 1024).toFixed(1)} KB • {new Date(dataset.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Folder className="w-12 h-12 text-zinc-500 mx-auto mb-4" />
                    <p className="text-zinc-400 mb-4">No datasets found</p>
                    <Button onClick={() => router.push('/upload')}>
                      Upload Dataset
                    </Button>
                  </div>
                )}
              </Card>

              {/* Step 2: Configure Training */}
              {selectedDataset && (
                <Card className="p-6 border-zinc-700/50 card-spacing">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-8 h-8 bg-green-500 text-white rounded-full flex items-center justify-center font-bold">2</div>
                    <h2 className="text-xl font-bold text-white">Configure Training Settings</h2>
                  </div>
                  <p className="text-zinc-400 mb-6">Set up your machine learning experiment parameters</p>
                  <div className="space-y-6">
                    <div>
                      <label className="block text-white font-medium mb-2">Target Column</label>
                      {loading ? (
                        <div className="text-zinc-400">Loading columns...</div>
                      ) : (
                        <select
                          title='DS'
                          value={config.target_column}
                          onChange={(e) => setConfig({...config, target_column: e.target.value})}
                          className="w-full p-3 bg-zinc-800 border border-zinc-700 rounded-lg text-white"
                        >
                          <option value="">Select target column</option>
                          {datasetColumns.map((col) => (
                            <option key={col} value={col}>{col}</option>
                          ))}
                        </select>
                      )}
                    </div>

                    <div>
                      <label className="block text-white font-medium mb-2">Task Type</label>
                      <select
                      title='DS'
                        value={config.task_type}
                        onChange={(e) => setConfig({...config, task_type: e.target.value})}
                        className="w-full p-3 bg-zinc-800 border border-zinc-700 rounded-lg text-white"
                      >
                        <option value="classification">Classification</option>
                        <option value="regression">Regression</option>
                      </select>
                    </div>

                    <div className="grid md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-white font-medium mb-2">Test Size</label>
                        <input
                        title='DS'
                          type="range"
                          min="0.1"
                          max="0.4"
                          step="0.05"
                          value={config.hyperparameters.test_size}
                          onChange={(e) => setConfig({
                            ...config, 
                            hyperparameters: {...config.hyperparameters, test_size: parseFloat(e.target.value)}
                          })}
                          className="w-full"
                        />
                        <div className="text-zinc-400 text-sm mt-1">{(config.hyperparameters.test_size * 100).toFixed(0)}%</div>
                      </div>
                      <div>
                        <label className="block text-white font-medium mb-2">Validation Size</label>
                        <input
                        title='DS'
                          type="range"
                          min="0.05"
                          max="0.2"
                          step="0.025"
                          value={config.hyperparameters.val_size}
                          onChange={(e) => setConfig({
                            ...config, 
                            hyperparameters: {...config.hyperparameters, val_size: parseFloat(e.target.value)}
                          })}
                          className="w-full"
                        />
                        <div className="text-zinc-400 text-sm mt-1">{(config.hyperparameters.val_size * 100).toFixed(1)}%</div>
                      </div>
                    </div>
                  </div>
                </Card>
              )}

              {/* Step 3: Advanced Model Selection */}
              {selectedDataset && (
                <Card className="p-6 border-zinc-700/50 card-spacing">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-8 h-8 bg-purple-500 text-white rounded-full flex items-center justify-center font-bold">3</div>
                    <h2 className="text-xl font-bold text-white">Select ML Models</h2>
                  </div>
                  <p className="text-zinc-400 mb-6">Choose which machine learning models to train and compare automatically</p>
                  
                  

                  {/* Traditional ML Models */}
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                      <BarChart3 className="w-5 h-5 text-green-400" />
                      Traditional ML Models
                    </h3>
                    <div className="grid md:grid-cols-2 gap-4">
                      {[
                        { 
                          id: 'random_forest', 
                          name: 'Random Forest', 
                          description: 'Ensemble method excellent for feature importance analysis',
                          icon: TreePine,
                          iconColor: 'text-green-400',
                          bestFor: 'Feature interpretation'
                        },
                        { 
                          id: 'xgboost', 
                          name: 'XGBoost', 
                          description: 'Gradient boosting for high-performance predictions',
                          icon: Zap,
                          iconColor: 'text-yellow-400',
                          bestFor: 'High accuracy'
                        },
                        { 
                          id: 'svm', 
                          name: 'Support Vector Machine', 
                          description: 'Effective for high-dimensional biological data',
                          icon: Ruler,
                          iconColor: 'text-blue-400',
                          bestFor: 'Complex boundaries'
                        },
                        { 
                          id: 'neural_network', 
                          name: 'Neural Network (MLP)', 
                          description: 'Multi-layer perceptron for general classification',
                          icon: Calculator,
                          iconColor: 'text-purple-400',
                          bestFor: 'Non-linear patterns'
                        }
                      ].map((model) => {
                        const IconComponent = model.icon;
                        return (
                          <div
                            key={model.id}
                            onClick={() => {
                              const newModels = config.models.includes(model.id)
                                ? config.models.filter(m => m !== model.id)
                                : [...config.models, model.id];
                              setConfig({...config, models: newModels});
                            }}
                            className={`p-4 border rounded-lg cursor-pointer transition-all ${
                              config.models.includes(model.id)
                                ? 'border-green-500 bg-green-500/10'
                                : 'border-zinc-700 hover:border-zinc-600 hover:bg-zinc-800/30'
                            }`}
                          >
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <IconComponent className={`w-5 h-5 ${model.iconColor}`} />
                                <h4 className="text-white font-medium">{model.name}</h4>
                              </div>
                              {config.models.includes(model.id) && (
                                <CheckCircle2 className="w-5 h-5 text-green-400" />
                              )}
                            </div>
                            <p className="text-zinc-400 text-sm mb-2">{model.description}</p>
                            <div className="text-xs text-green-300 bg-green-900/30 px-2 py-1 rounded">
                              Best for: {model.bestFor}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                  
                  <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Lightbulb className="w-5 h-5 text-blue-400" />
                      <span className="text-blue-300 font-medium">AutoML Recommendation</span>
                    </div>
                    <p className="text-blue-200 text-sm">
                      Selected {config.models.length} models. AutoML will automatically train, tune hyperparameters, and compare all selected models to find the best performer for your data.
                    </p>
                  </div>
                </Card>
              )}

              {/* Preprocessing Options */}
              {selectedDataset && (
                <Card className="p-6 border-zinc-700/50 card-spacing">
                  <h2 className="text-xl font-bold text-white mb-4">Preprocessing Options</h2>
                  <div className="space-y-4">
                    {Object.entries(config.preprocessing).map(([key, value]) => (
                      <label key={key} className="flex items-center gap-3 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={value}
                          onChange={(e) => setConfig({
                            ...config,
                            preprocessing: {...config.preprocessing, [key]: e.target.checked}
                          })}
                          className="w-4 h-4 text-blue-600 bg-zinc-800 border-zinc-700 rounded"
                        />
                        <span className="text-white capitalize">
                          {key.replace('_', ' ')}
                        </span>
                        <span className="text-zinc-400 text-sm">
                          {key === 'scale_features' && '(StandardScaler normalization)'}
                          {key === 'handle_missing' && '(Impute missing values)'}
                          {key === 'feature_selection' && '(Automatic feature selection)'}
                        </span>
                      </label>
                    ))}
                  </div>
                </Card>
              )}
            </div>

            {/* Summary & Launch Panel */}
            <div className="gap-component flex flex-col">
              <Card className="p-6 border-zinc-700/50">
                <h2 className="text-xl font-bold text-white mb-4">AutoML Summary</h2>
                <div className="space-y-4">
                  <div>
                    <span className="text-zinc-400">Dataset:</span>
                    <div className="text-white font-medium">
                      {selectedDataset ? datasets.find(d => d.id === selectedDataset)?.name : 'Not selected'}
                    </div>
                  </div>
                  
                  {config.target_column && (
                    <div>
                      <span className="text-zinc-400">Target:</span>
                      <div className="text-white font-medium">{config.target_column}</div>
                    </div>
                  )}
                  
                  <div>
                    <span className="text-zinc-400">Task Type:</span>
                    <div className="text-white font-medium capitalize">{config.task_type}</div>
                  </div>
                  
                  <div>
                    <span className="text-zinc-400">Models:</span>
                    <div className="text-white font-medium">{config.models.length} selected</div>
                  </div>
                  
                  <div>
                    <span className="text-zinc-400">Data Split:</span>
                    <div className="text-white font-medium">
                      {(config.hyperparameters.test_size * 100).toFixed(0)}% test, {(config.hyperparameters.val_size * 100).toFixed(1)}% validation
                    </div>
                  </div>
                </div>

                <div className="mt-6 pt-6 border-t border-zinc-700/50">
                  <Button
                    onClick={startAutoML}
                    disabled={!selectedDataset || !config.target_column || config.models.length === 0 || starting}
                    size="lg"
                    className="w-full"
                  >
                    {starting ? (
                      <>
                        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white mr-3"></div>
                        Starting AutoML...
                      </>
                    ) : (
                      <>
                        <Rocket className="w-4 h-4 mr-2" />
                        Start AutoML Training
                      </>
                    )}
                  </Button>
                </div>
              </Card>

              {/* AutoML Features */}
              <Card className="p-6 border-zinc-700/50 card-spacing">
                <h3 className="text-lg font-bold text-white mb-4">AutoML Features</h3>
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-green-400 rounded-full"></span>
                    <span className="text-zinc-300 text-sm">Automatic hyperparameter tuning</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-blue-400 rounded-full"></span>
                    <span className="text-zinc-300 text-sm">Model comparison & selection</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-purple-400 rounded-full"></span>
                    <span className="text-zinc-300 text-sm">Live training visualization</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-orange-400 rounded-full"></span>
                    <span className="text-zinc-300 text-sm">Feature importance analysis</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-red-400 rounded-full"></span>
                    <span className="text-zinc-300 text-sm">Comprehensive evaluation metrics</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-yellow-400 rounded-full"></span>
                    <span className="text-zinc-300 text-sm">Automated report generation</span>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}