#!/usr/bin/env bash

text=data/text/AISHELL-1_train.txt

stage=0

if [ $stage -le 0 ]; then
    ln -s $text text
fi

if [ $stage -le 1 ]; then
    echo "Training tokenizer from text: "
    sio/tokenizer_train  --config tokenizer.yaml  --input $text  --model tokenizer  2>log.tokenizer
fi

if [ $stage -le 2 ]; then
    echo "Traning stt model ..."
    sio/stt_train  --node_rank 0  --config train.yaml  .  2>log.train
fi

if [ $stage -le 3 ]; then
    echo "Averaging model checkpoints ..."
    sio/stt_average  checkpoints  final.model  2>log.average

    echo "Exporting torchscript model ..."
    sio/stt_export  --config train.yaml  final.model  final.ts  2>log.export
fi

if [ $stage -le 4 ]; then
    echo "Decoding test set ..."
    sio/stt  --config test.yaml  .  1>test.txt  2>log.test
fi

if [ $stage -le 5 ]; then
    echo "Evaluating error rate ..."
    awk -F'\t' '{print $2, $3}' test.txt >rec.txt
    sio/stt_error_rate  --tokenizer char  --ref ref.txt  --hyp rec.txt  RESULT  2>log.eval
fi
