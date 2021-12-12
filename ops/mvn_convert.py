import sys
from pysio.stt import *

mv_stats_file = 'exp/tmp/mean_var_stats.json'

mv_stats = MeanVarStats().load(mv_stats_file)
mvn = MeanVarNormalizer(mv_stats)

with open('ops/libsio/testdata/mean_var_norm.txt', 'w+') as f:
    f.write(f'[ {" ".join([ str(e) for e in mvn.mean_norm_shift.tolist() ])} ]\n')
    f.write(f'[ {" ".join([ str(e) for e in mvn.var_norm_scale.tolist() ])} ]\n')

