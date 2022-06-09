#!/usr/bin/env bash

raw_text=data/text/AISHELL-1_train.txt

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
    ops/text_norm -n $nj -i $raw_text -o text.txt 2>log.text_norm
fi


if [ $stage -le 2 ]; then
    echo "Training tokenizer ..."
    ops/tokenizer_train -c tokenizer.yaml -t text.txt -m tokenizer 2>log.tokenizer
fi


if [ $stage -le 3 ]; then
    echo "Training stt model ..."
    ops/stt_train  --config stt.yaml  --node_rank 0  .  2>log.train
fi


if [ $stage -le 4 ]; then
    echo "Averaging model checkpoints ..."
    ops/stt_average  checkpoints  average.pt  2>log.average

    echo "Exporting torchscript model ..."
    ops/stt_export  --config stt.yaml  average.pt  final.pts  2>log.export
fi


if [ $stage -le 5 ]; then
    echo "Decoding test set ..."
    ops/stt_test  --config stt_test.yaml  .  1>test.tsv  2>log.test
fi


if [ $stage -le 6 ]; then
    echo "Evaluating error rate ..."
    awk -F'\t' '{print $2"\t"$3}' test.tsv >test.hyp
    ops/stt_error_rate  --tokenizer char  --ref test.ref  --hyp test.hyp  RESULT  2>log.eval
fi


if [ $stage -le 7 ]; then
    echo "Apply trained tokenizer to raw text ..."
    ops/tokenizer -n $nj -m tokenizer.model -x encode -i text.txt -o lm.txt

    echo "Training ARPA from tokenized text ..."
    ops/lm_train  --config lm.yaml  --text lm.txt  --vocab tokenizer.vocab  --model lm
fi

