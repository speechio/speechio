#!/usr/bin/env bash

text_data=data/text/AISHELL-1_train.txt

stage=0
nj=40

if [ $stage -le 0 ]; then
    for x in tokenizer.yaml stt.yaml stt_test.yaml lm.yaml $text; do
        [ -f $x ] || { echo "Error: Cannot find $x"; exit 1; }
    done
    [ -d data ] || { echo "No data dir, try 'ln -s ../../data data'"; exit 1; }
    [ -d ops ] || { echo "No ops dir, try 'ln -s ../../ops ops'"; exit 1; }
fi


if [ $stage -le 1 ]; then
    echo "normalizing raw text ..."
    ops/text_norm -n $nj -i ${text_data} -o text.txt 2>log.text_norm
fi


if [ $stage -le 2 ]; then
    echo "Training tokenizer ..."
    ops/tokenizer_train -c tokenizer.yaml -i text.txt -o tokenizer 2>log.tokenizer
fi


if [ $stage -le 3 ]; then
    echo "Training stt model ..."
    ops/stt_train --node_rank 0 -c stt.yaml -o $(pwd) 2>log.train
fi


if [ $stage -le 4 ]; then
    echo "Averaging model checkpoints ..."
    ops/stt_average -n 20 -i checkpoints -o average.pt 2>log.average

    echo "Exporting torchscript model ..."
    ops/stt_export -c stt.yaml -i average.pt -o final.pts 2>log.export
fi


if [ $stage -le 5 ]; then
    echo "Decoding test set ..."
    ops/stt_test -c stt_test.yaml -o $(pwd) 1>test.tsv 2>log.test
fi


if [ $stage -le 6 ]; then
    echo "Evaluating error rate ..."
    awk -F'\t' '{print $2"\t"$3}' test.tsv >test.hyp
    ops/error_rate  --token char  --ref test.ref  --hyp test.hyp  RESULT  2>log.eval
fi


if [ $stage -le 7 ]; then
    echo "Apply trained tokenizer to raw text ..."
    ops/tokenizer -n $nj -m tokenizer.model -i text.txt -o lm.txt

    echo "Training ARPA from tokenized text ..."
    ops/lm_train -c lm.yaml -v tokenizer.vocab -i lm.txt -o lm
fi

