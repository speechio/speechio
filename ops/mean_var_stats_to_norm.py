import os, argparse
from pysio.stt import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("mean_var_stats_file", type=str, help = "input")
    parser.add_argument("mean_var_norm_file", type=str, help = "output")
    args = parser.parse_args()

    assert(os.path.isfile(args.mean_var_stats_file))

    mv_norm = MeanVarStats().load(args.mean_var_stats_file).dump_mean_var_norm(args.mean_var_norm_file)
