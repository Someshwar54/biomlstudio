'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Header } from '@/components/Header';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/useAuth';
import { 
  BarChart3, 
  Rocket, 
  Bot, 
  Database, 
  Upload, 
  Dna, 
  Search, 
  TrendingUp, 
  Target, 
  FileText,
  Activity,
  Zap,
  Plus,
  RefreshCw
} from 'lucide-react';

interface DashboardStats {
  totalProjects: number;
  activeTraining: number;
  completedModels: number;
  totalDatasets: number;
  recentDatasets: any[];
  recentJobs: any[];
}

export default function Dashboard() {
  const authResult = useAuth();
  const router = useRouter();
  
  const [stats, setStats] = useState<DashboardStats>({
    totalProjects: 0,
    activeTraining: 0,
    completedModels: 0,
    totalDatasets: 0,
    recentDatasets: [],
    recentJobs: []
  });
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  console.log('Dashboard component rendering, auth:', authResult);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const refreshData = () => {
    loadDashboardData(true);
  };

  const loadDashboardData = async (isRefresh = false) => {
    console.log(isRefresh ? 'Refreshing dashboard data...' : 'Loading dashboard data...');
    
    if (isRefresh) {
      setRefreshing(true);
      setError(null);
    }
    
    try {
      // Load datasets with limit for faster loading
      console.log('Loading datasets...');
      const datasets = await api.get<any>('/datasets/?limit=10');
      console.log('Datasets loaded:', datasets);
      
      // Load jobs with limit for faster loading
      console.log('Loading jobs...');
      const jobs = await api.get<any>('/jobs/?limit=10&sort_by=created_at&sort_order=desc');
      console.log('Jobs loaded:', jobs);

      // Handle both .items and .datasets/.jobs response formats
      const datasetItems = datasets.datasets || datasets.items || [];
      const jobItems = jobs.jobs || jobs.items || [];

      const newStats = {
        totalProjects: jobs.total || jobItems.length || 0,
        activeTraining: jobItems.filter((j: any) => j.status === 'running' || j.status === 'queued').length || 0,
        completedModels: jobItems.filter((j: any) => j.status === 'completed').length || 0,
        totalDatasets: datasets.total || datasetItems.length || 0,
        recentDatasets: datasetItems.slice(0, 5) || [],
        recentJobs: jobItems.slice(0, 5) || []
      };
      
      console.log('Setting stats:', newStats);
      setStats(newStats);
      setError(null);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      console.error('Error details:', error);
      setError(error instanceof Error ? error.message : 'Failed to load dashboard data');
    } finally {
      console.log('Dashboard loading complete');
      if (isRefresh) {
        setRefreshing(false);
      } else {
        setLoading(false);
      }
    }
  };

  if (loading) {
    return (
      <>
        <Header />
        <div className="flex-1 space-y-4 p-8 pt-6 max-w-7xl mx-auto">
          <div className="flex items-center justify-center min-h-[400px]">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          </div>
        </div>
      </>
    );
  }

  if (error) {
    return (
      <>
        <Header />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex-1 space-y-4 p-8 pt-6">
          <div className="flex items-center justify-between space-y-2">
            <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
          </div>
          <Card>
            <CardContent className="p-6">
              <div className="text-center">
                <div className="text-red-500 mb-4">
                  <Activity className="h-12 w-12 mx-auto mb-2" />
                  <p className="text-lg font-semibold">Failed to load dashboard</p>
                </div>
                <p className="text-muted-foreground mb-4">{error}</p>
                <Button onClick={refreshData}>
                  Try Again
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </>
    );
  }

  return (
    <>
      <Header />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex-1 space-y-4 p-8 pt-6">
        <div className="flex items-center justify-between space-y-2">
          <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
          <div className="flex items-center space-x-2">
            <Button 
              variant="outline" 
              onClick={refreshData}
              disabled={refreshing}
            >
              <RefreshCw className={`mr-2 h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
              {refreshing ? 'Refreshing...' : 'Refresh'}
            </Button>
            <Button onClick={() => router.push('/upload')}>
              <Plus className="mr-2 h-4 w-4" />
              Upload Dataset
            </Button>
          </div>
        </div>

        {/* Stats Overview */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 relative">
          {refreshing && (
            <div className="absolute inset-0  backdrop-blur-sm z-10 flex items-center justify-center rounded-lg">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          )}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Total Projects
              </CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.totalProjects}</div>
              <p className="text-xs text-muted-foreground">
                ML training projects
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Active Training
              </CardTitle>
              <Rocket className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.activeTraining}</div>
              <p className="text-xs text-muted-foreground">
                Running models
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Completed Models
              </CardTitle>
              <Bot className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.completedModels}</div>
              <p className="text-xs text-muted-foreground">
                Ready for inference
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Datasets
              </CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.totalDatasets}</div>
              <p className="text-xs text-muted-foreground">
                Available for training
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card className="cursor-pointer hover:bg-accent transition-colors" onClick={() => router.push('/upload')}>
            <CardContent className="flex items-center p-6">
              <Upload className="h-8 w-8 text-blue-600 mr-4" />
              <div>
                <CardTitle className="text-sm">Upload Dataset</CardTitle>
                <CardDescription>Upload FASTA or CSV files</CardDescription>
              </div>
            </CardContent>
          </Card>

          <Card className="cursor-pointer hover:bg-accent transition-colors" onClick={() => router.push('/automl')}>
            <CardContent className="flex items-center p-6">
              <Zap className="h-8 w-8 text-yellow-600 mr-4" />
              <div>
                <CardTitle className="text-sm">AutoML</CardTitle>
                <CardDescription>Automated model training</CardDescription>
              </div>
            </CardContent>
          </Card>

          <Card className="cursor-pointer hover:bg-accent transition-colors" onClick={() => router.push('/inference')}>
            <CardContent className="flex items-center p-6">
              <Target className="h-8 w-8 text-green-600 mr-4" />
              <div>
                <CardTitle className="text-sm">Inference</CardTitle>
                <CardDescription>Make predictions</CardDescription>
              </div>
            </CardContent>
          </Card>

          <Card className="cursor-pointer hover:bg-accent transition-colors" onClick={() => router.push('/results')}>
            <CardContent className="flex items-center p-6">
              <TrendingUp className="h-8 w-8 text-purple-600 mr-4" />
              <div>
                <CardTitle className="text-sm">Results</CardTitle>
                <CardDescription>View model performance</CardDescription>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Recent Activity */}
        <div className="grid gap-4 md:grid-cols-2">
          {/* Recent Datasets */}
          <Card className="relative">
            {refreshing && (
              <div className="absolute inset-0 backdrop-blur-sm z-10 flex items-center justify-center rounded-lg">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
              </div>
            )}
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Recent Datasets</CardTitle>
                <Button variant="outline" size="sm" onClick={() => router.push('/datasets')}>
                  View All
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {stats.recentDatasets.length > 0 ? (
                  stats.recentDatasets.map((dataset: any) => (
                    <div 
                      key={dataset.id} 
                      className="flex items-center justify-between p-3 rounded-lg border cursor-pointer hover:bg-accent transition-colors"
                      onClick={() => router.push(`/analysis/${dataset.id}`)}
                    >
                      <div className="flex-1">
                        <p className="font-medium">{dataset.name}</p>
                        <p className="text-sm text-muted-foreground capitalize">
                          {dataset.dataset_type} • {new Date(dataset.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <Badge variant="secondary">
                        {(dataset.file_size / 1024).toFixed(1)} KB
                      </Badge>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8">
                    <Database className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-muted-foreground mb-4">No datasets uploaded yet</p>
                    <Button size="sm" onClick={() => router.push('/upload')}>
                      Upload Dataset
                    </Button>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Recent Jobs */}
          <Card className="relative">
            {refreshing && (
              <div className="absolute inset-0 backdrop-blur-sm z-10 flex items-center justify-center rounded-lg">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
              </div>
            )}
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Recent Jobs</CardTitle>
                <Button variant="outline" size="sm" onClick={() => router.push('/jobs')}>
                  View All
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {stats.recentJobs.length > 0 ? (
                  stats.recentJobs.map((job: any) => (
                    <div 
                      key={job.id} 
                      className="flex items-center justify-between p-3 rounded-lg border cursor-pointer hover:bg-accent transition-colors"
                      onClick={() => router.push(`/running/${job.id}`)}
                    >
                      <div className="flex-1">
                        <p className="font-medium">{job.name}</p>
                        <p className="text-sm text-muted-foreground">{job.job_type}</p>
                      </div>
                      <Badge 
                        variant={
                          job.status === 'completed' ? 'default' :
                          job.status === 'running' ? 'secondary' :
                          job.status === 'failed' ? 'destructive' : 'outline'
                        }
                      >
                        {job.status?.toUpperCase()}
                      </Badge>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8">
                    <Activity className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-muted-foreground mb-4">No training jobs yet</p>
                    <Button size="sm" onClick={() => router.push('/automl')}>
                      Start Training
                    </Button>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </>
  );
}