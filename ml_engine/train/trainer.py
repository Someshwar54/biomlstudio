# trainer wrapper with checkpoint + seed + early stopping (PL if available)
import os, time, json
import numpy as np
import torch
_HAS_PL = True
try:
    import pytorch_lightning as pl
    from pytorch_lightning.callbacks import ModelCheckpoint, EarlyStopping
except Exception:
    _HAS_PL = False

def set_seed(seed=42):
    import random
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)

def run_training(train_loader, val_loader, config, job_id='local'):
    set_seed(config.get('seed',42))
    out_dir = os.path.join('data','models','checkpoints')
    os.makedirs(out_dir, exist_ok=True)
    ckpt_path = os.path.join(out_dir, f"{job_id}.ckpt")
    if _HAS_PL:
        # tiny PL model wrapper
        class LitModel(pl.LightningModule):
            def __init__(self, input_dim):
                super().__init__()
                self.net = torch.nn.Sequential(torch.nn.Linear(input_dim,16), torch.nn.ReLU(), torch.nn.Linear(16,2))
                self.loss = torch.nn.CrossEntropyLoss()
            def training_step(self, batch, batch_idx):
                x,y = batch; yhat = self.net(x); return self.loss(yhat,y)
            def validation_step(self, batch, batch_idx):
                x,y = batch; yhat = self.net(x); loss = self.loss(yhat,y); self.log('val_loss', loss)
            def configure_optimizers(self): return torch.optim.SGD(self.net.parameters(), lr=0.01)
        model = LitModel(config.get('input_dim',4))
        ckpt_cb = ModelCheckpoint(dirpath=out_dir, filename=job_id, save_top_k=1, monitor='val_loss', mode='min')
        es = EarlyStopping(monitor='val_loss', patience=3, mode='min')
        trainer = pl.Trainer(max_epochs=config.get('epochs',1), callbacks=[ckpt_cb, es], logger=False, enable_checkpointing=True)
        trainer.fit(model, train_loader, val_loader)
        return ckpt_cb.best_model_path or ckpt_path
    else:
        # plain torch quick loop and save state_dict
        net = torch.nn.Sequential(torch.nn.Linear(config.get('input_dim',4),16), torch.nn.ReLU(), torch.nn.Linear(16,2))
        opt = torch.optim.SGD(net.parameters(), lr=0.01)
        loss_fn = torch.nn.CrossEntropyLoss()
        for epoch in range(config.get('epochs',1)):
            net.train()
            for x,y in train_loader:
                opt.zero_grad(); yhat = net(x); loss = loss_fn(yhat,y); loss.backward(); opt.step()
        torch.save(net.state_dict(), ckpt_path)
        return ckpt_path