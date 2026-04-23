export interface Dataset {
  id: number;
  name: string;
  file_path: string;
  file_size: number;
  dataset_type: string;
  created_at: string;
}

export interface DatasetPreview {
  dataset_id: number;
  preview_data: Record<string, any>[];
  total_rows: number;
  columns?: string[];
}

export interface Job {
  id: number;
  job_type: string;
  name: string;
  status: 'pending' | 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  config: any;
  progress?: number;
  result?: any;
  error_message?: string;
  created_at: string;
  updated_at?: string;
}

export interface JobResults {
  metrics?: {
    accuracy?: number;
    precision?: number;
    recall?: number;
    f1_score?: number;
    roc_auc?: number;
    mse?: number;
    rmse?: number;
    r2?: number;
    train_score?: number;
    val_score?: number;
    primary_score?: number;
  };
  feature_importance?: Array<{ feature: string; importance: number }>;
  confusion_matrix?: number[][];
  sequence_stats?: {
    total_sequences: number;
    avg_length: number;
    sequence_type: string;
  };
  plots?: {
    confusion_matrix?: string;
    feature_importance?: string;
    roc_curve?: string;
  };
  best_model?: string;
  models_trained?: Array<{
    model_name: string;
    model_type: string;
    training_time: number;
    metrics: {
      train_score: number;
      val_score: number;
      primary_score: number;
    };
    is_best: boolean;
  }>;
  training_time?: number;
  shap_explanations?: SHAPExplanation;
}

export interface FeatureContribution {
  feature: string;
  value: number;
  shap_value: number;
  contribution: 'positive' | 'negative';
}

export interface TopFeature {
  feature: string;
  importance: number;
  mean_shap: number;
  std_shap: number;
}

export interface SHAPSummary {
  feature_importance: Record<string, number>;
  top_features: TopFeature[];
  total_features: number;
}

export interface SHAPPlots {
  summary_plot?: string;
  bar_plot?: string;
  waterfall_plot?: string;
  force_plot?: string;
}

export interface SHAPExplanation {
  success: boolean;
  shap_values?: number[][];
  feature_names?: string[];
  plots?: SHAPPlots;
  summary?: SHAPSummary;
  explainer_type?: string;
  error?: string;
  timestamp?: string;
}

export interface PredictionExplanation {
  prediction: number;
  probability?: number[];
  contributions: FeatureContribution[];
  base_value?: number;
}
