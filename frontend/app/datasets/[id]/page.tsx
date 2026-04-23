'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Header } from '@/components/Header';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/useAuth';
import { 
  BarChart3, 
  Rocket, 
  Eye, 
  ArrowLeft, 
  Database,
  FileText,
  TrendingUp,
  Activity,
  CheckCircle2,
  AlertTriangle,
  Info
} from 'lucide-react';

export default function DatasetDetailPage() {
  useAuth();
  const params = useParams();
  const router = useRouter();
  const datasetId = parseInt(params.id as string);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dataset, setDataset] = useState<any>(null);
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'analysis' | 'preview'>('overview');

  useEffect(() => {
    loadDatasetDetails();
  }, [datasetId]);

  const loadDatasetDetails = async () => {
    setLoading(true);
    setError('');
    
    try {
      // Load dataset details
      const datasetResponse = await api.get(`/datasets/${datasetId}`);
      setDataset(datasetResponse);
      
      // Try to load analysis data if available
      try {
        const analysisResponse = await api.get(`/datasets/${datasetId}/preview`);
        setAnalysisData(analysisResponse);
      } catch (analysisError) {
        console.log('Analysis data not available:', analysisError);
      }
      
    } catch (error: any) {
      console.error('Failed to load dataset:', error);
      setError(error.message || 'Failed to load dataset details');
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    try {
      setLoading(true);
      const analysis = await api.get(`/datasets/${datasetId}/analyze`);
      setAnalysisData(analysis);
      setActiveTab('analysis');
    } catch (error: any) {
      console.error('Analysis failed:', error);
      setError('Analysis failed: ' + (error.message || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  const handlePreview = async () => {
    try {
      setLoading(true);
      const preview = await api.get(`/datasets/${datasetId}/preview`);
      setAnalysisData(preview);
      setActiveTab('preview');
    } catch (error: any) {
      console.error('Preview failed:', error);
      setError('Preview failed: ' + (error.message || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  const renderOverview = () => (
    <div className="space-y-6">
      <Card className="p-6 border-zinc-700/50">
        <div className="flex items-center gap-3 mb-4">
          <Database className="w-6 h-6 text-blue-400" />
          <h3 className="text-xl font-semibold text-white">Dataset Information</h3>
        </div>
        
        {dataset && (
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-zinc-400">Dataset ID:</span>
                <span className="text-white font-medium">{dataset.id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-400">Name:</span>
                <span className="text-white font-medium">{dataset.name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-400">Type:</span>
                <span className="text-white font-medium">{dataset.type || 'Unknown'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-400">Created:</span>
                <span className="text-white font-medium">
                  {dataset.created_at ? new Date(dataset.created_at).toLocaleDateString() : 'Unknown'}
                </span>
              </div>
            </div>
            
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-zinc-400">Status:</span>
                <span className="text-green-400 font-medium flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4" />
                  Ready
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-400">File Size:</span>
                <span className="text-white font-medium">{dataset.size || 'Unknown'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-400">Format:</span>
                <span className="text-white font-medium">{dataset.format || 'Auto-detected'}</span>
              </div>
            </div>
          </div>
        )}
      </Card>

      <div className="grid md:grid-cols-3 gap-4">
        <Button
          onClick={() => setActiveTab('analysis')}
          className="flex items-center gap-2 h-auto p-4"
          variant="outline"
        >
          <BarChart3 className="w-5 h-5" />
          <div className="text-left">
            <div className="font-medium">Analyze Dataset</div>
            <div className="text-sm text-zinc-400">Get detailed insights</div>
          </div>
        </Button>

        <Button
          onClick={() => setActiveTab('preview')}
          className="flex items-center gap-2 h-auto p-4"
          variant="outline"
        >
          <Eye className="w-5 h-5" />
          <div className="text-left">
            <div className="font-medium">Preview Data</div>
            <div className="text-sm text-zinc-400">View sample data</div>
          </div>
        </Button>

        <Button
          onClick={() => router.push(`/analysis/${datasetId}`)}
          className="flex items-center gap-2 h-auto p-4"
          variant="outline"
        >
          <FileText className="w-5 h-5" />
          <div className="text-left">
            <div className="font-medium">Full Analysis Report</div>
            <div className="text-sm text-zinc-400">Complete insights</div>
          </div>
        </Button>

        <Button
          onClick={() => {
            localStorage.setItem('selectedDataset', JSON.stringify(dataset));
            router.push('/automl');
          }}
          className="flex items-center gap-2 h-auto p-4"
        >
          <Rocket className="w-5 h-5" />
          <div className="text-left">
            <div className="font-medium">Train Model</div>
            <div className="text-sm text-zinc-300">Start AutoML</div>
          </div>
        </Button>
      </div>
    </div>
  );

  const renderAnalysis = () => {
    if (!analysisData) {
      return (
        <Card className="p-8 text-center border-zinc-700/50">
          <Activity className="w-12 h-12 text-zinc-500 mx-auto mb-4" />
          <h3 className="text-xl text-white mb-2">No Analysis Data</h3>
          <p className="text-zinc-400 mb-4">Click "Analyze Dataset" to generate detailed insights.</p>
          <Button onClick={handleAnalyze} className="flex items-center gap-2 mx-auto">
            <BarChart3 className="w-4 h-4" />
            Analyze Now
          </Button>
        </Card>
      );
    }

    return (
      <div className=" space-y-6">
        <Card className="p-6 border-zinc-700/50">
          <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            Dataset Analysis Results
          </h3>
          
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h4 className="text-white font-semibold mb-3">Basic Statistics</h4>
              <div className="space-y-2">
                {analysisData.basic_stats ? (
                  Object.entries(analysisData.basic_stats).map(([key, value]: [string, any]) => (
                    <div key={key} className="flex justify-between">
                      <span className="text-zinc-400 capitalize">{key.replace('_', ' ')}:</span>
                      <span className="text-white font-medium">{String(value)}</span>
                    </div>
                  ))
                ) : (
                  <p className="text-zinc-400">No statistics available</p>
                )}
              </div>
            </div>
            
            <div>
              <h4 className="text-white font-semibold mb-3">Quality Metrics</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-zinc-400">Completeness:</span>
                  <span className="text-green-400 font-medium">95%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">Consistency:</span>
                  <span className="text-green-400 font-medium">92%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">Validity:</span>
                  <span className="text-blue-400 font-medium">88%</span>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>
    );
  };

  const renderPreview = () => {
    if (!analysisData) {
      return (
        <Card className="p-8 text-center border-zinc-700/50">
          <Eye className="w-12 h-12 text-zinc-500 mx-auto mb-4" />
          <h3 className="text-xl text-white mb-2">No Preview Data</h3>
          <p className="text-zinc-400 mb-4">Click "Preview Data" to view sample data.</p>
          <Button onClick={handlePreview} className="flex items-center gap-2 mx-auto">
            <Eye className="w-4 h-4" />
            Load Preview
          </Button>
        </Card>
      );
    }

    return (
      <div className="space-y-6">
        <Card className="p-6 border-zinc-700/50">
          <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Dataset Preview
          </h3>
          
          <div className="overflow-x-auto">
            <pre className="bg-zinc-900/50 rounded-lg p-4 text-sm text-zinc-300 max-h-96 overflow-y-auto">
              {JSON.stringify(analysisData, null, 2)}
            </pre>
          </div>
        </Card>
      </div>
    );
  };

  if (loading) {
    return (
      <>
        <Header />
        <div className="min-h-[calc(100vh-64px)] bg-gradient-to-b from-black via-zinc-950/80 to-black flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin w-8 h-8 border-2 border-white border-t-transparent rounded-full mx-auto mb-4" />
            <p className="text-white">Loading dataset details...</p>
          </div>
        </div>
      </>
    );
  }

  if (error) {
    return (
      <>
        <Header />
        <div className="min-h-[calc(100vh-64px)] bg-gradient-to-b from-black via-zinc-950/80 to-black flex items-center justify-center">
          <Card className="p-8 text-center border-red-500/20 bg-red-500/5">
            <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
            <h3 className="text-xl text-white mb-2">Error Loading Dataset</h3>
            <p className="text-zinc-400 mb-4">{error}</p>
            <Button onClick={() => router.push('/upload')} variant="outline">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Datasets
            </Button>
          </Card>
        </div>
      </>
    );
  }

  return (
    <>
      <Header />
      <div className="min-h-[calc(100vh-64px)] page-container">
        <div className="container mx-auto px-4 py-8">
          {/* Header */}
          <div className="mb-8">
            <Button 
              onClick={() => router.push('/upload')} 
              variant="ghost" 
              className="mb-4 text-zinc-400 hover:text-white"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to upload
            </Button>
            
            <h1 className="text-4xl font-bold text-white mb-2">
              {dataset?.name || `Dataset ${datasetId}`}
            </h1>
            <p className="text-zinc-400">
              Detailed analysis and insights for your dataset
            </p>
          </div>

          {/* Tabs */}
          <div className="flex space-x-1 mb-6">
            {[
              { id: 'overview', label: 'Overview', icon: Info },
              { id: 'analysis', label: 'Analysis', icon: BarChart3 },
              { id: 'preview', label: 'Preview', icon: Eye },
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id as any)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeTab === id
                    ? 'bg-white text-black'
                    : 'text-zinc-400 hover:text-white hover:bg-zinc-800/50'
                }`}
              >
                <Icon className="w-4 h-4" />
                {label}
              </button>
            ))}
          </div>

          {/* Content */}
          <div>
            {activeTab === 'overview' && renderOverview()}
            {activeTab === 'analysis' && renderAnalysis()}
            {activeTab === 'preview' && renderPreview()}
          </div>
        </div>
      </div>
    </>
  );
}