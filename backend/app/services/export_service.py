"""
Export service for models, results, and PDF reports
"""

import io
import base64
import logging
import json
import joblib
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.pdfgen import canvas

logger = logging.getLogger(__name__)


class ExportService:
    """
    Service for exporting trained models, preprocessing pipelines, and generating PDF reports.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def export_model_package(
        self,
        model_path: str,
        output_dir: str,
        include_preprocessors: bool = True,
        include_metadata: bool = True
    ) -> Dict[str, str]:
        """
        Export complete model package with all necessary artifacts.
        
        Args:
            model_path: Path to trained model
            output_dir: Output directory for package
            include_preprocessors: Include preprocessing pipeline
            include_metadata: Include model metadata
            
        Returns:
            Dict: Paths to exported files
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        exported_files = {}
        
        try:
            # Copy model file
            model_path = Path(model_path)
            if model_path.exists():
                export_model_path = output_dir / model_path.name
                import shutil
                shutil.copy(model_path, export_model_path)
                exported_files['model'] = str(export_model_path)
                self.logger.info(f"Exported model to {export_model_path}")
            
            # Export metadata if available
            if include_metadata:
                metadata_path = model_path.parent / f"{model_path.stem}_metadata.json"
                if metadata_path.exists():
                    export_metadata_path = output_dir / metadata_path.name
                    import shutil
                    shutil.copy(metadata_path, export_metadata_path)
                    exported_files['metadata'] = str(export_metadata_path)
            
            # Create README
            readme_path = output_dir / "README.md"
            readme_content = self._generate_model_readme(model_path.stem)
            with open(readme_path, 'w') as f:
                f.write(readme_content)
            exported_files['readme'] = str(readme_path)
            
            self.logger.info(f"Model package exported to {output_dir}")
            
        except Exception as e:
            self.logger.error(f"Error exporting model package: {e}")
        
        return exported_files
    
    def _generate_model_readme(self, model_name: str) -> str:
        """Generate README for exported model"""
        readme = f"""# BioMLStudio - Exported Model

## Model: {model_name}

### Usage

```python
import joblib

# Load the model
model = joblib.load('{model_name}.joblib')

# Make predictions
predictions = model.predict(X_new)
```

### Requirements

```
scikit-learn>=1.3.0
numpy>=1.26.0
pandas>=2.1.0
joblib>=1.3.0
```

### Notes

- This model was trained using BioMLStudio
- For bioinformatics data, ensure proper preprocessing before prediction
- Refer to the metadata file for model parameters and performance metrics

### Support

For issues or questions, refer to BioMLStudio documentation.

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        return readme
    
    async def generate_pdf_report(
        self,
        results: Dict[str, Any],
        dataset_info: Dict[str, Any],
        output_path: str
    ) -> str:
        """
        Generate comprehensive PDF report with all training results.
        
        Args:
            results: Training results dictionary
            dataset_info: Dataset information
            output_path: Path for output PDF
            
        Returns:
            str: Path to generated PDF
        """
        self.logger.info(f"Generating PDF report: {output_path}")
        
        try:
            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Container for PDF elements
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1f2937'),
                spaceAfter=30,
                alignment=1  # Center
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#374151'),
                spaceAfter=12,
                spaceBefore=12
            )
            
            # Title page
            story.append(Paragraph("BioMLStudio", title_style))
            story.append(Paragraph("Machine Learning Analysis Report", styles['Heading2']))
            story.append(Spacer(1, 12))
            story.append(Paragraph(
                f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}",
                styles['Normal']
            ))
            story.append(PageBreak())
            
            # Table of Contents
            story.append(Paragraph("Table of Contents", heading_style))
            toc_data = [
                ["1.", "Dataset Summary"],
                ["2.", "Preprocessing Steps"],
                ["3.", "Model Selection & Training"],
                ["4.", "Performance Metrics"],
                ["5.", "Visualizations"],
                ["6.", "Predictions & Results"]
            ]
            toc_table = Table(toc_data, colWidths=[0.5*inch, 5*inch])
            toc_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#374151')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(toc_table)
            story.append(PageBreak())
            
            # 1. Dataset Summary
            story.append(Paragraph("1. Dataset Summary", heading_style))
            dataset_data = [
                ["Property", "Value"],
                ["Dataset Name", dataset_info.get('name', 'N/A')],
                ["Dataset Type", dataset_info.get('dataset_type', 'N/A')],
                ["Total Samples", str(dataset_info.get('total_samples', 'N/A'))],
                ["Features", str(dataset_info.get('n_features', 'N/A'))],
                ["File Size", f"{dataset_info.get('file_size_mb', 0):.2f} MB"]
            ]
            dataset_table = Table(dataset_data, colWidths=[2*inch, 4*inch])
            dataset_table.setStyle(self._get_table_style())
            story.append(dataset_table)
            story.append(Spacer(1, 20))
            
            # 2. Preprocessing Steps
            story.append(Paragraph("2. Preprocessing Steps", heading_style))
            if 'preprocessing_steps' in results:
                for i, step in enumerate(results['preprocessing_steps'], 1):
                    story.append(Paragraph(f"<b>Step {i}: {step.get('step', 'Unknown')}</b>", styles['Normal']))
                    for action in step.get('actions', []):
                        story.append(Paragraph(f"  • {action}", styles['Normal']))
                    story.append(Spacer(1, 8))
            story.append(PageBreak())
            
            # 3. Model Selection & Training
            story.append(Paragraph("3. Model Selection & Training", heading_style))
            
            if 'models_trained' in results:
                model_data = [["Model", "Training Time", "Score"]]
                for model_result in results['models_trained']:
                    model_data.append([
                        model_result.get('model_name', 'Unknown'),
                        f"{model_result.get('training_time', 0):.2f}s",
                        f"{model_result.get('metrics', {}).get('primary_score', 0):.4f}"
                    ])
                
                model_table = Table(model_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
                model_table.setStyle(self._get_table_style())
                story.append(model_table)
            
            if 'best_model' in results:
                story.append(Spacer(1, 12))
                story.append(Paragraph(
                    f"<b>Best Model:</b> {results['best_model'].get('model_name', 'Unknown')}",
                    styles['Normal']
                ))
            
            story.append(PageBreak())
            
            # 4. Performance Metrics
            story.append(Paragraph("4. Performance Metrics", heading_style))
            
            if 'metrics' in results:
                metrics = results['metrics']
                
                # Training metrics
                if 'training' in metrics:
                    story.append(Paragraph("<b>Training Metrics:</b>", styles['Normal']))
                    train_metrics = metrics['training']
                    metrics_data = [[k.replace('_', ' ').title(), f"{v:.4f}"] for k, v in train_metrics.items()]
                    if metrics_data:
                        metrics_table = Table([["Metric", "Value"]] + metrics_data, colWidths=[2.5*inch, 2*inch])
                        metrics_table.setStyle(self._get_table_style())
                        story.append(metrics_table)
                        story.append(Spacer(1, 12))
                
                # Validation metrics
                if 'validation' in metrics:
                    story.append(Paragraph("<b>Validation Metrics:</b>", styles['Normal']))
                    val_metrics = metrics['validation']
                    metrics_data = [[k.replace('_', ' ').title(), f"{v:.4f}"] for k, v in val_metrics.items()]
                    if metrics_data:
                        metrics_table = Table([["Metric", "Value"]] + metrics_data, colWidths=[2.5*inch, 2*inch])
                        metrics_table.setStyle(self._get_table_style())
                        story.append(metrics_table)
            
            story.append(PageBreak())
            
            # 5. Visualizations
            story.append(Paragraph("5. Visualizations", heading_style))
            
            if 'visualizations' in results:
                for plot_name, plot_base64 in results['visualizations'].items():
                    story.append(Paragraph(
                        plot_name.replace('_', ' ').title(),
                        styles['Heading3']
                    ))
                    
                    # Decode base64 image
                    try:
                        img_data = base64.b64decode(plot_base64)
                        img_buffer = io.BytesIO(img_data)
                        
                        # Add image to PDF
                        img = Image(img_buffer, width=5*inch, height=3.5*inch)
                        story.append(img)
                        story.append(Spacer(1, 12))
                    except Exception as e:
                        self.logger.warning(f"Could not add plot {plot_name}: {e}")
                        story.append(Paragraph(f"[Plot: {plot_name}]", styles['Italic']))
            
            story.append(PageBreak())
            
            # 6. Training Logs (summary)
            story.append(Paragraph("6. Training Summary", heading_style))
            
            if 'logs' in results and results['logs']:
                story.append(Paragraph(f"<b>Total training time:</b> {results.get('training_time', 0):.2f} seconds", styles['Normal']))
                story.append(Spacer(1, 8))
                
                # Show important log entries
                important_logs = [log for log in results['logs'] if log.get('level') in ['SUCCESS', 'ERROR']]
                if important_logs:
                    story.append(Paragraph("<b>Key Events:</b>", styles['Normal']))
                    for log in important_logs[:10]:  # Limit to 10
                        story.append(Paragraph(
                            f"[{log.get('level')}] {log.get('message')}",
                            styles['Normal']
                        ))
            
            # Footer
            story.append(PageBreak())
            story.append(Spacer(1, 100))
            story.append(Paragraph(
                "Report generated by BioMLStudio - AI-Based No-Code Platform for Bioinformatics",
                styles['Italic']
            ))
            story.append(Paragraph(
                f"© {datetime.now().year} BioMLStudio. All rights reserved.",
                styles['Italic']
            ))
            
            # Build PDF
            doc.build(story)
            
            self.logger.info(f"PDF report generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error generating PDF report: {e}")
            raise
    
    def _get_table_style(self) -> TableStyle:
        """Get standard table style for PDF"""
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#111827')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#374151')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb'))
        ])
    
    async def export_preprocessing_pipeline(
        self,
        encoders: Dict[str, Any],
        scalers: Dict[str, Any],
        output_path: str
    ) -> str:
        """
        Export preprocessing pipeline for reuse.
        
        Args:
            encoders: Label encoders dict
            scalers: Feature scalers dict
            output_path: Output file path
            
        Returns:
            str: Path to saved pipeline
        """
        try:
            pipeline_data = {
                'encoders': encoders,
                'scalers': scalers,
                'timestamp': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            joblib.dump(pipeline_data, output_path)
            self.logger.info(f"Preprocessing pipeline exported to {output_path}")
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error exporting preprocessing pipeline: {e}")
            raise


# Global instance
export_service = ExportService()
