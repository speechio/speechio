import sys
from pysio.stt import *

mv_stats_file = 'exp/tmp/mean_var_stats.json'
mv_norm_file = 'ops/libsio/testdata/mean_var_norm.txt'

mv_stats = MeanVarStats().load(mv_stats_file)

mv_norm = MeanVarNormalizer(mv_stats).dump(mv_norm_file)



