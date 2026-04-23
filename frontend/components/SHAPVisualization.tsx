"use client";

import React from 'react';
import { Card } from '@/components/ui/Card';
import { SHAPExplanation } from '@/types/api';
import { BarChart3 } from 'lucide-react';

interface SHAPVisualizationProps {
  shapData: SHAPExplanation;
  className?: string;
}

export default function SHAPVisualization({ shapData, className = '' }: SHAPVisualizationProps) {
  if (!shapData?.success || !shapData.plots) {
    return null;
  }

  const { plots, summary, explainer_type } = shapData;

  return (
    <div className={`gap-section flex flex-col ${className}`}>
      {/* Header */}
      <Card className="card-spacing">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-6">
          <div>
            <h2 className="text-3xl font-bold mb-2">
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">
                SHAP Explanations
              </span>
            </h2>
            <p className="text-base text-zinc-400 leading-relaxed">
              SHapley Additive exPlanations (SHAP) provide insights into which features
              contribute most to individual predictions and overall model behavior.
            </p>
          </div>
          {explainer_type && (
            <div className="flex items-center gap-2">
              <span className="px-4 py-2 text-sm font-semibold bg-gradient-to-r from-blue-500/10 to-purple-500/10 text-blue-400 rounded-xl border border-blue-500/30 backdrop-blur-sm">
                {explainer_type}
              </span>
            </div>
          )}
        </div>
      </Card>

      {/* Summary Statistics */}
      {summary && (
        <Card className="card-spacing">
          <h3 className="text-2xl font-bold mb-6 text-white flex items-center gap-2">
            <BarChart3 className="w-6 h-6" />
            Top Contributing Features
          </h3>
          <div className="space-y-4">
            {summary.top_features.slice(0, 10).map((feature, idx) => (
              <div key={idx} className="space-y-2">
                <div className="flex justify-between items-center text-sm">
                  <span className="font-medium text-zinc-300">{feature.feature}</span>
                  <div className="flex gap-4 text-zinc-400">
                    <span className="font-mono">
                      Impact: {feature.importance.toFixed(4)}
                    </span>
                    <span className="font-mono">
                      Mean: {feature.mean_shap > 0 ? '+' : ''}{feature.mean_shap.toFixed(4)}
                    </span>
                  </div>
                </div>
                <div className="relative w-full bg-zinc-800 rounded-full h-2">
                  <div
                    className="absolute h-2 rounded-full bg-gradient-to-r from-blue-500 to-purple-500"
                    style={{
                      width: `${(feature.importance / summary.top_features[0].importance) * 100}%`,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
          <p className="mt-4 text-xs text-zinc-500">
            Showing top 10 of {summary.total_features} features
          </p>
        </Card>
      )}

      {/* SHAP Summary Plot */}
      {plots.summary_plot && (
        <Card className="p-6 card-spacing">
          <h3 className="text-xl font-bold mb-4 text-zinc-200">Feature Impact Distribution</h3>
          <p className="text-sm text-zinc-400 mb-4">
            Each dot represents a sample. Red indicates high feature values, blue indicates low.
            Position on x-axis shows the impact on model output.
          </p>
          <div className="bg-white rounded-lg p-4 flex items-center justify-center">
            <img
              src={plots.summary_plot}
              alt="SHAP Summary Plot"
              className="max-w-full h-auto"
            />
          </div>
        </Card>
      )}

      {/* SHAP Bar Plot */}
      {plots.bar_plot && (
        <Card className="p-6 card-spacing">
          <h3 className="text-xl font-bold mb-4 text-zinc-200">Mean Feature Importance</h3>
          <p className="text-sm text-zinc-400 mb-4">
            Average magnitude of SHAP values across all predictions. Higher values indicate
            greater importance to the model.
          </p>
          <div className="bg-white rounded-lg p-4 flex items-center justify-center">
            <img
              src={plots.bar_plot}
              alt="SHAP Bar Plot"
              className="max-w-full h-auto"
            />
          </div>
        </Card>
      )}

      {/* Waterfall Plot */}
      {plots.waterfall_plot && (
        <Card className="p-6 card-spacing">
          <h3 className="text-xl font-bold mb-4 text-zinc-200">Individual Prediction Breakdown</h3>
          <p className="text-sm text-zinc-400 mb-4">
            Shows how each feature pushes the prediction from the base value (expected model output)
            to the final prediction for a single sample.
          </p>
          <div className="bg-white rounded-lg p-4 flex items-center justify-center">
            <img
              src={plots.waterfall_plot}
              alt="SHAP Waterfall Plot"
              className="max-w-full h-auto"
            />
          </div>
        </Card>
      )}

      {/* Force Plot */}
      {plots.force_plot && (
        <Card className="p-6 card-spacing">
          <h3 className="text-xl font-bold mb-4 text-zinc-200">Force Plot</h3>
          <p className="text-sm text-zinc-400 mb-4">
            Visualizes feature contributions pushing the prediction higher (red) or lower (blue)
            from the base value.
          </p>
          <div className="bg-white rounded-lg p-4 overflow-x-auto">
            <img
              src={plots.force_plot}
              alt="SHAP Force Plot"
              className="w-full h-auto min-w-[800px]"
            />
          </div>
        </Card>
      )}

      {/* Interpretation Guide */}
      <Card className="p-6 bg-gradient-to-br from-blue-500/5 to-purple-500/5 border-blue-500/20 card-spacing">
        <h3 className="text-lg font-bold mb-3 text-zinc-200">How to Interpret SHAP Values</h3>
        <ul className="space-y-2 text-sm text-zinc-300">
          <li className="flex gap-2">
            <span className="text-blue-400">•</span>
            <span><strong>Positive SHAP values</strong> increase the model&apos;s prediction</span>
          </li>
          <li className="flex gap-2">
            <span className="text-purple-400">•</span>
            <span><strong>Negative SHAP values</strong> decrease the model&apos;s prediction</span>
          </li>
          <li className="flex gap-2">
            <span className="text-green-400">•</span>
            <span><strong>Magnitude</strong> indicates the strength of the feature&apos;s impact</span>
          </li>
          <li className="flex gap-2">
            <span className="text-yellow-400">•</span>
            <span><strong>Base value</strong> is the average model output over the training data</span>
          </li>
        </ul>
      </Card>
    </div>
  );
}
