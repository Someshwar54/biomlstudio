# BioMLStudio - Complete Workflow Integration

## Overview
This document describes the completed end-to-end ML workflow integration for BioMLStudio, combining all services into a unified API that handles the complete pipeline from data upload to model export.

### Backend Services (Completed)
1. **PreprocessingService** (`app/services/preprocessing_service.py`)
   - Data loading and cleaning
   - Missing value handling
   - Sequence encoding (k-mer, one-hot, integer)
   - Feature engineering (GC content, composition, molecular weight)
   - Data splitting (train/val/test with stratification)

2. **AutoMLService** (`app/services/automl_service.py`)
   - Intelligent model selection based on task type
   - Support for 9 ML algorithms
   - Model ranking based on data characteristics
   - Task-specific recommendations

3. **TrainingService** (`app/services/training_service.py`)
   - Multi-model training with monitoring
   - Hyperparameter optimization
   - Comprehensive evaluation metrics
   - Real-time progress tracking

4. **VisualizationService** (`app/services/visualization_service.py`)
   - ROC curves
   - Confusion matrices
   - Feature importance plots
   - Dataset analysis visualizations

5. **ExportService** (`app/services/export_service.py`)
   - Model packaging with metadata
   - PDF report generation
   - Preprocessing pipeline export
   - README generation

### Workflow API (`app/api/routes/workflow.py`)

#### Endpoints

**POST `/api/v1/workflow/start`**
Starts the complete ML workflow in the background.

Request Body:
```json
{
  "dataset_id": 1,
  "task_type": "protein_classification",
  "target_column": "label",
  "encoding_method": "kmer",
  "kmer_size": 3,
  "test_size": 0.2,
  "val_size": 0.1,
  "optimize_hyperparams": false,
  "n_models": 3,
  "generate_report": true
}
```

Response:
```json
{
  "job_id": 123,
  "status": "started",
  "message": "ML workflow started. Processing dataset: my_dataset.fasta"
}
```

**GET `/api/v1/workflow/{job_id}/status`**
Get current workflow status and progress.

Response:
```json
{
  "job_id": 123,
  "status": "running",
  "progress": 65,
  "result": null,
  "error_message": null,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:35:00"
}
```

**GET `/api/v1/workflow/{job_id}/results`**
Get complete workflow results (only when completed).

Response:
```json
{
  "job_id": 123,
  "dataset_id": 1,
  "results": {
    "success": true,
    "best_model": "Random Forest",
    "metrics": {
      "training": {
        "accuracy": 0.95,
        "f1_score": 0.94
      },
      "validation": {
        "accuracy": 0.92,
        "f1_score": 0.91
      }
    },
    "artifacts": {
      "model": "/path/to/model.joblib",
      "report": "/path/to/report.pdf",
      "visualizations": {
        "confusion_matrix": "base64_encoded_image",
        "roc_curve": "base64_encoded_image"
      }
    },
    "training_time": 45.3
  },
  "config": {
    "task_type": "protein_classification",
    "encoding_method": "kmer"
  }
}
```

**GET `/api/v1/workflow/{job_id}/download/model`**
Download the trained model file (.joblib).

**GET `/api/v1/workflow/{job_id}/download/report`**
Download the PDF report.

### Workflow Execution Steps

The `execute_ml_workflow` function orchestrates the complete pipeline:

1. **Preprocessing (Progress: 10-30%)**
   - Load dataset
   - Clean and validate data
   - Encode sequences
   - Engineer features
   - Split into train/val/test sets

2. **Model Selection & Training (Progress: 30-80%)**
   - AutoML selects best models for task
   - Train multiple models
   - Optimize hyperparameters (if enabled)
   - Track training progress

3. **Evaluation & Export (Progress: 80-100%)**
   - Evaluate all models
   - Generate metrics and visualizations
   - Save best model
   - Create PDF report
   - Package artifacts

### Frontend Pages (Completed)

1. **Configure Page** (`app/configure/[id]/page.tsx`)
   - Task type selection
   - Target column configuration
   - Encoding method settings
   - Training options
   - Submits to workflow API

2. **Running Page** (`app/running/[id]/page.tsx`)
   - Real-time progress monitoring
   - Status updates every 3 seconds
   - Progress bar with messages
   - Auto-redirect to results when complete

3. **Results Page** (`app/results/[id]/page.tsx`)
   - Summary cards (best model, accuracy, time)
   - Tabbed interface:
     - Overview: Configuration and summary
     - Metrics: Training and validation metrics
     - Visualizations: Embedded plots
   - Download buttons for model and report

### Frontend API Client Updates

Added to `lib/api.ts`:
```typescript
async startWorkflow(config): Promise<WorkflowStartResponse>
async getWorkflowStatus(jobId): Promise<WorkflowStatus>
async getWorkflowResults(jobId): Promise<WorkflowResults>
getWorkflowModelDownloadUrl(jobId): string
getWorkflowReportDownloadUrl(jobId): string
```

## Complete User Journey

1. **Login/Register** → User authenticates
2. **Upload Dataset** → FASTA/CSV file uploaded
3. **Analyze Dataset** (Optional) → View quality metrics and visualizations
4. **Configure Training** → Select task type, encoding, and options
5. **Monitor Training** → Real-time progress and status updates
6. **View Results** → Metrics, visualizations, and model performance
7. **Download Artifacts** → Model file and PDF report

## Task Types Supported

- `general_classification` - General purpose classification
- `protein_classification` - Protein sequence classification
- `dna_classification` - DNA sequence classification
- `rna_classification` - RNA sequence classification
- `gene_expression` - Gene expression analysis
- `regression` - Regression tasks

## Encoding Methods

- `kmer` - K-mer frequency encoding (k=2-6)
- `onehot` - One-hot encoding of sequences
- `integer` - Integer encoding (A=0, C=1, G=2, T=3)

## Supported ML Models

1. Random Forest
2. XGBoost
3. Gradient Boosting
4. Logistic Regression
5. Ridge Regression
6. SVM (Linear and RBF)
7. KNN
8. Naive Bayes

## PDF Report Contents

The generated report includes:
1. Title page with BioMLStudio branding
2. Table of contents
3. Dataset summary
4. Preprocessing steps documentation
5. Model selection results
6. Performance metrics tables
7. Embedded visualizations
8. Training logs summary

## Database Schema Updates

The `Job` model tracks workflow execution:
- `job_type`: 'ml_workflow'
- `status`: PENDING, RUNNING, COMPLETED, FAILED
- `progress`: 0-100
- `config`: Workflow configuration
- `result`: Training results and artifacts

## Error Handling

- Validation errors return 400 with details
- Dataset not found returns 404
- Job not found returns 404
- Training errors update job status to FAILED
- All errors logged with stack traces

## Performance Considerations

- Background task execution prevents blocking
- Progress updates every 3 seconds on frontend
- Efficient data loading with pandas
- Model artifacts saved to disk, not database
- Base64 encoding for visualization embedding

## Security

- All endpoints require authentication
- Users can only access their own jobs
- File paths validated to prevent traversal
- Token required for download endpoints

## Testing Checklist

- [ ] Upload FASTA dataset
- [ ] Upload CSV dataset
- [ ] Configure workflow with different task types
- [ ] Monitor training progress
- [ ] View completed results
- [ ] Download model file
- [ ] Download PDF report
- [ ] Test error handling (invalid config)
- [ ] Test with small and large datasets
- [ ] Test with different encoding methods

## Next Steps (Future Enhancements)

1. **Email OTP Authentication**
   - Add email service integration
   - Implement OTP generation and validation
   - Update auth endpoints

2. **Real-time WebSocket Updates**
   - Replace polling with WebSocket connections
   - Push progress updates to clients
   - Reduce server load

3. **Model Comparison Dashboard**
   - Compare multiple trained models
   - A/B testing functionality
   - Model versioning

4. **Custom Model Upload**
   - Allow users to upload pre-trained models
   - Model validation and testing
   - Transfer learning support

5. **Deployment Integration**
   - Deploy models as REST APIs
   - Docker container generation
   - Cloud deployment automation

## Configuration Variables

Environment variables used:
- `MODELS_DIR`: Directory for storing trained models
- `UPLOADS_DIR`: Directory for uploaded datasets
- `DATABASE_URL`: Database connection string
- `API_VERSION`: API version (v1)
- `DEBUG`: Enable debug mode

## Monitoring and Logging

All workflow steps are logged:
- Preprocessing completion
- Model selection
- Training progress
- Evaluation metrics
- Export success/failure

Logs include:
- Timestamp
- Job ID
- User ID
- Operation details
- Error messages (if any)

## Conclusion

The BioMLStudio workflow integration is now complete, providing a seamless end-to-end experience for bioinformatics researchers to:
1. Upload and analyze biological datasets
2. Automatically preprocess and encode sequences
3. Train multiple ML models with AutoML
4. Evaluate and compare model performance
5. Export trained models with comprehensive reports

All major components are implemented and integrated through the unified workflow API.
