## Tokenizer memo
# ops/tokenizer_encode --input misc/text --model misc/tokenizer --output_format id --output misc/encoded1
# cat misc/text | ops/tokenizer_encode --model misc/tokenizer > misc/encoded2

# ops/tokenizer_decode --model misc/tokenizer --input misc/encoded1 --input_format id > misc/decoded1
# cat misc/encoded2 | ops/tokenizer_decode --model misc/tokenizer > misc/decoded2

#-------------------- RECIPE --------------------#
tokenizer_text=data/text/AISHELL-1_trn.txt
tokenizer_model=model/tokenizer/AISHELL-1
tokenizer_config=config/tokenizer_zh.yaml

trn_config=config/stt_train_zh.yaml
tst_config=config/stt_test_zh.yaml

dir=exp/AISHELL-1

mkdir -p $dir
stage=0

# Train tokenizer from text
if [ $stage -le 1 ]; then
    ops/tokenizer_train --config $tokenizer_config \
        --input $tokenizer_text \
        --model $tokenizer_model \
        2> $dir/log.tokenizer
fi

# Train stt model
if [ $stage -le 2 ]; then
    ops/stt_train --node_rank 0 --config $trn_config $dir 2> $dir/log.train
fi

# Average model checkpoints & export as runtime resource
if [ $tage -le 3 ]; then
    ops/stt_average $dir/checkpoints $dir/final.model # default average last 20 checkpoints
    ops/stt_export --config $trn_config $dir/final.model $dir/final.pt
fi

# Decode on test set
if [ $stage -le 4 ]; then
    ops/stt --config $tst_config $dir 1> $dir/res.test 2> $dir/log.test
fi

# Evaluate error rate
if [ $stage -le 5 ]; then
    awk -F'\t' '{print $2, $3}' $dir/res.test > $dir/rec.txt
    ops/stt_error_rate --tokenizer char \
        --ref $dir/ref.txt \
        --hyp $dir/rec.txt \
        $dir/RESULT
fi
