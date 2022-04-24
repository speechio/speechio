# SpeechIO Operations
It's all about organizing your speech data, really.

## Dataset
A dataset is represented with a single table: `metadata.tsv`:
* compact
* human-readable
* easy to parse, merge, split, modify etc

| ID | AUDIO | BEGIN | DURATION | TEXT | SPEAKER |
|-|-|-|-|-|-|
| AUD001 | data/audio/MINI/AUD001.wav | 0.3 | 1.5 | HELLO WORLD | SPK001 |
| AUD002 | data/audio/MINI/AUD002.wav | 0.5 | 2.1 | HEY SIRI | SPK001 |
| ... | ... | ... | ... | ... | ... |

notes on table columns:
| Field | Type | Description | Optional | Default |
|-|-|-|-|-|
| ID | string | A unique identifier for the utterance | &check; | audio file name |
| AUDIO | string | Audio path containing the utterance | &cross; | |
| BEGIN | float | Utterance beginning inside audio file (in sec) | &check; | 0.0 |
| DURATION | float | Utterance duration (in sec) | &check; | length of the audio |
| TEXT | string | Utterance transcription | &check; | "" |
| SPEAKER | string | Unique identifier of the utterance speaker | &check; | "" |

### More examples

An unlabeled dataset, consisting of a list of audio files.
| AUDIO |
| - |
| data/audio/MINI/AUD001.wav |
| data/audio/MINI/AUD002.wav |
| ... |

Same as above, except explicitly specified utterance IDs
| ID | AUDIO |
| - | - |
| AUD001 | data/audio/MINI/AUD001.wav |
| AUD002 | data/audio/MINI/AUD002.wav |
| ... | ... |

A short-form dataset that can be used in ASR training
| ID | AUDIO | TEXT |
| - | - | - |
| AUD001 | data/audio/MINI/AUD001.wav | HEY THERE |
| AUD002 | data/audio/MINI/AUD002.wav | HOW ARE YOU |
| ... | ... |

A long-form dataset for speech-to-text tasks
| ID | AUDIO | BEGIN | END | TEXT |
| - | - | - | - | - |
| AUD001_SEG0001 | data/audio/MINI/AUD001.wav | 0.5 | 1.3 | HEY THERE |
| AUD001_SEG0002 | data/audio/MINI/AUD001.wav | 1.3 | 2.5 | HOW ARE YOU |
| ... | ... | ... | ... | ... |
| AUD123_SEG456 | data/audio/MINI/AUD123.wav | 1234.5 | 1235.0 | BLA BLA BLA |

A minimal short-form dataset for speaker related tasks
| ID | AUDIO | SPEAKER |
| - | - | - |
| AUD001 | data/audio/MINI/AUD001.wav | SPK001 |
| AUD002 | data/audio/MINI/AUD002.wav | SPK002 |
| ... | ... | ... |
