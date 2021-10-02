#!/usr/bin/env python3
# coding=utf8
# Copyright 2021  Jiayu DU

import os, sys
import argparse
import csv
from speechcolab.datasets.gigaspeech import GigaSpeech
import torchaudio

gigaspeech_punctuations = ['<COMMA>', '<PERIOD>', '<QUESTIONMARK>', '<EXCLAMATIONPOINT>']
gigaspeech_garbage_utterance_tags = ['<SIL>', '<NOISE>', '<MUSIC>', '<OTHER>']

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Save the audio segments into flac files.')
    parser.add_argument('--subset', choices = ['XS', 'S', 'M', 'L', 'XL', 'DEV', 'TEST'], default='XS', help='The subset name')
    parser.add_argument('gigaspeech_dataset_dir', help='The corpus directory')
    parser.add_argument('output', help='The output directory')
    args = parser.parse_args()

    audio_dir = os.path.join(args.output, 'audio')
    os.makedirs(audio_dir, exist_ok = True)

    gigaspeech = GigaSpeech(args.gigaspeech_dataset_dir)
    subset = '{' + args.subset + '}'
    with open(os.path.join(args.output, 'metadata.tsv'), 'w+', encoding='utf8') as fo:
        csv_header_fields = ['ID', 'AUDIO', 'DURATION', 'TEXT']
        csv_writer = csv.DictWriter(fo, delimiter='\t', fieldnames=csv_header_fields, lineterminator='\n')
        csv_writer.writeheader()
        for audio in gigaspeech.audios(subset):
            audio_path = os.path.join(args.gigaspeech_dataset_dir, audio["path"])

            audio_info = torchaudio.info(audio_path)
            opus_sample_rate = audio_info.sample_rate
            assert opus_sample_rate == 48000
            nc = audio_info.num_channels
            assert nc == 1

            sample_rate = 16000
            long_waveform, _ = torchaudio.load(audio_path)
            long_waveform = torchaudio.transforms.Resample(opus_sample_rate, sample_rate)(long_waveform)

            #print(audio_info)
            for seg in audio['segments']:
                if subset not in seg['subsets']:
                    continue

                text = seg['text_tn']
                for punctuation in gigaspeech_punctuations:
                    text = text.replace(punctuation, '').strip()
                    text = ' '.join(text.split())

                if text in gigaspeech_garbage_utterance_tags:
                    continue

                begin = seg['begin_time'] 
                duration = seg['end_time'] - seg['begin_time']
                frame_offset = int(begin    * sample_rate)
                num_frames   = int(duration * sample_rate)

                waveform = long_waveform[0][frame_offset : frame_offset + num_frames] # channel = mono 

                os.makedirs(os.path.join(audio_dir, audio['aid']), exist_ok = True)
                torchaudio.save(
                    os.path.join(audio_dir, audio['aid'], f'{seg["sid"]}.wav'), 
                    waveform.unsqueeze(0), 
                    sample_rate = sample_rate,
                    format = 'wav',
                    encoding = 'PCM_S',
                    bits_per_sample = 16,
                )

                utt = {'ID': seg['sid'], 'AUDIO': os.path.join('audio', audio['aid'], f'{seg["sid"]}.wav'), 'DURATION': f'{duration:.3f}', 'TEXT': text }
                csv_writer.writerow(utt)
            break

