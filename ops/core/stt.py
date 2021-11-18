#!/usr/bin/env python3
# coding = utf8
#
# Copyright (c) 2021 Jiayu DU
# All rights reserved.

import os, sys
import argparse
from typing import Optional
from dataclasses import dataclass
import logging.config

import decimal
import random

#import numpy
import torch
import torch.nn as nn
import torchaudio
import torchaudio.sox_effects

import csv   # metadata
import json  # mvn stats
from omegaconf import OmegaConf  # various configs

import sentencepiece as spm
#import k2

# Global Constants
G_FEATURE_PADDING_VALUE = float(0.0)
G_PAD_ID = -1

G_DEFAULT_DATA_ZOO = 'config/data_zoo.yaml'
G_DEFAULT_LOGGING_CONFIG = 'config/logging.yaml'
# setup logging
if os.path.isfile(G_DEFAULT_LOGGING_CONFIG):
    import yaml
    with open(G_DEFAULT_LOGGING_CONFIG, 'r', encoding='utf8') as f:
        logging.config.dictConfig(yaml.safe_load(f))
else:
    logging.basicConfig(
        stream=sys.stderr, level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s'
    )


@dataclass
class Sample:
    id:str = ''
    audio:str = ''
    begin:float = 0.0
    duration:float = 0.0
    text:str = ''
    speaker:str = ''


class SampleLoader:
    ''' A callable wrapper class to load one utterance dict (a tsv/jsonl/yaml item)
    input:
        utt_dict = {
            'ID': 'utt_key_1',
            'AUDIO': 'audio/one_utterance.wav',
            'DURATION': '1.28',
            'TEXT': 'Hello World'
        }

    return:
        a Sample object or None
        None if an utterance doesn't satisfy constraints e.g. duration, text length
    '''
    def __init__(self, min_duration:float = 0.0, max_duration:float = 60.0, min_text_length:int = 1, max_text_length:int = 2048, field_map:dict = None, data_dir:str = ''):
        if field_map:
            self.field_map = field_map
        else:
            self.field_map = {
                'id': 'ID',
                'audio': 'AUDIO',
                'begin': 'BEGIN',
                'duration': 'DURATION',
                'text': 'TEXT',
                'speaker': 'SPEAKER',
            }

        self.min_duration = min_duration
        self.max_duration = max_duration
        self.min_text_length = min_text_length
        self.max_text_length = max_text_length

        self.data_dir = data_dir

    def __call__(self, utt:dict) -> Optional[Sample] :
        sample = Sample()
        for attr, field in self.field_map.items():
            if v := utt.get(field):
                if attr in ['duration', 'begin', ]:
                    v = float(v)
                elif attr == 'audio':
                    v = os.path.join(self.data_dir, v)
                else:
                    v = str(v)
                assert hasattr(sample, attr), f'{field} -> Sample.{attr} mapping failed, no such attribute'
                setattr(sample, attr, v)

        if sample.duration < self.min_duration:
            return None
        if sample.duration > self.max_duration:
            return None
        if len(sample.text) < self.min_text_length:
            return None
        if len(sample.text) > self.max_text_length:
            return None

        return sample


class Dataset:
    def __init__(self,
        dataset_config:dict,
        sample_loader_config:dict,
        data_zoo_path:str = G_DEFAULT_DATA_ZOO,
    ) :
        self.samples = []
        data_zoo = OmegaConf.load(data_zoo_path)

        for subset in dataset_config.subsets:
            if subset.max_num_samples == 0:
                continue
            elif subset.max_num_samples < 0:
                subset.max_num_samples = sys.maxsize # https://docs.python.org/3/library/sys.html#sys.maxsize

            # retrive dataset info from data zoo
            subset_dir, subset_meta = data_zoo[subset.id].dir, data_zoo[subset.id].metadata
            logging.info(f'Loading {subset.id} from ({subset_dir} : {subset_meta}) ...')
            with open(subset_meta, 'r', encoding='utf8') as f:
                if str.endswith(subset_meta, '.tsv'):
                    utterance_reader = csv.DictReader(f, delimiter='\t')
                else:
                    raise NotImplementedError

                sample_loader = SampleLoader(**sample_loader_config, data_dir = subset_dir)
                k = 0
                for utt in utterance_reader:
                    if k >= subset.max_num_samples:
                        break
                    if sample := sample_loader(utt):
                        self.samples.append(sample)
                        k += 1
                logging.info(f'{k} samples loaded from {subset.id}')
        logging.info(F'Total {len(self.samples)} loaded.')
        # length sort

        # shuffle

    def __getitem__(self, index:int):
        return self.samples[index]

    def __len__(self):
        return len(self.samples)


# https://github.com/lhotse-speech/lhotse/blob/master/lhotse/utils.py#L367 : compute_num_samples()
def seconds_to_samples(sample_rate:int, seconds:float):
    """
    Convert a time quantity to the number of samples given a specific sampling rate.
    Performs consistent rounding up or down for ``duration`` that is not a multiply of
    the sampling interval (unlike Python's built-in ``round()`` that implements banker's rounding).
    """
    return int(
        decimal.Decimal(
            round(seconds * sample_rate, ndigits=8)
        ).quantize(0, rounding=decimal.ROUND_HALF_UP)
    )


def torch_audio_load(audio_path:str, begin:float, duration:float) :
    '''
    https://pytorch.org/tutorials/beginner/audio_preprocessing_tutorial.html#audio-i-o

    torchaudio.info(sample.audio)
    ->
    AudioMetaData(
        sample_rate=16000, num_frames=31872, num_channels=1, bits_per_sample=16, encoding=PCM_S,
    )
    '''
    info = torchaudio.info(audio_path)
    waveform, sample_rate = torchaudio.load(
        audio_path,
        frame_offset = seconds_to_samples(info.sample_rate, begin),
        num_frames   = seconds_to_samples(info.sample_rate, duration),
    )
    return waveform, sample_rate


class Resampler:
    def __init__(self, sample_rate:int):
        self.target_sample_rate = sample_rate

    def __call__(self, waveform:torch.Tensor, sample_rate:int):
        if sample_rate != self.target_sample_rate:
            waveform = torchaudio.transforms.Resample(sample_rate, self.target_sample_rate)(waveform)
        return waveform, self.target_sample_rate


class Perturbation:
    def __init__(self,
        mark_key:bool = False,
        speeds:Optional[list[float]] = None,
        tempos:Optional[list[float]] = None,
        volumes:Optional[list[float]] = None,
    ) :
        self.mark_key = mark_key
        self.speeds = speeds
        self.tempos = tempos
        self.volumes = volumes

    def __call__(self, key:str, waveform:torch.Tensor, sample_rate:int):
        '''
        Note: Regarding to 'speed' and 'tempo' perturbation:

        in classic SoX CLI:
            soxi raw.wav -> sample_rate: 16000, duration: 00:00:01.99 = 31872 samples

            sox raw.wav speed.wav speed 1.5
            soxi speed.wav -> sample_rate: 16000, 00:00:01.33 = 21248 sample

            sox raw.wav tempo.wav tempo 1.5
            soxi tempo.wav -> sample_rate: 16000, 00:00:01.33 = 21248 sample

        whereas in torchaudio.sox_effect function calls:
            output waveform sample_rate is changed,
            so here we need explicitly 'rate' resampling after 'speed' or 'tempo'

        '''
        effects_chain = []
        if self.speeds:
            if (factor := random.choice(self.speeds)) != 1.0:
                effects_chain.extend([
                    ['speed', str(factor)],
                    ['rate', str(sample_rate)]
                ])
                if self.mark_key:
                    key = f'{key}__speed{factor}'

        if self.tempos:
            if (factor := random.choice(self.tempos)) != 1.0:
                effects_chain.extend([
                    ['tempo', str(factor)],
                    ['rate', str(sample_rate)]
                ])
                if self.mark_key:
                    key = f'{key}__tempo{factor}'

        if self.volumes:
            if (factor := random.choice(self.volumes)) != 1.0:
                effects_chain.append(['vol', str(factor)])
                if self.mark_key:
                    key = f'{key}__vol{factor}'

        if effects_chain:
            new_waveform, new_sample_rate = torchaudio.sox_effects.apply_effects_tensor(
                waveform, sample_rate,
                effects_chain,
            )
            assert new_sample_rate == sample_rate # perturbation shouldn't change sample_rate
            waveform, sample_rate = new_waveform, new_sample_rate

        return key, waveform, sample_rate


class FbankFeatureExtractor:
    def __init__(self, num_mel_bins:int, dither:float = 0.0):
        self.num_mel_bins = num_mel_bins
        self.dither = dither

    def __call__(self, waveform:torch.Tensor, sample_rate:int):
        '''
        kaldi:
            https://github.com/kaldi-asr/kaldi/blob/master/src/feat/mel-computations.h#L60
            https://github.com/kaldi-asr/kaldi/blob/master/src/feat/feature-fbank.h#L62

        torchaudio:
            https://pytorch.org/audio/stable/compliance.kaldi.html
        '''
        # By default, torchaudio uses normalized 32bits float waveform [-1.0, 1.0]
        # To use Kaldi compliance function, waveform needs to be convert to 16bits signed-interger PCM [-32768, 32767]
        # TODO:
        # torchaudio's feature extraction is not consistent with Kaldi https://github.com/pytorch/audio/issues/400
        # torchaudio official plan to bind kaldi feat lib: https://github.com/pytorch/audio/issues/1269
        # to not finished up to 2021-10-02 : https://github.com/pytorch/audio/pull/1326
        # keep an eye on this work and do it myself if necessary
        assert waveform.dtype == torch.float32
        INT16PCM_waveform = waveform * torch.iinfo(torch.int16).max
        feature = torchaudio.compliance.kaldi.fbank(
            INT16PCM_waveform,
            sample_frequency = sample_rate,
            num_mel_bins = self.num_mel_bins,
            dither = self.dither,
            energy_floor = torch.finfo(torch.float).eps,
            # about energy_floor:
            #   Kaldi default = 0.0; torchaudio default = 1.0;
            #   it doesn't matter if use_energy = False (default in both)
        )

        return feature


class MeanVarStats:
    def __init__(self):
        self.o1_stats = None
        self.o2_stats = None
        self.n = 0

    def __repr__(self):
        return (
            '\nGlobal MEAN/VAR stats:\n'
            f'    1st_order:  {self.o1_stats}\n'
            f'    2nd_order:  {self.o2_stats}\n'
            f'    frames:   {self.n}\n'
        )

    def accumulate_mean_var_stats(self, feature:torch.Tensor):
        num_frames, feature_dim = feature.shape
        if self.n == 0:
            self.o1_stats = torch.zeros(feature_dim)
            self.o2_stats = torch.zeros(feature_dim)

        assert self.o1_stats.shape[0] == feature_dim, f'mvn accumulator dim {self.o1_stats.shape[0]} inconsistent with feature dim {feature_dim}'
        self.o1_stats += feature.sum(dim=0)
        self.o2_stats += feature.square().sum(dim=0)
        self.n += num_frames

    def load(self, filename:str):
        with open(filename, 'r') as f:
            stats = json.load(f)
            self.o1_stats = torch.Tensor(stats['o1_stats'])
            self.o2_stats = torch.Tensor(stats['o2_stats'])
            self.n = stats['n']
        return self

    def dump(self, filename:str):
        stats = {
            'o1_stats': self.o1_stats.tolist(),
            'o2_stats': self.o2_stats.tolist(),
            'n': self.n,
        }
        with open(filename, 'w+') as f:
            json.dump(stats, f, indent=4)


class MeanVarNormalizer:
    def __init__(self, mean_var_stats:MeanVarStats):
        mean = mean_var_stats.o1_stats / mean_var_stats.n
        var  = mean_var_stats.o2_stats / mean_var_stats.n - mean.square()
        self.mean_norm_shift = -mean
        self.var_norm_scale = var.sqrt().clamp(min = torch.finfo(torch.float32).eps).reciprocal()

    def __repr__(self):
        return (
            '\nGlobal MEAN/VAR normalizer:\n'
            f'    mean_norm_shift:  {self.mean_norm_shift}\n'
            f'    var_norm_scale:  {self.var_norm_scale}\n'
        )

    def __call__(self, feature:torch.Tensor):
        feature += self.mean_norm_shift
        feature *= self.var_norm_scale
        return feature


class SpecAugment:
    def __init__(
        self,
        mark_key:bool = False,
        num_t_masks:int = 2,
        t_mask_width_min:int = 1,
        t_mask_width_max:int = 50,
        num_f_masks:int = 2,
        f_mask_width_min:int = 1,
        f_mask_width_max:int = 10,
    ) :
        self.mark_key = mark_key

        self.num_t_masks = num_t_masks
        self.t_mask_width_min = t_mask_width_min
        self.t_mask_width_max = t_mask_width_max

        self.num_f_masks = num_f_masks
        self.f_mask_width_min = f_mask_width_min
        self.f_mask_width_max = f_mask_width_max

    def __call__(self, key:str, feature:torch.Tensor) :
        assert(feature.dim() == 2)
        T, F = feature.shape

        for _ in range(self.num_t_masks):
            t = random.randrange(0, T)
            k = random.randint(self.t_mask_width_min, self.t_mask_width_max)
            feature[t : t + k, :] = 0.0

        for _ in range(self.num_f_masks):
            f = random.randrange(0, F)
            k = random.randint(self.f_mask_width_min, self.f_mask_width_max)
            feature[:, f : f + k] = 0.0

        if self.mark_key:
            key = f'{key}__SpecAugment'
        return key, feature


class Tokenizer:
    def __init__(self,
        model_path:str,
        vocab_path:str,
        blk:str = '<blk>',
        bos:str = '<s>',
        eos:str = '</s>',
        sil:str = '<sil>',
        unk:str = '<unk>',
    ) :
        self.sentence_piece = spm.SentencePieceProcessor()
        self.sentence_piece.load(model_path)

        self.tokens = []
        self.token_to_id = {}
        with open(vocab_path, 'r') as f:
            for l in f:
                if len(cols := l.strip().split()) == 2:
                    word = cols[0]
                    self.token_to_id[word] = len(self.tokens)
                    self.tokens.append(word)

        self.unk, self.unk_index = unk, self.token_to_id[unk]
        self.bos, self.bos_index = bos, self.token_to_id[bos]
        self.eos, self.eos_index = eos, self.token_to_id[eos]
        self.sil, self.sil_index = sil, self.token_to_id.get(sil, self.unk_index)
        self.blk, self.blk_index = blk, self.token_to_id.get(blk, self.unk_index)

    def encode(self, text:str, mode) -> list[int]:
        tokens = []
        if mode == 'id':
            tokens = self.sentence_piece.encode_as_ids(text)
        elif mode == 'piece':
            tokens = self.sentence_piece.encode_as_pieces(text)
        else:
            raise RuntimeError
        return tokens

    def decode(self, tokens:list[int]) -> str:
        return self.sentence_piece.DecodeIds(tokens)

    def size(self):
        return len(self.tokens)

    def __call__(self, text) -> tuple[list[str], list[int]] :
        return self.encode(text, 'piece'), self.encode(text, 'id')


class TextNormalizer:
    def __init__(self, case:str):
        self.case = case

    def __call__(self, text):
        if self.case == 'upper':
            text = text.upper()
        elif self.case == 'lower':
            text = text.lower()
        return text


class DataPipe:
    def __init__(self,
        audio_loader:callable,
        resampler:Optional[callable] = None,
        perturbation:Optional[callable] = None,
        feature_extractor:Optional[callable] = None,
        mean_var_normalizer:Optional[callable] = None,
        spec_augment:Optional[callable] = None,
        text_normalizer:Optional[callable] = None,
        tokenizer:Optional[callable] = None,
    ) :
        self.audio_loader = audio_loader
        self.resampler = resampler
        self.perturbation = perturbation
        self.feature_extractor = feature_extractor
        self.mean_var_normalizer = mean_var_normalizer
        self.spec_augment = spec_augment
        self.text_normalizer = text_normalizer
        self.tokenizer = tokenizer

        logging.info(f'\n    DataPipe components: {[ k for k,v in vars(self).items() if v ]}')


    def __call__(self, samples:list[Sample]):
        samples_processed = []
        for sample in samples:
            # raw audio loading
            key = sample.id

            waveform, sample_rate = self.audio_loader(sample.audio, sample.begin, sample.duration)

            if self.resampler:
                waveform, sample_rate = self.resampler(waveform, sample_rate)

            if self.perturbation:
                key, waveform, sample_rate = self.perturbation(key, waveform, sample_rate)

            # reverb

            # add noise

            # feature extraction
            feature = torch.Tensor()  # default: an empty tensor
            if self.feature_extractor:
                feature = self.feature_extractor(waveform, sample_rate)

            if self.mean_var_normalizer:
                feature = self.mean_var_normalizer(feature)

            # specaug
            if self.spec_augment:
                key, feature = self.spec_augment(key, feature)

            # detach
            feature = feature.detach()

            text = sample.text
            # text normalization
            if self.text_normalizer:
                text = self.text_normalizer(text)

            # tokenization
            token_pieces, token_ids = [], []
            if self.tokenizer:
                token_pieces, token_ids = self.tokenizer(text)

            # store everything here for debug purpose
            samples_processed.append({
                'key': key,
                'waveform': waveform,
                'sample_rate': sample_rate,
                'feature': feature,
                'text': text,
                'token_pieces': token_pieces,
                'token_ids': token_ids,
            })
            logging.debug(f'Processed sample {sample.id} -> {key}')

        features = [ x['feature'] for x in samples_processed ]
        time_lengths = torch.tensor([ len(x) for x in features ])  # [batch_size]
        inputs = nn.utils.rnn.pad_sequence(
            features,
            batch_first = True,
            padding_value = G_FEATURE_PADDING_VALUE,
        )  # [batch_size, max(time_lengths), frequency]

        labels = [ x['token_ids'] for x in samples_processed ]
        label_lengths = torch.tensor([ len(y) for y in labels ])  # [batch_size]
        targets = nn.utils.rnn.pad_sequence(
            [ torch.tensor(l) for l in labels ],
            batch_first = True,
            padding_value = G_PAD_ID,
        )  # [batch_size, max(label_lengths)]

        num_utts = len(samples_processed)
        num_frames = int(time_lengths.sum())

        return samples_processed, num_utts, num_frames, inputs, time_lengths, targets, label_lengths


def make_length_mask(lengths:torch.Tensor) -> torch.Tensor:
    """Make mask tensor indicating in-length elements.
    Args:
        lengths (torch.Tensor): Batch of lengths (N,).
    Returns:
        torch.Tensor: Bool tensor mask indicating in-length elements.
    """
    B = int(lengths.size(0))
    L = int(lengths.max().item())
    range_tensor = torch.arange(0, L, dtype=torch.int64, device=lengths.device).unsqueeze(0).expand(B, L)
    mask = range_tensor < lengths.unsqueeze(-1)
    return mask


def dump_tensor_to_csv(x:torch.Tensor, filename:str):
    import pandas as pd
    df = pd.DataFrame(x.numpy())
    df.to_csv(filename)


def move_tensor_to_device(*tensors):
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    return tuple([t.to(device) for t in tensors])


def compute_mean_var_stats(dataset, config):
    feature_datapipe = DataPipe(
        audio_loader = torch_audio_load,
        resampler = Resampler(**config.Resampler),
        perturbation = Perturbation(**config.Perturbation),
        feature_extractor = FbankFeatureExtractor(**config.FbankFeatureExtractor),
    )

    # data loaders
    dataloader = torch.utils.data.DataLoader(
        dataset,
        shuffle = False,
        batch_size = 32,
        drop_last = False,
        num_workers = 4,
        collate_fn = feature_datapipe,
    )

    stats = MeanVarStats()
    for batch in dataloader:
        samples, *_ = batch
        for sample in samples:
            stats.accumulate_mean_var_stats(sample['feature'])  # [Time, Freq]
    return stats


def load_model(model_id:str, model_hparam:str, input_dim, tokenizer):
    if  model_id == 'conformer':
        from core.conformer import Model
        model = Model(
            os.path.join(os.path.dirname(__file__), model_hparam),
            input_dim,
            tokenizer.size(),
            blk_index = tokenizer.blk_index,
            bos_index = tokenizer.bos_index,
            eos_index = tokenizer.eos_index,
            unk_index = tokenizer.unk_index,
            sil_index = tokenizer.sil_index,
        )
        logging.info(
            'Total params: '
            f'{sum([ p.numel() for p in model.parameters() ])/float(1e6):.2f}M '
            'Trainable params: '
            f'{sum([ p.numel() for p in model.parameters() if p.requires_grad ])/float(1e6):.2f}M '
        )
        return model
    else:
        raise NotImplementedError(f'Unsupported model_id: {model_id}')


def train(config_path, dir):
    config = OmegaConf.load(config_path)
    print(OmegaConf.to_yaml(config), file = sys.stderr, flush = True)

    train_dataset = Dataset(config.train_set, config.get('SampleLoader', {}))
    valid_dataset = Dataset(config.valid_set, config.get('SampleLoader', {}))

    # mean var normalization
    mean_var_stats_file = os.path.join(dir, 'mean_var_stats.json')
    if os.path.isfile(mean_var_stats_file):
        logging.info(f'Loading mean/var stats <- {mean_var_stats_file}')
        mean_var_stats = MeanVarStats().load(mean_var_stats_file)
    else:
        logging.info(f'Computing mean/var stats -> {mean_var_stats_file}')
        mean_var_stats = compute_mean_var_stats(train_dataset, config)
        mean_var_stats.dump(mean_var_stats_file)
    mvn = MeanVarNormalizer(mean_var_stats)
    logging.info(mvn)

    tokenizer = Tokenizer(**config.Tokenizer)

    train_datapipe = DataPipe(
        audio_loader = torch_audio_load,
        resampler = Resampler(**config.Resampler) if config.get('Resampler') else None,
        perturbation = Perturbation(**config.Perturbation) if config.get('Perturbation') else None,
        feature_extractor = FbankFeatureExtractor(**config.FbankFeatureExtractor),
        mean_var_normalizer = mvn,
        spec_augment = SpecAugment(**config.SpecAugment) if config.get('SpecAugment') else None,
        text_normalizer = TextNormalizer(**config.TextNormalizer) if config.get('TextNormalizer') else None,
        tokenizer = tokenizer,
    )

    train_dataloader = torch.utils.data.DataLoader(
        train_dataset,
        **config.DataLoader,
        collate_fn = train_datapipe,
    )
    valid_dataloader = torch.utils.data.DataLoader(
        valid_dataset,
        shuffle = False,
        batch_size = config.DataLoader.batch_size,
        drop_last = config.DataLoader.drop_last,
        num_workers = config.DataLoader.num_workers,
        collate_fn = train_datapipe,
    )

    model = load_model(config.model_id, config.model_hparam, config.FbankFeatureExtractor.num_mel_bins, tokenizer)
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    model.to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr = config.optimizer.Adam.lr)

    scheduler = torch.optim.lr_scheduler.LambdaLR(
        optimizer,
        lr_lambda = lambda k: min(
            (k+1)/config.scheduler.warmup_steps,
            (config.scheduler.warmup_steps/(k+1))**0.5
        )
    )

    os.makedirs(os.path.join(dir, 'checkpoints'), exist_ok = True)
    for e in range(1, config.num_epochs + 1): # 1-based indexing
        logging.info(f'Training epoch {e} ...')
        model.train()
        train_loss = 0.0
        train_utts, train_frames = 0, 0
        num_batches = len(train_dataloader)
        for b, batch in enumerate(train_dataloader, 1): # 1-based indexing
            samples, num_utts, num_frames, X, T, Y, U = batch

            X = X.to(device)
            T = T.to(device)
            Y = Y.to(device)
            U = U.to(device)
            loss = model(X, T, Y, U)

            (loss / num_utts / config.gradient_accumulation).backward()
            if b % config.gradient_accumulation == 0:
                if torch.isfinite(nn.utils.clip_grad_norm_(model.parameters(), config.gradient_clipping)):
                    optimizer.step()
                optimizer.zero_grad()
                scheduler.step()

            train_loss += loss.item()
            train_utts += num_utts
            train_frames += num_frames
            train_utt_loss, train_frame_loss = train_loss/train_utts, train_loss/train_frames

            if b % config.log_interval == 0:
                logging.info(f'  [{e}/{config.num_epochs}]:[{b}/{num_batches}] {train_utt_loss:7.2f} LR={scheduler.get_last_lr()[0]:7.6f}')

        torch.save(model.state_dict(), os.path.join(dir, 'checkpoints', f'{e}.pt'))

        # validation
        logging.info(f'Validating epoch {e} ...')
        with torch.no_grad():
            model.eval()
            valid_loss = 0.0
            valid_utts, valid_frames = 0, 0
            for b, batch in enumerate(valid_dataloader, 1):
                samples, num_utts, num_frames, X, T, Y, U = batch

                X = X.to(device)
                T = T.to(device)
                Y = Y.to(device)
                U = U.to(device)
                loss = model(X, T, Y, U)

                valid_loss += loss.item()
                valid_utts += num_utts
                valid_frames += num_frames
                valid_utt_loss, valid_frame_loss = valid_loss/valid_utts, valid_loss/valid_frames

        # epoch summary
        logging.info(
            f'\nEpoch[{e}]'
            f'  train_utt_loss:{train_utt_loss:7.2f}'
            f'  valid_utt_loss:{valid_utt_loss:7.2f}'
            f'  loss_diff:{train_utt_loss - valid_utt_loss:7.2f}'
        )


def recognize(config_path, dir):
    config = OmegaConf.load(config_path)
    print(OmegaConf.to_yaml(config), file = sys.stderr, flush = True)

    mean_var_stats_file = os.path.join(dir, 'mean_var_stats.json')
    logging.info(f'Loading mean/var stats <- {mean_var_stats_file}')
    mvn = MeanVarNormalizer(MeanVarStats().load(mean_var_stats_file))

    tokenizer = Tokenizer(**config.Tokenizer)

    datapipe = DataPipe(
        audio_loader = torch_audio_load,
        resampler = Resampler(**config.Resampler) if config.get('Resampler') else None,
        perturbation = Perturbation(**config.Perturbation) if config.get('Perturbation') else None,
        feature_extractor = FbankFeatureExtractor(**config.FbankFeatureExtractor),
        mean_var_normalizer = mvn,
        spec_augment = SpecAugment(**config.SpecAugment) if config.get('SpecAugment') else None,
        text_normalizer = TextNormalizer(**config.TextNormalizer) if config.get('TextNormalizer') else None,
        tokenizer = tokenizer,
    )

    dataset = Dataset(config.test_set, config.get('SampleLoader', {}))
    dataloader = torch.utils.data.DataLoader(
        dataset,
        shuffle = False,
        batch_size = 1,
        drop_last = False,
        num_workers = 1,
        collate_fn = datapipe,
    )

    checkpoint_path = os.path.join(dir, 'final.pt')
    assert os.path.isfile(checkpoint_path)
    checkpoint = torch.load(checkpoint_path)

    model = load_model(config.model_id, config.model_hparam, config.FbankFeatureExtractor.num_mel_bins, tokenizer)
    model.load_state_dict(checkpoint)
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    model.to(device)

    logging.info('Decoding ...')
    with torch.no_grad():
        model.eval()
        for b, batch in enumerate(dataloader):
            samples, num_utts, num_frames, X, T, _, _ = batch
            assert num_utts == 1

            X = X.to(device)
            T = T.to(device)
            hyps = model.decode(X, T)

            print(f'{b}\t{samples[0]["key"]}\t{tokenizer.decode(hyps[0])}\t{hyps[0]}', file=sys.stderr, flush=True)
