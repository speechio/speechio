#!/usr/bin/env python3
# coding = utf8
#
# Copyright (c) 2021 Jiayu DU
# All rights reserved.

import yaml
import torch.nn as nn

from wenet.transformer.encoder import TransformerEncoder, ConformerEncoder
from wenet.transformer.decoder import TransformerDecoder, BiTransformerDecoder
from wenet.transformer.ctc import CTC
from wenet.transformer.asr_model import ASRModel

def stt_create(config_filename, idim, odim, blk_index:int, bos_index:int, eos_index:int, sil_index:int, unk_index:int):
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

        model = ASRModel(
            vocab_size=odim,
            encoder=encoder,
            decoder=decoder,
            ctc=CTC(odim, encoder.output_size()),
            **config['model_conf'],
        )

        model.sos = bos_index
        model.eos = eos_index

        return model
    
def stt_loss(model, X, T, L, U):
    loss = model(X, T, L, U)
    return loss[0] * X.shape[0] # batch loss

def stt_decode(model, X, T, mode = 'attention_rescoring'):
    if mode == 'attention':
        hyps, _ = model.recognize(X, T)
        hyps = [hyp.tolist() for hyp in hyps]
    elif mode == 'ctc_greedy_search':
        hyps, _ = model.ctc_greedy_search(X, T)
    elif mode == 'ctc_prefix_beam_search':
        hyp, _ = model.ctc_prefix_beam_search(X, T, beam_size = 10)
        hyps = [list(hyp)]
    elif mode == 'attention_rescoring':
        hyp, _ = model.attention_rescoring(X, T, beam_size = 10)
        hyps = [list(hyp)]
    return hyps
