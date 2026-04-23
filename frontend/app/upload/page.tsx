'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Progress } from '@/components/ui/ProgressBar';
import { Separator } from '@/components/ui/Separator';
import { Header } from '@/components/Header';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/useAuth';
import { 
  Upload as UploadIcon, 
  FileText, 
  Database, 
  CheckCircle2, 
  AlertTriangle, 
  Loader2,
  ArrowRight,
  FileSpreadsheet,
  Dna,
  BarChart3,
  Brain
} from 'lucide-react';

export default function Upload() {
  useAuth();
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [fileInfo, setFileInfo] = useState<any>(null);
  const [uploadedDatasetId, setUploadedDatasetId] = useState<number | null>(null);
  const [preprocessing, setPreprocessing] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleFileSelect = (selectedFile: File) => {
    if (!selectedFile) return;

    // Validate file type
    const allowedTypes = ['.csv', '.fasta', '.fas', '.fa', '.txt'];
    const fileExtension = '.' + selectedFile.name.split('.').pop()?.toLowerCase();
    
    if (!allowedTypes.includes(fileExtension)) {
      setError('Please upload a CSV or FASTA file (.csv, .fasta, .fas, .fa, .txt)');
      return;
    }

    // Validate file size (max 100MB)
    if (selectedFile.size > 100 * 1024 * 1024) {
      setError('File size must be less than 100MB');
      return;
    }

    setFile(selectedFile);
    setError('');
    setFileInfo({
      name: selectedFile.name,
      size: selectedFile.size,
      sizeFormatted: formatFileSize(selectedFile.size),
      type: fileExtension.includes('csv') ? 'CSV' : 'FASTA'
    });
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      handleFileSelect(droppedFile);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  };

  const uploadFile = async () => {
    if (!file) return;

    setUploading(true);
    setError('');

    try {
      const fileName = file.name.replace(/\.[^/.]+$/, ""); // Remove extension for name
      const datasetType = file.name.toLowerCase().endsWith('.fasta') ? 'dna' : 'general';
      
      const response = await api.uploadDataset(file, fileName, datasetType);
      
      if (response.id) {
        setUploadedDatasetId(response.id);
        
        // Create dataset object for localStorage
        const datasetInfo = {
          id: response.id,
          name: response.name || file.name,
          type: response.dataset_type || datasetType,
          size: file.size,
          uploadedAt: new Date().toISOString(),
          filename: file.name,
          file_path: response.file_path
        };
        
        // Save to localStorage for persistence
        localStorage.setItem('lastUploadedDataset', JSON.stringify(datasetInfo));
        
        // Update available datasets list in localStorage
        const savedDatasets = localStorage.getItem('availableDatasets');
        let datasets = [];
        if (savedDatasets) {
          try {
            datasets = JSON.parse(savedDatasets);
          } catch (error) {
            console.error('Error parsing saved datasets:', error);
          }
        }
        
        // Add new dataset to the list (avoid duplicates)
        const existingIndex = datasets.findIndex((d: any) => d.id === response.id);
        if (existingIndex >= 0) {
          datasets[existingIndex] = datasetInfo;
        } else {
          datasets.unshift(datasetInfo); // Add to beginning of list
        }
        
        localStorage.setItem('availableDatasets', JSON.stringify(datasets));
        
        // Trigger a storage event to notify other tabs/pages
        window.dispatchEvent(new StorageEvent('storage', {
          key: 'availableDatasets',
          newValue: JSON.stringify(datasets)
        }));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const startPreprocessing = async () => {
    if (!uploadedDatasetId) return;
    
    setPreprocessing(true);
    try {
      const preprocessingConfig = {
        steps: [
          {
            name: "handle_missing_values",
            parameters: { strategy: "mean" },
            enabled: true
          },
          {
            name: "feature_scaling",
            parameters: { method: "standard" },
            enabled: true
          }
        ],
        output_name: "preprocessed_dataset",
        save_intermediate: false
      };
      
      await api.post(`/datasets/${uploadedDatasetId}/preprocess`, preprocessingConfig);
      router.push(`/analysis/${uploadedDatasetId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Preprocessing failed');
      setPreprocessing(false);
    }
  };

  return (
    <>
      <Header />
      <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">Upload Dataset</h1>
          <p className="text-muted-foreground">
            Upload your bioinformatics data to get started with automated ML analysis
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {/* Upload Section */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <UploadIcon className="h-5 w-5" />
                File Upload
              </CardTitle>
              <CardDescription>
                Drag and drop your file or click to browse. Supports CSV and FASTA formats.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {!file ? (
                <div
                  className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                    dragOver
                      ? 'border-primary bg-primary/5'
                      : 'border-muted-foreground/25 hover:border-muted-foreground/50'
                  }`}
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Database className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <div className="space-y-2">
                    <p className="text-sm font-medium">
                      Drag and drop your file here, or click to browse
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Supports .csv, .fasta, .fas, .fa, .txt files up to 100MB
                    </p>
                  </div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    className="hidden"
                    accept=".csv,.fasta,.fas,.fa,.txt"
                    onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
                    aria-label="Upload dataset file"
                  />
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center space-x-4 p-4 border rounded-lg">
                    {fileInfo?.type === 'CSV' ? (
                      <FileSpreadsheet className="h-10 w-10 text-green-600" />
                    ) : (
                      <Dna className="h-10 w-10 text-blue-600" />
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{fileInfo?.name}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="secondary">{fileInfo?.type}</Badge>
                        <span className="text-xs text-muted-foreground">
                          {fileInfo?.sizeFormatted}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <Button 
                      onClick={uploadFile} 
                      disabled={uploading || !!uploadedDatasetId}
                      className="flex-1"
                    >
                      {uploading ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Uploading...
                        </>
                      ) : uploadedDatasetId ? (
                        <>
                          <CheckCircle2 className="mr-2 h-4 w-4" />
                          Uploaded
                        </>
                      ) : (
                        <>
                          <UploadIcon className="mr-2 h-4 w-4" />
                          Upload File
                        </>
                      )}
                    </Button>
                    
                    <Button
                      variant="outline"
                      onClick={() => {
                        setFile(null);
                        setFileInfo(null);
                        setUploadedDatasetId(null);
                        setError('');
                      }}
                    >
                      Clear
                    </Button>
                  </div>

                  {uploadedDatasetId && (
                    <>
                      <Separator />
                      <div className="space-y-2">
                        <Button 
                          onClick={() => router.push(`/automl?datasetId=${uploadedDatasetId}`)}
                          className="w-full"
                          variant="default"
                        >
                          <Brain className="mr-2 h-4 w-4" />
                          Start AutoML Training
                          <ArrowRight className="ml-2 h-4 w-4" />
                        </Button>
                        
                        <Button 
                          onClick={startPreprocessing} 
                          disabled={preprocessing}
                          className="w-full"
                          variant="outline"
                        >
                          {preprocessing ? (
                            <>
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              Processing...
                            </>
                          ) : (
                            <>
                              <BarChart3 className="mr-2 h-4 w-4" />
                              Start Analysis
                              <ArrowRight className="ml-2 h-4 w-4" />
                            </>
                          )}
                        </Button>
                      </div>
                    </>
                  )}
                </div>
              )}

              {error && (
                <div className="flex items-center space-x-2 text-sm text-destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <span>{error}</span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Info Section */}
          <Card>
            <CardHeader>
              <CardTitle>Supported Formats</CardTitle>
              <CardDescription>
                Learn about the file formats we support for bioinformatics analysis
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex items-start space-x-3">
                  <FileSpreadsheet className="h-5 w-5 text-green-600 mt-0.5" />
                  <div>
                    <p className="font-medium">CSV Files</p>
                    <p className="text-sm text-muted-foreground">
                      Tabular data with headers. Perfect for structured datasets with features and labels.
                    </p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-3">
                  <Dna className="h-5 w-5 text-blue-600 mt-0.5" />
                  <div>
                    <p className="font-medium">FASTA Files</p>
                    <p className="text-sm text-muted-foreground">
                      Sequence data for proteins or DNA. Supports .fasta, .fas, .fa, and .txt extensions.
                    </p>
                  </div>
                </div>
              </div>

              <Separator />

              <div className="space-y-2">
                <p className="font-medium text-sm">File Requirements:</p>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• Maximum file size: 100MB</li>
                  <li>• UTF-8 text encoding</li>
                  <li>• For CSV: Include column headers</li>
                  <li>• For FASTA: Standard format with sequence IDs</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>What's Next?</CardTitle>
            <CardDescription>
              After uploading your dataset, you can explore these powerful features
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="flex items-center space-x-3 p-4 rounded-lg border">
                <BarChart3 className="h-8 w-8 text-blue-600" />
                <div>
                  <p className="font-medium">Dataset Analysis</p>
                  <p className="text-sm text-muted-foreground">Explore data quality and statistics</p>
                </div>
              </div>
              
              <div className="flex items-center space-x-3 p-4 rounded-lg border">
                <FileText className="h-8 w-8 text-green-600" />
                <div>
                  <p className="font-medium">Feature Engineering</p>
                  <p className="text-sm text-muted-foreground">Automated preprocessing pipelines</p>
                </div>
              </div>
              
              <div className="flex items-center space-x-3 p-4 rounded-lg border">
                <CheckCircle2 className="h-8 w-8 text-purple-600" />
                <div>
                  <p className="font-medium">AutoML Training</p>
                  <p className="text-sm text-muted-foreground">One-click model generation</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </>
  );
}