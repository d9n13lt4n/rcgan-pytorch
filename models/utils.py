import os
from typing import Dict

import numpy as np
import torch
from torch.utils.tensorboard import SummaryWriter
from tqdm import trange

from models.dataset import RCGANDataset

def sample_Z(batch_size=32, seq_length=100, latent_dim=20, use_time=False):
    """
    return noise vector sampled from normal distribution with shape 
    (32, 100, 20)
    """
    sample = np.float32(np.random.normal(size=[batch_size, seq_length, latent_dim]))
    if use_time:
        print('WARNING: use_time has different semantics')
        sample[:, :, 0] = np.linspace(0, 1.0/seq_length, num=seq_length)

    return sample

def sample_C(batch_size=32, cond_dim=2, max_val=1, one_hot=False):
    """
    return an array of integers (so far we only allow integer-valued
    conditional values)
    """
    if cond_dim == 0:
        return None
    else:
        if one_hot:
            assert max_val == 1
            C = np.zeros(shape=(batch_size, cond_dim))
            labels = np.random.choice(cond_dim, batch_size)
            C[np.arange(batch_size), labels] = 1
        else:
            C = np.random.choice(max_val+1, size=(batch_size, cond_dim))
        return C

def rcgan_trainer(model, data, time, args):
    # Initialize TimeGAN dataset and dataloader
    dataset = RCGANDataset(data, time)
    dataloader = torch.utils.data.DataLoader(
        dataset=dataset,
        batch_size=args.batch_size,
        shuffle=False    
    )

    model.to(args.device)

    # Initialize Optimizers
    g_opt = torch.optim.Adam(model.generator.parameters(), lr=args.learning_rate)
    d_opt = torch.optim.Adam(model.discriminator.parameters(), lr=args.learning_rate)
    
    # TensorBoard writer
    writer = SummaryWriter(os.path.join(f"tensorboard/{args.exp}"))

    logger = trange(
        args.epochs, 
        desc=f"Epoch: 0, E_loss: 0, G_loss: 0, D_loss: 0"
    )
    
    for epoch in logger:
        for X_mb, T_mb in dataloader:
            Z_mb = torch.rand((args.batch_size, args.max_seq_len, args.Z_dim))
            # Discriminator forward pass
            for _ in range(args.d_iters):
                model.zero_grad()
                d_loss, _ = model(
                    X=X_mb,
                    Z=Z_mb,
                    T=T_mb,
                    CG=None,
                    CD=None,
                    CS=None
                )
                d_loss.backward()
                d_opt.step()
            # Generator forward pass
            for _ in range(args.g_iters):
                model.zero_grad()
                _, g_loss = model(
                    X=X_mb,
                    Z=Z_mb,
                    T=T_mb,
                    CG=None,
                    CD=None,
                    CS=None
                )
                g_loss.backward()
                g_opt.step()

def rcgan_generator(model, time, args):
    Z = torch.rand((len(time), args.max_seq_len, args.Z_dim))

    with torch.no_grad():
        X_hat = model.generate(Z=Z, T=time, C=None)

    return X_hat
