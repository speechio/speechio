## Tokenizer
#ops/tokenizer_train --config config/tokenizer_zh.yaml --input data/text/AISHELL-1_trn.txt --model model/tokenizer/AISHELL-1
#ops/tokenizer_train --config config/tokenizer_en.yaml --input data/text/GigaSpeech_S.txt --model model/tokenizer/GigaSpeech_S

# ops/tokenizer_encode --input misc/text --model misc/tokenizer --output_format id --output misc/encoded1
# cat misc/text | ops/tokenizer_encode --model misc/tokenizer > misc/encoded2

# ops/tokenizer_decode --model misc/tokenizer --input misc/encoded1 --input_format id > misc/decoded1
# cat misc/encoded2 | ops/tokenizer_decode --model misc/tokenizer > misc/decoded2

## Train
dir=exp/ddp && mkdir -p $dir
ops/stt_train --node_rank 0 --config config/train_stt_zh.yaml $dir
#ops/stt_test --config config/stt_test_zh.yaml $dir
