"""
Test script to verify SHAP integration
"""
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import make_classification
import joblib
from pathlib import Path
import shap

print("=" * 60)
print("Testing SHAP Integration")
print("=" * 60)

# 1. Create a simple dataset
print("\n1. Creating test dataset...")
X, y = make_classification(n_samples=100, n_features=10, n_informative=5, random_state=42)
feature_names = [f'feature_{i}' for i in range(10)]
print(f"   ✓ Created dataset with {X.shape[0]} samples and {X.shape[1]} features")

# 2. Train a simple model
print("\n2. Training RandomForest model...")
model = RandomForestClassifier(n_estimators=10, random_state=42)
model.fit(X, y)
print(f"   ✓ Model trained with accuracy: {model.score(X, y):.2f}")

# 3. Test SHAP TreeExplainer
print("\n3. Testing SHAP TreeExplainer...")
try:
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X[:10])
    print(f"   ✓ SHAP TreeExplainer working!")
    print(f"   ✓ SHAP values shape: {np.array(shap_values[0]).shape if isinstance(shap_values, list) else shap_values.shape}")
    print(f"   ✓ Expected value: {explainer.expected_value if not isinstance(explainer.expected_value, np.ndarray) else explainer.expected_value[0]:.4f}")
except Exception as e:
    print(f"   ✗ TreeExplainer failed: {e}")

# 4. Test feature importance extraction
print("\n4. Testing feature importance...")
mean_abs_shap = np.abs(shap_values[0] if isinstance(shap_values, list) else shap_values).mean(axis=0)
sorted_idx = np.argsort(mean_abs_shap)[::-1]
print(f"   ✓ Top 3 features by SHAP importance:")
for i in sorted_idx[:3]:
    print(f"      - {feature_names[i]}: {mean_abs_shap[i]:.4f}")

print("\n" + "=" * 60)
print("✓ SHAP is working correctly!")
print("=" * 60)
print("\nTo use SHAP in the application:")
print("1. Train a model through the API")
print("2. SHAP explanations will be automatically generated")
print("3. View SHAP visualizations on the results page")
print("4. Or call /api/shap/explain/model/{model_id} explicitly")
