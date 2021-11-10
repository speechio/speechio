#!/usr/bin/env python3
# coding = utf8
#
# Copyright (c) 2021 Jiayu DU
# All rights reserved.

import torch
import torch.nn as nn

import sys
sys.path.insert(0, "ops/nnet/deps")
from wenet.transformer.encoder import TransformerEncoder, ConformerEncoder
from wenet.transformer.decoder import TransformerDecoder, BiTransformerDecoder
from wenet.transformer.ctc import CTC
from wenet.transformer.asr_model import ASRModel

class Model(nn.Module):
    def __init__(self, configs, vocab_size):
        super().__init__()

        configs['input_dim'] = configs['dataset_conf']['fbank_conf']['num_mel_bins']
        configs['output_dim'] = vocab_size

        input_dim = configs['input_dim']
        vocab_size = configs['output_dim']

        encoder_type = configs.get('encoder', 'conformer')
        decoder_type = configs.get('decoder', 'bitransformer')

        if encoder_type == 'conformer':
            encoder = ConformerEncoder(input_dim, **configs['encoder_conf'])
        else:
            encoder = TransformerEncoder(input_dim, **configs['encoder_conf'])

        if decoder_type == 'transformer':
            decoder = TransformerDecoder(vocab_size, encoder.output_size(), **configs['decoder_conf'])
        else:
            assert 0.0 < configs['model_conf']['reverse_weight'] < 1.0
            assert configs['decoder_conf']['r_num_blocks'] > 0
            decoder = BiTransformerDecoder(vocab_size, encoder.output_size(), **configs['decoder_conf'])

        ctc = CTC(vocab_size, encoder.output_size())

        self.model = ASRModel(
            vocab_size=vocab_size,
            encoder=encoder,
            decoder=decoder,
            ctc=ctc,
            **configs['model_conf'],
        )
    
    def forward(self, X, T, L, U):
        loss = self.model(X, T, L, U)
        return loss[0] * X.shape[0] # batch loss

    def decode(self, X, T):
        return self.model.ctc_greedy_search(X, T)
