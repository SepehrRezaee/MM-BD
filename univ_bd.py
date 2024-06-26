from __future__ import absolute_import
from __future__ import print_function

import sys

sys.path.append('/kaggle/working/MM-BD')

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import torch.backends.cudnn as cudnn

import torchvision
import torchvision.transforms as transforms
from torchvision import models
from torchvision.transforms import Resize
from torchvision.models import vit_b_16, ViT_B_16_Weights

import os
import sys
import math
import argparse
import matplotlib.pyplot as plt
from PIL import Image
import PIL
import random
import copy as cp
import numpy as np

# from src.resnet import ResNet18

# from transformers import ViTForImageClassification

parser = argparse.ArgumentParser(description='UnivBD method')
parser.add_argument('--model_dir', default='model1', help='model path')
#parser.add_argument('--data_path', '-d', required=True, help='data path')
args = parser.parse_args()

device = 'cuda' if torch.cuda.is_available() else 'cpu'

random.seed()

# Detection parameters
NC = 10
NI = 150
PI = 0.9
NSTEP = 300
TC = 6
batch_size = 20

# Load model
# model = ResNet18()
# model = model.to(device)
# criterion = nn.CrossEntropyLoss()

#if device == 'cuda':
#    model = torch.nn.DataParallel(model)
#    cudnn.benchmark = True

# model.load_state_dict(torch.load('./' + args.model_dir + '/model.pth'))
# model.eval()

num_classes = 10  

# Initialize the model with pretrained weights
model = vit_b_16(weights=ViT_B_16_Weights.IMAGENET1K_V1)

# Print the model to verify structure (optional, for debugging)
# print(model)

# Check if the heads and head exist and replace the classifier (head)
if hasattr(model, 'heads') and hasattr(model.heads, 'head'):
    in_features = model.heads.head.in_features
    model.heads.head = nn.Linear(in_features, num_classes)
else:
    raise AttributeError("The model does not have the expected 'heads.head' structure")

# Add image resizing as the first step in the model
net = nn.Sequential(
    Resize((224, 224)),  # Resize images to the expected input size
    model
)

base_dir = '/kaggle/working/MM-BD/model13/model.pt'
# checkpoint_path = os.path.join(base_dir, args.model_dir, 'model.pth')
print("Loading checkpoint from:", checkpoint_path)
checkpoint = torch.load(base_dir, map_location=device)

# Load the state dict into the model
net.load_state_dict(checkpoint['model'])

# Set the model to evaluation mode
net.eval()


# Define the device to use (CUDA if available)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def lr_scheduler(iter_idx):
    lr = 1e-2


    return lr

res = []
for t in range(10):

    # images = torch.rand([30, 3, 32, 32]).to(device)
    images = torch.rand([30, 3, 224, 224]).to(device)
    images.requires_grad = True

    last_loss = 1000
    labels = t * torch.ones((len(images),), dtype=torch.long).to(device)
    onehot_label = F.one_hot(labels, num_classes=NC)
    for iter_idx in range(NSTEP):

        optimizer = torch.optim.SGD([images], lr=lr_scheduler(iter_idx), momentum=0.2)
        optimizer.zero_grad()
        outputs = model(torch.clamp(images, min=0, max=1))

        loss = -1 * torch.sum((outputs * onehot_label)) \
               + torch.sum(torch.max((1-onehot_label) * outputs - 1000 * onehot_label, dim=1)[0])
        loss.backward(retain_graph=True)
        optimizer.step()
        if abs(last_loss - loss.item())/abs(last_loss)< 1e-5:
            break
        last_loss = loss.item()

    res.append(torch.max(torch.sum((outputs * onehot_label), dim=1)\
               - torch.max((1-onehot_label) * outputs - 1000 * onehot_label, dim=1)[0]).item())
    print(t, res[-1])

stats = res
from scipy.stats import median_abs_deviation as MAD
from scipy.stats import gamma
mad = MAD(stats, scale='normal')
abs_deviation = np.abs(stats - np.median(stats))
score = abs_deviation / mad
print(f"score is {score}")

np.save('results.npy', np.array(res))
ind_max = np.argmax(stats)
r_eval = np.amax(stats)
r_null = np.delete(stats, ind_max)

shape, loc, scale = gamma.fit(r_null)
pv = 1 - pow(gamma.cdf(r_eval, a=shape, loc=loc, scale=scale), len(r_null)+1)
print(f'pv is {pv}')
print(args.model_dir)
if pv > 0.05:
    print('No Attack!')
else:
    print('There is attack with target class {}'.format(np.argmax(stats)))
