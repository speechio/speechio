## Tokenizer
# ops/train_tokenizer --config configs/train_tokenizer.yaml --input misc/text --model misc/tokenizer

# ops/tokenizer_encode --input misc/text --model misc/tokenizer --output_format id --output misc/encoded1
# cat misc/text | ops/tokenizer_encode --model misc/tokenizer > misc/encoded2

# ops/tokenizer_decode --model misc/tokenizer --input misc/encoded1 --input_format id > misc/decoded1
# cat misc/encoded2 | ops/tokenizer_decode --model misc/tokenizer > misc/decoded2

## Train
ops/train_sito --config configs/train_sito.yaml
