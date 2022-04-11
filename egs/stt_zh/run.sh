#!/usr/bin/env bash

raw_text=data/text/AISHELL-1_train.txt

stage=0
nj=40

if [ $stage -le 0 ]; then
    for x in data.yaml tokenizer.yaml train.yaml test.yaml lm.yaml $text; do
        [ -f $x ] || { echo "Error: Cannot find $x"; exit 1; }
    done
    [ -d ops ] || { echo "No ops dir, try 'ln -s ../../ops ops'"; exit 1; }
fi


if [ $stage -le 1 ]; then
    echo "normalizing raw text ..."
    ops/text_norm  --nj $nj  --input $raw_text  --output text.txt  2>log.text_norm
fi


if [ $stage -le 2 ]; then
    echo "Training tokenizer ..."
    ops/tokenizer_train  --config tokenizer.yaml  --input text.txt  --model tokenizer  2>log.tokenizer
fi


if [ $stage -le 3 ]; then
    echo "Training stt model ..."
    ops/stt_train  --node_rank 0  --config train.yaml  .  2>log.train
fi


if [ $stage -le 4 ]; then
    echo "Averaging model checkpoints ..."
    ops/stt_average  checkpoints  average.pt  2>log.average

    echo "Exporting torchscript model ..."
    ops/stt_export  --config train.yaml  average.pt  final.pts  2>log.export
fi


if [ $stage -le 5 ]; then
    echo "Decoding test set ..."
    ops/stt_test  --config test.yaml  .  1>test.tsv  2>log.test
fi


if [ $stage -le 6 ]; then
    echo "Evaluating error rate ..."
    awk -F'\t' '{print $2"\t"$3}' test.tsv >test.hyp
    ops/stt_error_rate  --tokenizer char  --ref test.ref  --hyp test.hyp  RESULT  2>log.eval
fi


if [ $stage -le 7 ]; then
    echo "Apply trained tokenizer to raw text ..."
    ops/tokenizer_encode  --nj $nj  --model tokenizer.model  --input text.txt  --output lm.txt

    echo "Training ARPA from tokenized text ..."
    ops/lm_train  --config lm.yaml  --text lm.txt  --vocab tokenizer.vocab  --model lm
fi

