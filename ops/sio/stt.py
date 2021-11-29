#!/usr/bin/env python3
# coding = utf8
#
# Copyright (c) 2021 Jiayu DU
# All rights reserved.

import os, sys
import decimal
import random
import time
from dataclasses import dataclass
from typing import Optional
from contextlib import nullcontext

import logging
from logging import debug, info, warning

import csv   # metadata
import json  # mvn stats
from omegaconf import OmegaConf

#import numpy
import torch
import torch.nn as nn
import torchaudio
import torchaudio.sox_effects

import sentencepiece as spm
#import k2

# Global Constants
FLOAT_INF = float('inf')
DEFAULT_SEED = 37927
FEATURE_PADDING_VALUE = 0.0
LABEL_PADDING_VALUE = -1
DEFAULT_DB = 'config/db.yaml'


@dataclass
class Sample:
    id:str = ''
    audio:str = ''
    begin:float = 0.0
    duration:float = FLOAT_INF
    text:str = ''
    speaker:str = ''


class SampleLoader:
    ''' A callable wrapper class to load one utterance dict (a tsv/json/jsonl item)
    input:
        utt_dict = {
            'ID': 'foo_bar',
            'AUDIO': 'audio/foo_bar.wav',
            'BEGIN': 0.0,
            'DURATION': 1.28,
            'TEXT': 'Hey, Siri',
            'SPEAKER': 'Jerry'
        }

    return:
        a Sample object, or None
        None if an utterance doesn't satisfy constraints e.g. duration, text length
    '''
    def __init__(self, 
        field_map:dict = {
            'id': 'ID',
            'audio': 'AUDIO',
            'begin': 'BEGIN',
            'duration': 'DURATION',
            'text': 'TEXT',
            'speaker': 'SPEAKER',
        },
        min_duration:float = 0.0, 
        max_duration:float = FLOAT_INF,
        min_text_length:int = 0, 
        max_text_length:int = sys.maxsize,
    ) :
        self.field_map = field_map

        self.min_duration = min_duration
        self.max_duration = max_duration

        self.min_text_length = min_text_length
        self.max_text_length = max_text_length

    def __call__(self, base_dir, utt:dict) -> Optional[Sample] :
        sample = Sample()
        for attr, field in self.field_map.items():
            if v := utt.get(field):
                if attr in ['duration', 'begin', ]:
                    v = float(v)
                elif attr == 'audio':
                    v = os.path.join(base_dir, v)
                else:
                    v = str(v)
                assert hasattr(sample, attr), f'{field} -> Sample.{attr} mapping failed'
                setattr(sample, attr, v)

        if sample.duration != FLOAT_INF:
            if sample.duration < self.min_duration:
                return None
            if sample.duration > self.max_duration:
                return None
        
        if sample.text:
            if len(sample.text) < self.min_text_length:
                return None
            if len(sample.text) > self.max_text_length:
                return None

        return sample


class Dataset:
    def __init__(self,
        database:dict,
        dataset_config:dict,
        sample_loader:callable = SampleLoader(),
    ) :
        self.samples = []

        for subset in dataset_config.subsets:
            if subset.max_num_samples == 0:  # set this to 0 in config means skipping
                continue
            elif subset.max_num_samples < 0:
                subset.max_num_samples = sys.maxsize

            base_dir = database[subset.id].dir
            metadata = database[subset.id].metadata
            debug(f'  Loading {subset.id} from ({base_dir} : {metadata}) ...')

            with open(metadata, 'r', encoding='utf8') as f:
                if str.endswith(metadata, '.tsv'):
                    utts_reader = csv.DictReader(f, delimiter='\t')

                    if sample_loader.field_map['begin'] not in utts_reader.fieldnames:
                        warning(
                            'Metadata provides nothing for Sample.begin to load, '
                            'using default value 0.0'
                        )
                    if sample_loader.field_map['duration'] not in utts_reader.fieldnames:
                        warning(
                            'Metadata provides nothing for Sample.duration to load, '
                            'min/max_duration filtering will be turned OFF.'
                        )
                    if sample_loader.field_map['text'] not in utts_reader.fieldnames:
                        warning(
                            'Metadata provides nothing for Sample.text to load, '
                            'min/max_text_length filtering will be turned OFF.'
                        )
                else:
                    raise NotImplementedError

                # Invariant: self.samples[0, k) are loaded
                k = 0  # Precondition: k == 0
                for utt in utts_reader:
                    if k < subset.max_num_samples:
                        if sample := sample_loader(base_dir, utt):
                            self.samples.append(sample)
                            k += 1
                    else:
                        break
                # Postcondition: k == min(length of utts_reader, subset.max_num_samples)
                debug(f'  {k} samples loaded from {subset.id}')
        debug(f'Total {len(self.samples)} loaded.')

    def __getitem__(self, index:int):
        return self.samples[index]

    def __len__(self):
        return len(self.samples)


class DatasetView:
    def __init__(self, dataset:Dataset):
        self.dataset = dataset
        self.itable = list(range(len(dataset)))

    def __getitem__(self, i):
        return self.dataset[self.itable[i]]
    
    def __len__(self):
        return len(self.itable)

    def shuffle(self):
        random.shuffle(self.itable)
        return self

    def draw(self, n:int, how:str = 'random'):
        if how == 'random':
            self.itable = random.sample(self.itable, n)
        elif how == 'head':
            self.itable = self.itable[:n]
        elif how == 'tail':
            self.itable = self.itable[-n:]
        return self
    
    def repeat(self, num_copies:int):
        self.itable *= num_copies
        return self

    def shard(self, shard_index:int, num_shards:int):
        self.itable = self.itable[shard_index::num_shards]
        return self

    def sort(self, by_what:str = 'duration', decreasing = True):
        if by_what == 'duration':
            self.itable = sorted(
                self.itable, 
                key = lambda x: self.dataset[x].duration, 
                reverse = decreasing,
            )
        else:
            raise NotImplementedError
        return self


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


def load_audio(path:str, begin:float = 0.0, duration:float = FLOAT_INF) :
    '''
    https://pytorch.org/tutorials/beginner/audio_preprocessing_tutorial.html#audio-i-o

    torchaudio.info(sample.audio)
    ->
    AudioMetaData(
        sample_rate=16000, num_frames=31872, num_channels=1, bits_per_sample=16, encoding=PCM_S,
    )
    '''
    meta = torchaudio.info(path)
    actual_duration = min(
        meta.num_frames / meta.sample_rate - begin,
        duration,
    )
    waveform, sample_rate = torchaudio.load(
        path,
        frame_offset = seconds_to_samples(meta.sample_rate, begin),
        num_frames   = seconds_to_samples(meta.sample_rate, actual_duration),
    )
    return waveform, sample_rate, actual_duration


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
                    key += f'__speed{factor}'

        if self.tempos:
            if (factor := random.choice(self.tempos)) != 1.0:
                effects_chain.extend([
                    ['tempo', str(factor)],
                    ['rate', str(sample_rate)]
                ])
                if self.mark_key:
                    key += f'__tempo{factor}'

        if self.volumes:
            if (factor := random.choice(self.volumes)) != 1.0:
                effects_chain.append(['vol', str(factor)])
                if self.mark_key:
                    key += f'__vol{factor}'

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
        # To use Kaldi compliance function, 
        # waveform needs to be convert to 16bits signed-interger PCM [-32768, 32767]
        # TODO:
        # torchaudio's feature extraction is not consistent with Kaldi:
        #   https://github.com/pytorch/audio/issues/400
        # torchaudio official plan to bind kaldi feat lib: 
        #   https://github.com/pytorch/audio/issues/1269
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
        self.o1_sum = None
        self.o2_sum = None
        self.n = 0

    def __repr__(self):
        return (
            '\nGlobal MEAN/VAR stats:\n'
            f'    1st_order:  {self.o1_sum}\n'
            f'    2nd_order:  {self.o2_sum}\n'
            f'    frames:   {self.n}\n'
        )

    def accumulate_mean_var_stats(self, feature:torch.Tensor):
        num_frames, feature_dim = feature.shape
        if self.n == 0:
            self.o1_sum = torch.zeros(feature_dim)
            self.o2_sum = torch.zeros(feature_dim)
        assert self.o1_sum.shape[0] == feature_dim
        assert self.o2_sum.shape[0] == feature_dim

        self.o1_sum += feature.sum(dim=0)
        self.o2_sum += feature.square().sum(dim=0)
        self.n += num_frames

    def load(self, path:str):
        info(f'Loading mean/var stats <- {path}')
        with open(path, 'r') as f:
            stats = json.load(f)
            self.o1_sum = torch.tensor(stats['o1_sum'])
            self.o2_sum = torch.tensor(stats['o2_sum'])
            self.n = stats['n']
        return self

    def dump(self, path:str):
        info(f'Dumping mean/var stats -> {path}')
        stats = {
            'o1_sum': self.o1_sum.tolist(),
            'o2_sum': self.o2_sum.tolist(),
            'n': self.n,
        }
        with open(path, 'w+') as f:
            json.dump(stats, f, indent=4)


class MeanVarNormalizer:
    def __init__(self, mean_var_stats:MeanVarStats):
        mean = mean_var_stats.o1_sum / mean_var_stats.n
        var  = mean_var_stats.o2_sum / mean_var_stats.n - mean.square()
        isd  = var.sqrt().clamp(min = torch.finfo(torch.float32).eps).reciprocal()
        self.mean_norm_shift = -mean
        self.var_norm_scale = isd

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
    def __init__(self,
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
            key += '__SpecAugment'
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
        self.token_to_idx = {}
        with open(vocab_path, 'r') as f:
            for l in f:
                if len(cols := l.strip().split()) == 2:
                    word = cols[0]
                    self.token_to_idx[word] = len(self.tokens)
                    self.tokens.append(word)

        self.unk, self.unk_index = unk, self.token_to_idx[unk]
        self.bos, self.bos_index = bos, self.token_to_idx[bos]
        self.eos, self.eos_index = eos, self.token_to_idx[eos]
        self.sil, self.sil_index = sil, self.token_to_idx.get(sil, self.unk_index)
        self.blk, self.blk_index = blk, self.token_to_idx.get(blk, self.unk_index)

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
        resampler:Optional[callable] = None,
        perturbation:Optional[callable] = None,
        feature_extractor:Optional[callable] = None,
        mean_var_normalizer:Optional[callable] = None,
        spec_augment:Optional[callable] = None,
        text_normalizer:Optional[callable] = None,
        tokenizer:Optional[callable] = None,
    ) :
        self.resampler = resampler
        self.perturbation = perturbation
        self.feature_extractor = feature_extractor
        self.mean_var_normalizer = mean_var_normalizer
        self.spec_augment = spec_augment
        self.text_normalizer = text_normalizer
        self.tokenizer = tokenizer
    
    def __repr__(self):
        return f'\n    DataPipe: {[ k for k,v in vars(self).items() if v ]}'

    def __call__(self, raw_samples:list[Sample]):
        samples = []
        for sample in raw_samples:
            key = sample.id

            waveform, sample_rate, sample.duration = load_audio(
                sample.audio, sample.begin, sample.duration
            ) # This ensures sample.duration consistent with actually loaded wave length

            if self.resampler:
                waveform, sample_rate = self.resampler(waveform, sample_rate)

            if self.perturbation:
                key, waveform, sample_rate = self.perturbation(key, waveform, sample_rate)

            # reverb

            # add noise

            feature = torch.tensor([])  # default: an empty tensor
            if self.feature_extractor:
                feature = self.feature_extractor(waveform, sample_rate)

            if self.mean_var_normalizer:
                feature = self.mean_var_normalizer(feature)

            if self.spec_augment:
                key, feature = self.spec_augment(key, feature)

            # detach
            feature = feature.detach()

            text = sample.text
            if self.text_normalizer:
                text = self.text_normalizer(text)

            token_pieces, token_ids = [], []
            if self.tokenizer:
                token_pieces, token_ids = self.tokenizer(text)

            samples.append({
                'key': key,
                'waveform': waveform,
                'sample_rate': sample_rate,
                'feature': feature,
                'text': text,
                'token_pieces': token_pieces,
                'token_ids': token_ids,
            })
            #debug(f'Processed sample {sample.id} -> {key}')

        features = [ s['feature'] for s in samples ]
        inputs = nn.utils.rnn.pad_sequence(
            features,
            batch_first = True,
            padding_value = FEATURE_PADDING_VALUE,
        )  # [batch_size, max(num_time_frames), fbank_dim]
        input_lengths = torch.tensor([ len(x) for x in features ])  # [batch_size]

        labels = [ torch.tensor(s['token_ids']) for s in samples ]
        targets = nn.utils.rnn.pad_sequence(
            labels,
            batch_first = True,
            padding_value = LABEL_PADDING_VALUE,
        )  # [batch_size, max(num_label_tokens)]
        target_lengths = torch.tensor([ len(y) for y in labels ])  # [batch_size]

        num_utts = inputs.shape[0]
        num_frames = input_lengths.sum().item()

        return samples, num_utts, num_frames, inputs, input_lengths, targets, target_lengths


def dump_tensor_to_csv(x:torch.Tensor, path:str):
    import pandas as pd
    df = pd.DataFrame(x.numpy())
    df.to_csv(path)


def compute_mean_var_stats(dataset, config):
    feature_datapipe = DataPipe(
        resampler = Resampler(**c) if (c := config.get('resampler')) else None,
        perturbation = Perturbation(**c) if (c := config.get('perturbation')) else None,
        feature_extractor = FbankFeatureExtractor(**config.fbank_feature_extractor),
    )

    dataloader = torch.utils.data.DataLoader(
        dataset,
        shuffle = False,
        batch_size = 16,
        drop_last = False,
        num_workers = 8,
        collate_fn = feature_datapipe,
    )

    info(f'Computing mean var stats ...')
    stats = MeanVarStats()
    for batch in dataloader:
        samples, *_ = batch
        for sample in samples:
            stats.accumulate_mean_var_stats(sample['feature'])
    return stats


def create_model(model_name:str, model_hparam:str, input_dim, tokenizer):
    if  model_name == 'wenet':
        from .wenet import Model
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
        return model
    else:
        raise NotImplementedError(f'Unsupported model: {model_name}')


def load_model_checkpoint(model:nn.Module, device, path:str):
    state_dict = torch.load(path, map_location = device)
    if isinstance(model, nn.parallel.DistributedDataParallel):
        model.module.load_state_dict(state_dict)
    else:
        model.load_state_dict(state_dict)


def dump_model_checkpoint(model:nn.Module, path:str):
    if isinstance(model, nn.parallel.DistributedDataParallel):
        state_dict = model.module.state_dict()
    else:
        state_dict = model.state_dict()
    torch.save(state_dict, path)


def average_model_checkpoints(checkpoint_paths:list[str]):
    from functools import reduce

    N = len(checkpoint_paths)
    print(f'averaging {N} models: {checkpoint_paths}', file=sys.stderr, flush=True)
    
    summed = reduce(
        lambda x, y: { k: x[k] + y[k] for k in x.keys() }, # sum of two "pytorch state dicts"
        [ torch.load(f, map_location=torch.device('cpu')) for f in checkpoint_paths ],
    )
    averaged = { k : torch.true_divide(v, N) for k,v in summed.items() }
    return averaged


def seed_all(seed:int):
    random.seed(seed)
    #np.random.seed(seed) # numpy not used for now
    torch.manual_seed(seed)


def ddp_barrier():
    if torch.distributed.is_initialized(): 
        torch.distributed.barrier()


def train(config, dir:str, device_id:int, world_size:int, rank:int):
    logging.basicConfig(
        stream=sys.stderr, 
        level=logging.DEBUG if rank == 0 else logging.INFO,
        format = f'\x1B[1;32m%(asctime)s [Rank={rank}/{world_size}:%(levelname)s] %(message)s\x1B[0m',
    )
    debug(f'\n{OmegaConf.to_yaml(config)}\n')

    # Setup envrionment
    seed_all(DEFAULT_SEED)
    checkpoint_dir = os.path.join(dir, 'checkpoints')
    if rank == 0: os.makedirs(checkpoint_dir, exist_ok = True)

    if world_size > 1:
        import torch.distributed as dist
        os.environ['MASTER_ADDR'] = str(config.ddp_master_addr)
        os.environ['MASTER_PORT'] = str(config.ddp_master_port)
        dist.init_process_group(config.ddp_backend, rank = rank, world_size = world_size)
        distributed = True
    else:
        distributed = False

    device = torch.device('cuda', device_id) if torch.cuda.is_available() else torch.device('cpu')
    info(f'Rank:{rank} -> device:{device}')

    # Vocabulary
    tokenizer = Tokenizer(**config.tokenizer)

    # Model
    model = create_model(
        config.model_name, 
        config.model_hparam, 
        config.fbank_feature_extractor.num_mel_bins, 
        tokenizer,
    )
    debug(
        'Total params: '
        f'{sum([ p.numel() for p in model.parameters() ])/1e6:.2f}M '
        'Trainable params: '
        f'{sum([ p.numel() for p in model.parameters() if p.requires_grad ])/1e6:.2f}M '
    )
    model.to(device)
    pretrained_or_initial_model = os.path.join(checkpoint_dir, '0.model')
    if os.path.isfile(pretrained_or_initial_model):
        load_model_checkpoint(model, device, pretrained_or_initial_model)

    if distributed:
        from torch.nn.parallel import DistributedDataParallel as DDP
        model = DDP(model, find_unused_parameters=True)
    
    # Load train/valid sets
    db = OmegaConf.load(DEFAULT_DB)

    sample_loader = SampleLoader(**config.get('sample_loader', {}))
    debug('Loading train_set ...')
    train_dataset = Dataset(db, config.train_set, sample_loader)
    debug('Loading valid_set ...')
    valid_dataset = Dataset(db, config.valid_set, sample_loader)
    ddp_barrier()

    # Create pre-processing data pipeline
    mean_var_stats_file = os.path.join(dir, 'mean_var_stats.json')
    if rank == 0:
        if not os.path.isfile(mean_var_stats_file):
            mean_var_stats = compute_mean_var_stats(train_dataset, config)
            mean_var_stats.dump(mean_var_stats_file)
    ddp_barrier()
    mean_var_stats = MeanVarStats().load(mean_var_stats_file)

    datapipe = DataPipe(
        resampler = Resampler(**c) if (c := config.get('resampler')) else None,
        perturbation = Perturbation(**c) if (c := config.get('perturbation')) else None,
        feature_extractor = FbankFeatureExtractor(**config.fbank_feature_extractor),
        mean_var_normalizer = MeanVarNormalizer(mean_var_stats),
        spec_augment = SpecAugment(**c) if (c := config.get('spec_augment')) else None,
        text_normalizer = TextNormalizer(**c) if (c := config.get('text_normalizer')) else None,
        tokenizer = tokenizer,
    )
    debug(datapipe.mean_var_normalizer)
    debug(datapipe)

    # Dataloaders
    #train_dataset_view = DatasetView(train_dataset).repeat(10).sort_by('duration')
    if distributed:
        from torch.utils.data.distributed import DistributedSampler
        sampler = DistributedSampler(train_dataset, shuffle=True) 
    else:
        sampler = None

    train_dataloader = torch.utils.data.DataLoader(
        train_dataset,
        **config.data_loader,
        collate_fn = datapipe,
        shuffle = False if distributed else True,
        sampler = sampler,
    )

    valid_dataloader = torch.utils.data.DataLoader(
        valid_dataset,
        **config.data_loader,
        collate_fn = datapipe,
        shuffle = False,
    )

    # Trainer
    optimizer = torch.optim.Adam(model.parameters(), lr = config.optimizer.Adam.lr)
    scheduler = torch.optim.lr_scheduler.LambdaLR(
        optimizer,
        lr_lambda = lambda k: min(
            (k+1)/config.scheduler.warmup_steps,
            (config.scheduler.warmup_steps/(k+1))**0.5
        )
    ) # warmup scheduler

    need_resume = False
    for e in range(1, config.num_epochs + 1): # 1-based indexing, 0 reserved for init/pretrain
        debug(f'On epoch {e} ...')

        checkpoint = os.path.join(checkpoint_dir, f'{e}.done.json')
        if os.path.isfile(checkpoint):
            debug(f'Skipping epoch {e}, found checkpoint: {checkpoint}')
            need_resume = True
            continue

        if need_resume and not os.path.isfile(checkpoint):
            if os.path.isfile(prev := os.path.join(checkpoint_dir, f'{e-1}.model')):
                debug(f'Resuming model from: {prev}')
                load_model_checkpoint(model, device, prev)

            if os.path.isfile(prev := os.path.join(checkpoint_dir, f'{e-1}.optimizer')):
                debug(f'Resuming optimizer from: {prev}')
                optimizer.load_state_dict(torch.load(prev, map_location=device))

            if os.path.isfile(prev := os.path.join(checkpoint_dir, f'{e-1}.scheduler')):
                debug(f'Resuming scheduler from: {prev}')
                scheduler.load_state_dict(torch.load(prev, map_location=device))

            need_resume = False

        # Here model & optimizer & scheduler should be in well-established states:
        # 1.For training from scratch: 
        #     all newly initialzed
        # 2.For resumed training from failure: 
        #     all loaded from last checkpoint
        # 3.For finetuning: 
        #     model loaded from checkpoint_dir/0.model, optimizer/scheduler newly initialized

        debug(f'Epoch {e} training ...')
        model.train()
        train_loss, train_utts = 0.0, 0
        if distributed: train_dataloader.sampler.set_epoch(e)

        with model.join() if distributed else nullcontext():
            for b, batch in enumerate(train_dataloader, 1): # 1-based indexing
                samples, num_utts, num_frames, X, T, Y, U = batch

                X, T = X.to(device), T.to(device)
                Y, U = Y.to(device), U.to(device)

                with model.no_sync() if distributed and b % config.gradient_accumulation != 0 else nullcontext():
                    loss = model(X, T, Y, U)
                    (loss / num_utts / config.gradient_accumulation).backward()

                if b % config.gradient_accumulation == 0:
                    if torch.isfinite(nn.utils.clip_grad_norm_(model.parameters(), config.gradient_clipping)):
                        optimizer.step()
                    optimizer.zero_grad()
                    scheduler.step()

                train_utts += num_utts
                train_loss += loss.item()
                train_loss_per_utt = train_loss/train_utts

                if b % config.log_interval == 0:
                    info(
                        f'Epoch={e}/{config.num_epochs} Batch={b}/{len(train_dataloader)} '
                        f'{train_loss_per_utt:>7.2f} LR={scheduler.get_last_lr()[0]:7.6f}'
                    )
        
        debug(f'Epoch {e} validation ...')

        model.eval()
        valid_loss, valid_utts = 0.0, 0

        with torch.no_grad():
            for b, batch in enumerate(valid_dataloader, 1):
                samples, num_utts, num_frames, X, T, Y, U = batch

                X, T = X.to(device), T.to(device)
                Y, U = Y.to(device), U.to(device)
                loss = model(X, T, Y, U)

                valid_utts += num_utts
                valid_loss += loss.item()
                valid_loss_per_utt = valid_loss/valid_utts

        # Dump checkpoint
        if rank == 0:
            info(f'Dumping epoch {e} checkpoints to {os.path.join(checkpoint_dir, f"{e}.*")}')
            model_checkpoint     = os.path.join(checkpoint_dir, f'{e}.model')
            optimizer_checkpoint = os.path.join(checkpoint_dir, f'{e}.optimizer')
            scheduler_checkpoint = os.path.join(checkpoint_dir, f'{e}.scheduler')

            dump_model_checkpoint(model, model_checkpoint)
            torch.save(optimizer.state_dict(), optimizer_checkpoint)
            torch.save(scheduler.state_dict(), scheduler_checkpoint)
            summary = {
                'time': time.asctime(),
                'epoch': e,
                'train_loss_per_utt': train_loss_per_utt,
                'train_utts': train_utts,
                'valid_loss_per_utt': valid_loss_per_utt,
                'valid_utts': valid_utts,
                'diff:': train_loss_per_utt - valid_loss_per_utt,
            }
            with open(checkpoint, 'w+') as f:
                json.dump(summary, f)
            info(f'Epoch {e} summary: {summary}')
        ddp_barrier()
        time.sleep(0.5)


def recognize(config_path, dir):
    config = OmegaConf.load(config_path)
    print(OmegaConf.to_yaml(config), file = sys.stderr, flush = True)

    db = OmegaConf.load(DEFAULT_DB)
    dataset = Dataset(db, config.test_set) # with default sample loader

    mean_var_stats_file = os.path.join(dir, 'mean_var_stats.json')
    if os.path.isfile(mean_var_stats_file):
        mean_var_stats = MeanVarStats().load(mean_var_stats_file)
    else:
        raise FileNotFoundError(f'Cannot find mean var stats file: {mean_var_stats_file}')

    tokenizer = Tokenizer(**config.tokenizer)

    datapipe = DataPipe(
        resampler = Resampler(**c) if (c := config.get('resampler')) else None,
        perturbation = Perturbation(**c) if (c := config.get('perturbation')) else None,
        feature_extractor = FbankFeatureExtractor(**config.fbank_feature_extractor),
        mean_var_normalizer = MeanVarNormalizer(mean_var_stats),
        spec_augment = SpecAugment(**c) if (c := config.get('spec_augment')) else None,
        text_normalizer = TextNormalizer(**c) if (c := config.get('text_normalizer')) else None,
        tokenizer = tokenizer,
    )

    dataloader = torch.utils.data.DataLoader(
        dataset,
        shuffle = False,
        batch_size = 1,
        drop_last = False,
        num_workers = 1,
        collate_fn = datapipe,
    )

    model = create_model(
        config.model_name, 
        config.model_hparam, 
        config.fbank_feature_extractor.num_mel_bins, 
        tokenizer
    )
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    model.to(device)
    load_model_checkpoint(model, device, os.path.join(dir, 'final.model'))

    info('Decoding ...')
    with torch.no_grad():
        model.eval()
        for b, batch in enumerate(dataloader):
            samples, num_utts, num_frames, X, T, *_ = batch
            assert num_utts == 1

            X, T = X.to(device), T.to(device)
            hyps = model.decode(X, T)

            print(f'{b}\t{samples[0]["key"]}\t{tokenizer.decode(hyps[0])}\t{hyps[0]}', file=sys.stdout, flush=True)
