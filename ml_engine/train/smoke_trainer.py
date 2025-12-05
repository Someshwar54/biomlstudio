# ml_engine/train/smoke_trainer.py
import torch

class SmokeTrainer:
    def __init__(self, input_dim=8, hidden_dim=16, output_dim=2, epochs=1, batch_size=4, lr=0.01, device=None):
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        self.epochs = epochs
        self.batch_size = batch_size
        self.lr = lr
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')

    def build_model(self):
        return torch.nn.Sequential(
            torch.nn.Linear(self.input_dim, self.hidden_dim),
            torch.nn.ReLU(),
            torch.nn.Linear(self.hidden_dim, self.output_dim)
        ).to(self.device)

    def train(self):
        model = self.build_model()
        optim = torch.optim.SGD(model.parameters(), lr=self.lr)
        loss_fn = torch.nn.CrossEntropyLoss()

        # Generate dummy data
        X = torch.randn(8, self.input_dim).to(self.device)
        y = torch.randint(0, self.output_dim, (8,)).to(self.device)

        model.train()
        final_loss = None
        for _ in range(self.epochs):
            for i in range(0, X.size(0), self.batch_size):
                xb = X[i:i+self.batch_size]
                yb = y[i:i+self.batch_size]
                preds = model(xb)
                loss = loss_fn(preds, yb)
                optim.zero_grad()
                loss.backward()
                optim.step()
                final_loss = loss.item()

        return model, final_loss