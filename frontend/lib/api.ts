const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_PREFIX = '/api/v1';

class ApiClient {
  private token: string | null = null;

  setToken(token: string) {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('token', token);
    }
  }

  getToken() {
    if (!this.token && typeof window !== 'undefined') {
      this.token = localStorage.getItem('token');
    }
    return this.token;
  }

  clearToken() {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
    }
  }

  private async request<T>(endpoint: string, options: RequestInit = {}, customTimeout?: number): Promise<T> {
    const token = this.getToken();
    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }

    // Use custom timeout or default based on endpoint
    const timeout = customTimeout || (endpoint.includes('/dna-discovery/') ? 300000 : 10000); // 5 minutes for DNA analysis, 10 seconds for others
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(`${API_BASE}${API_PREFIX}${endpoint}`, {
        ...options,
        headers,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      return response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Request timeout - server is taking too long to respond. Try analyzing fewer sequences at once.');
      }
      throw error;
    }
  }

  async uploadDataset(file: File, name: string, datasetType: string = 'general') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', name);
    formData.append('dataset_type', datasetType);

    return this.request<any>('/datasets/upload', {
      method: 'POST',
      body: formData,
    });
  }

  async getDataset(id: number) {
    return this.request<any>(`/datasets/${id}`);
  }

  async analyzeDataset(id: number) {
    return this.request<any>(`/datasets/${id}/analyze`);
  }

  async visualizeDataset(id: number) {
    return this.request<any>(`/datasets/${id}/visualizations`);
  }

  async previewDataset(id: number, rows: number = 5) {
    return this.request<any>(`/datasets/${id}/preview?rows=${rows}`);
  }

  async startAnalysis(datasetId: number, config: {
    target_column: string;
    analysis_type: string;
    feature_columns?: string;
  }) {
    const params = new URLSearchParams({
      target_column: config.target_column,
      analysis_type: config.analysis_type,
      ...(config.feature_columns && { feature_columns: config.feature_columns }),
    });

    return this.request<any>(`/analysis/auto-analyze/${datasetId}?${params}`, {
      method: 'POST',
    });
  }

  async getJobStatus(jobId: number) {
    return this.request<any>(`/jobs/${jobId}`);
  }

  async getJobResults(jobId: number) {
    return this.request<any>(`/jobs/${jobId}/results`);
  }

  async login(email: string, password: string) {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);

    const response = await this.request<any>('/auth/login', {
      method: 'POST',
      body: formData,
    });

    if (response.access_token) {
      this.setToken(response.access_token);
    }

    return response;
  }

  async register(email: string, password: string, fullName: string) {
    return this.request<any>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name: fullName }),
    });
  }

  async analyzeDataset(id: number) {
    return this.request<any>(`/datasets/${id}/analyze`);
  }

  async visualizeDataset(id: number) {
    return this.request<any>(`/datasets/${id}/visualize`);
  }

  async getDatasetStats(id: number) {
    return this.request<any>(`/datasets/${id}/stats`);
  }

  // Workflow endpoints
  async startWorkflow(config: {
    dataset_id: number;
    task_type: string;
    target_column: string;
    encoding_method: string;
    kmer_size: number;
    test_size: number;
    val_size: number;
    optimize_hyperparams: boolean;
    n_models: number;
    generate_report: boolean;
  }) {
    return this.request<any>('/workflow/start', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async startWorkflow(config: any) {
    return this.request<any>('/workflow/start', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async getWorkflowStatus(jobId: number) {
    return this.request<any>(`/workflow/${jobId}/status`);
  }

  async getWorkflowResults(jobId: number) {
    return this.request<any>(`/workflow/${jobId}/results`);
  }

  getWorkflowModelDownloadUrl(jobId: number) {
    const token = this.getToken();
    return `${API_BASE}${API_PREFIX}/workflow/${jobId}/download/model?token=${token}`;
  }

  getWorkflowReportDownloadUrl(jobId: number) {
    const token = this.getToken();
    return `${API_BASE}${API_PREFIX}/workflow/${jobId}/download/report?token=${token}`;
  }

  // Public HTTP methods
  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  // DNA Discovery methods
  async analyzeDNA(data: {
    sequences: string[];
    sequence_ids?: string[];
    analysis_config?: any;
  }) {
    // Enhanced batch processing for massive datasets
    const maxSequencesPerRequest = 1000;  // Increased limit
    const maxBasePairsPerRequest = 10000000; // 10M bp limit
    
    const totalBP = data.sequences.reduce((sum, seq) => sum + seq.length, 0);
    
    // For truly massive datasets (like 22M bp), enable server-side batch processing
    if (totalBP > 1000000) { // > 1M bp triggers batch processing
      console.log(`🔄 Large dataset detected (${totalBP.toLocaleString()} bp). Enabling batch processing mode.`);
      
      // Add batch processing flag to analysis config
      const batchConfig = {
        ...data.analysis_config,
        force_batch_processing: true,
        batch_mode: 'streaming'
      };
      
      return this.request<any>('/dna-discovery/analyze-comprehensive', {
        method: 'POST',
        body: JSON.stringify({
          ...data,
          analysis_config: batchConfig
        }),
      }, 1800000); // 30 minute timeout for massive datasets
    }
    
    // For large but manageable datasets
    if (data.sequences.length > maxSequencesPerRequest || totalBP > maxBasePairsPerRequest) {
      console.warn(`⚠️ Dataset size (${data.sequences.length} sequences, ${totalBP.toLocaleString()} bp) exceeds recommended limits. Processing first portion.`);
      
      const limitedData = { 
        ...data, 
        sequences: data.sequences.slice(0, maxSequencesPerRequest)
      };
      if (data.sequence_ids) {
        limitedData.sequence_ids = data.sequence_ids.slice(0, maxSequencesPerRequest);
      }
      
      return this.request<any>('/dna-discovery/analyze-comprehensive', {
        method: 'POST',
        body: JSON.stringify(limitedData),
      }, 900000); // 15 minute timeout
    }
    
    return this.request<any>('/dna-discovery/analyze-comprehensive', {
      method: 'POST',
      body: JSON.stringify(data),
    }, 300000); // 5 minute timeout
  }

  async discoverGenes(data: { sequences: string[]; sequence_ids?: string[] }) {
    return this.request<any>('/dna-discovery/discover-genes', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async identifyMutations(data: { sequences: string[]; sequence_ids?: string[] }) {
    return this.request<any>('/dna-discovery/identify-mutations', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async detectPathogens(data: { sequences: string[]; sequence_ids?: string[] }) {
    return this.request<any>('/dna-discovery/detect-pathogens', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
}

export const api = new ApiClient();

// Export individual methods for convenience
export const analyzeDataset = (id: number) => api.analyzeDataset(id);
export const visualizeDataset = (id: number) => api.visualizeDataset(id);
