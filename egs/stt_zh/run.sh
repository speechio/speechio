#!/usr/bin/env bash

text=data/text/AISHELL-1_train.txt

stage=0

if [ $stage -le 0 ]; then
    for x in data.yaml tokenizer.yaml train.yaml test.yaml lm.yaml $text; do
        [ ! -f $x ] || { echo "Error: Cannot find $x"; exit 1; }
    done
    [ ! -d ops ] || { echo "No ops dir, try 'ln -s ../../ops ops'"; exit 1; }
fi


if [ $stage -le 1 ]; then
    echo "Training tokenizer from raw text ..."
    ops/tokenizer_train  --config tokenizer.yaml  --input $text  --model tokenizer  2>log.tokenizer
fi


if [ $stage -le 2 ]; then
    echo "Traning stt model ..."
    ops/stt_train  --node_rank 0  --config train.yaml  .  2>log.train
fi


if [ $stage -le 3 ]; then
    echo "Averaging model checkpoints ..."
    ops/stt_average  checkpoints  average.pt  2>log.average

    echo "Exporting torchscript model ..."
    ops/stt_export  --config train.yaml  average.pt  final.pts  2>log.export
fi


if [ $stage -le 4 ]; then
    echo "Decoding test set ..."
    ops/stt  --config test.yaml  .  1>test.txt  2>log.test
fi


if [ $stage -le 5 ]; then
    echo "Evaluating error rate ..."
    awk -F'\t' '{print $2, $3}' test.txt >rec.txt
    ops/stt_error_rate  --tokenizer char  --ref ref.txt  --hyp rec.txt  RESULT  2>log.eval
fi


if [ $stage -le 6 ]; then
    echo "Apply trained tokenizer to raw text ..."
    ops/tokenizer_encode  --model tokenizer.model  --input $text  --output lm.txt

    echo "Training ARPA from tokenized text ..."
    ops/lm_train  --config lm.yaml  --text lm.txt  --vocab tokenizer.vocab  --model lm
fi

