# ml_engine/train/smoke_trainer.py
import os
import time
import json

def tiny_train(output_dir, epochs=1, input_dim=8):
    """
    Minimal CPU-only smoke training function.
    Creates a tiny PyTorch model, runs a few training steps, and saves weights.
    Falls back to dummy weights if PyTorch is unavailable.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        import torch
        import torch.nn as nn
        import torch.optim as optim
        
        # Create a simple 2-layer neural network
        model = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 2)
        )
        
        optimizer = optim.SGD(model.parameters(), lr=0.01)
        loss_fn = nn.CrossEntropyLoss()
        
        # Generate random training data
        X = torch.randn(16, input_dim)
        y = torch.randint(0, 2, (16,))
        
        # Training loop
        model.train()
        for epoch in range(epochs):
            preds = model(X)
            loss = loss_fn(preds, y)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        
        # Save weights as PyTorch state_dict
        weights_path = os.path.join(output_dir, "weights.pt")
        torch.save(model.state_dict(), weights_path)
        
        # Save metadata
        meta = {
            "loss": float(loss.item()),
            "trained_at": time.time(),
            "epochs": epochs,
            "input_dim": input_dim,
            "torch_available": True
        }
        
    except ImportError:
        # Fallback: create dummy weights file if torch is unavailable
        print("Warning: PyTorch not available, creating dummy weights file")
        weights_path = os.path.join(output_dir, "weights.pt")
        
        # Write a deterministic dummy file
        dummy_weights = b"DUMMY_WEIGHTS_" + str(time.time()).encode() + b"_" + str(input_dim).encode()
        with open(weights_path, "wb") as f:
            f.write(dummy_weights)
        
        meta = {
            "loss": 0.5,
            "trained_at": time.time(),
            "epochs": epochs,
            "input_dim": input_dim,
            "torch_available": False,
            "note": "Dummy weights - PyTorch unavailable"
        }
    
    # Write metadata JSON
    meta_path = os.path.join(output_dir, "meta.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    
    return weights_path, meta
