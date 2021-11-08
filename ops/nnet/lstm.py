#!/usr/bin/env python3
# coding = utf8
#
# Copyright (c) 2021 Jiayu DU
# All rights reserved.

import torch
import torch.nn as nn

G_MODEL_DEVICE = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

class Model(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.input_size = config.idim
        self.hidden_size = config.hidden_layer_dim
        self.num_layers = config.num_hidden_layers
        self.num_classes = config.odim

        self.lstm = nn.LSTM(self.input_size, self.hidden_size, self.num_layers, batch_first=True, bidirectional=True)
        self.fc = nn.Linear(self.hidden_size*2, self.num_classes)  # 2 for bidirection
        self.log_softmax = nn.LogSoftmax(dim = 2)
    
    def forward(self, x):
        # Set initial states
        h0 = torch.zeros(self.num_layers*2, x.size(0), self.hidden_size).to(G_MODEL_DEVICE) # 2 for bidirection 
        c0 = torch.zeros(self.num_layers*2, x.size(0), self.hidden_size).to(G_MODEL_DEVICE)
        
        # Forward propagate LSTM
        out, _ = self.lstm(x, (h0, c0))  # out: tensor of shape (batch_size, seq_length, hidden_size*2)
        # Decode the hidden state of the last time step
        out = self.fc(out)
        out = self.log_softmax(out)
        return out


class Loss(nn.Module):
    def __init__(self, blank_index):
        super().__init__()
        self.blank_index = blank_index

    def forward(self, log_probs, labels, input_lens, label_lens):
        log_probs = torch.einsum("btv->tbv", log_probs)
        loss = torch.nn.functional.ctc_loss(
            log_probs,
            labels,
            input_lens,
            label_lens,
            self.blank_index,
            zero_infinity=True,
            reduction='sum',
        )
        return loss

#def LossFunc(log_probs, labels, input_lens, label_lens, blank_index = 0):
#    log_probs = torch.einsum("btv->tbv", log_probs)
#    loss = torch.nn.functional.ctc_loss(
#        log_probs,
#        labels,
#        input_lens,
#        label_lens,
#        blank_index,
#        zero_infinity=True,
#        reduction='sum',
#    )
#    return loss
#