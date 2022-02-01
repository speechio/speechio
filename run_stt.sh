#!/usr/bin/env bash

text=data/text/AISHELL-1_train.txt
tokenizer=model/tokenizer/zh

config_dir=config/stt_zh
tokenizer_config=${config_dir}/tokenizer.yaml
train_config=${config_dir}/train.yaml
test_config=${config_dir}/test.yaml

dir=exp/stt_zh

mkdir -p $dir
stage=0

if [ $stage -le 1 ]; then
    echo "Training tokenizer from text ..."
    ops/tokenizer_train --config $tokenizer_config \
        --input $text \
        --model $tokenizer \
        2> $dir/log.tokenizer
fi

if [ $stage -le 2 ]; then
    echo "Traning stt model ..."
    ops/stt_train --node_rank 0 --config $train_config $dir 2> $dir/log.train
fi

if [ $stage -le 3 ]; then
    echo "Averaging model checkpoints ..."
    ops/stt_average $dir/checkpoints $dir/final.model # default average last 20 checkpoints

    echo "Exporting torchscript model ..."
    ops/stt_export --config $train_config $dir/final.model $dir/final.ts
fi

if [ $stage -le 4 ]; then
    echo "Decoding test set ..."
    ops/stt --config $test_config $dir 1> $dir/res.test 2> $dir/log.test
fi

if [ $stage -le 5 ]; then
    echo "Evaluating error rate ..."
    awk -F'\t' '{print $2, $3}' $dir/res.test > $dir/rec.txt
    ops/stt_error_rate --tokenizer char \
        --ref $dir/ref.txt \
        --hyp $dir/rec.txt \
        $dir/RESULT
fi
