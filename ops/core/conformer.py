#!/usr/bin/env python3
# coding = utf8
#
# Copyright (c) 2021 Jiayu DU
# All rights reserved.

import torch
import torch.nn as nn

import yaml

import sys
sys.path.insert(0, "toolkit")
from wenet.transformer.encoder import TransformerEncoder, ConformerEncoder
from wenet.transformer.decoder import TransformerDecoder, BiTransformerDecoder
from wenet.transformer.ctc import CTC
from wenet.transformer.asr_model import ASRModel

class Model(nn.Module):
    def __init__(self, config_filename, idim, odim, blk_index:int, bos_index:int, eos_index:int, sil_index:int, unk_index:int):
        super().__init__()

        with open(config_filename, 'r') as f: 
            config = yaml.load(f, Loader=yaml.FullLoader)

        if config.get('encoder', 'conformer') == 'conformer':
            encoder = ConformerEncoder(idim, **config['encoder_conf'])
        else:
            encoder = TransformerEncoder(idim, **config['encoder_conf'])

        if config.get('decoder', 'bitransformer') == 'transformer':
            decoder = TransformerDecoder(odim, encoder.output_size(), **config['decoder_conf'])
        else:
            assert 0.0 < config['model_conf']['reverse_weight'] < 1.0
            assert config['decoder_conf']['r_num_blocks'] > 0
            decoder = BiTransformerDecoder(odim, encoder.output_size(), **config['decoder_conf'])

        ctc = CTC(odim, encoder.output_size())

        self.model = ASRModel(
            vocab_size=odim,
            encoder=encoder,
            decoder=decoder,
            ctc=ctc,
            **config['model_conf'],
        )

        self.model.sos = bos_index
        self.model.eos = eos_index
    
    def forward(self, X, T, L, U):
        loss = self.model(X, T, L, U)
        return loss[0] * X.shape[0] # batch loss

    def decode(self, X, T, mode = 'attention_rescoring'):
        if mode == 'attention':
            hyps, _ = self.model.recognize(X, T)
            hyps = [hyp.tolist() for hyp in hyps]
        elif mode == 'ctc_greedy_search':
            hyps, _ = self.model.ctc_greedy_search(X, T)
        elif mode == 'ctc_prefix_beam_search':
            hyp, _ = self.model.ctc_prefix_beam_search(X, T, beam_size = 10)
            hyps = [list(hyp)]
        elif mode == 'attention_rescoring':
            hyp, _ = self.model.attention_rescoring(X, T, beam_size = 10)
            hyps = [list(hyp)]
        return hyps
