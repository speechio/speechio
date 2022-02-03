#!/usr/bin/env bash

config=config/stt_zh
dir=exp/stt_zh

tokenizer_config=${config}/tokenizer.yaml
train_config=${config}/train.yaml
test_config=${config}/test.yaml
text=data/text/AISHELL-1_train.txt

mkdir -p $dir

cp $config/tokenizer.yaml $dir/tokenizer.yaml
cp $config/train.yaml $dir/train.yaml
cp $config/test.yaml $dir/test.yaml

stage=0

if [ $stage -le 1 ]; then
    echo "Training tokenizer from text ..."
    ops/tokenizer_train --config $dir/tokenizer.yaml \
        --input $text \
        --model $dir/tokenizer \
        2> $dir/log.tokenizer
fi

if [ $stage -le 2 ]; then
    echo "Traning stt model ..."
    ops/stt_train --node_rank 0 --config $dir/train.yaml $dir 2> $dir/log.train
fi

if [ $stage -le 3 ]; then
    echo "Averaging model checkpoints ..."
    ops/stt_average $dir/checkpoints $dir/final.model 2> $dir/log.average # default average last 20 checkpoints

    echo "Exporting torchscript model ..."
    ops/stt_export --config $dir/train.yaml $dir/final.model $dir/final.ts 2> $dir/log.export
fi

if [ $stage -le 4 ]; then
    echo "Decoding test set ..."
    ops/stt --config $dir/test.yaml $dir 1> $dir/test.txt 2> $dir/log.test
fi

if [ $stage -le 5 ]; then
    echo "Evaluating error rate ..."
    awk -F'\t' '{print $2, $3}' $dir/test.txt > $dir/rec.txt
    ops/stt_error_rate --tokenizer char \
        --ref $dir/ref.txt \
        --hyp $dir/rec.txt \
        $dir/RESULT 2> $dir/log.eval
fi
