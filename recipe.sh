#!/usr/bin/env bash

config=config/stt_zh
dir=exp/stt_zh
text=data/text/AISHELL-1_train.txt

stage=0

if [ $stage -le 0 ]; then
    mkdir -p $dir
    cp $config/* $dir/
fi

if [ $stage -le 1 ]; then
    echo "Training tokenizer from text: "
    sio/tokenizer_train --config $dir/tokenizer.yaml --input $text --model $dir/tokenizer 2>$dir/log.tokenizer
fi

if [ $stage -le 2 ]; then
    echo "Traning stt model ..."
    sio/stt_train --node_rank 0 --config $dir/train.yaml $dir 2>$dir/log.train
fi

if [ $stage -le 3 ]; then
    echo "Averaging model checkpoints ..."
    sio/stt_average $dir/checkpoints $dir/final.model 2>$dir/log.average

    echo "Exporting torchscript model ..."
    sio/stt_export --config $dir/train.yaml $dir/final.model $dir/final.ts 2>$dir/log.export
fi

if [ $stage -le 4 ]; then
    echo "Decoding test set ..."
    sio/stt --config $dir/test.yaml $dir 1> $dir/test.txt 2>$dir/log.test
fi

if [ $stage -le 5 ]; then
    echo "Evaluating error rate ..."
    awk -F'\t' '{print $2, $3}' $dir/test.txt >$dir/rec.txt
    sio/stt_error_rate --tokenizer char --ref $dir/ref.txt --hyp $dir/rec.txt $dir/RESULT 2>$dir/log.eval
fi
