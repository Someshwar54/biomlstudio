# creates small csv, runs preprocess, balance, dataloaders and trainer
import numpy as np, os, torch
import pandas as pd
from ml_engine.src.data_handler import preprocess_tabular, balance_dataset
from ml_engine.train.trainer import run_training

def test_data_trainer_flow(tmp_path):
    # tiny csv
    p = tmp_path / "small.csv"
    df = pd.DataFrame({'f1':[1,2,3,4,5,6],'f2':[1,1,1,1,1,1],'target':[0,0,0,1,1,1]})
    df.to_csv(p, index=False)
    X,y = preprocess_tabular(pd.read_csv(p), target_col='target')
    Xb,yb = balance_dataset(X,y)
    # to torch tensors and dataloader
    Xt = torch.tensor(Xb, dtype=torch.float32)
    yt = torch.tensor(yb, dtype=torch.long)
    ds = torch.utils.data.TensorDataset(Xt, yt)
    loader = torch.utils.data.DataLoader(ds, batch_size=2)
    ckpt = run_training(loader, loader, config={'epochs':1,'input_dim':Xt.shape[1]}, job_id='testflow')
    assert os.path.exists(ckpt)