#!/usr/bin/env bash

tokenizer=../stt_zh/tokenizer

# tokenization
ops/tokenizer_encode  --model $tokenizer  --input text.txt  --output lm.txt

# train arpa
ops/ngram_train  lm.txt  $tokenizer  .  lm

