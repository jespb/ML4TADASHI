
import argparse

import tadashi
from tadashi import TrEnum
from tadashi.apps import Polybench

from util import *



class Heuristic:

    def __init__(self, args):
        print(f"Opening {args.benchmark}")
        dataset = f"-D{args.dataset}_DATASET"
        oflag = f"-O{args.oflag}"
        print(f"Using {dataset}")
        self.app_name = args.benchmark
        self.app_factory = Polybench(args.benchmark, compiler_options=[dataset, oflag])
        self.app_factory.compile()
        self.n_trials = args.n_trials
        self.allow_omp = args.allow_omp


    def fit(self):

        print("-----------------------------------------\n\n[STARTING NEW APP]")
        print(self.app_name)

        app = self.app_factory

        app.compile()

        bline = app.measure(repeat=self.n_trials)
        arrays_original = app.dump_arrays_and_time()["arrays"]

        print("Baseline measure: %f" % bline)

        full_tr_list = []

        tile_size = 32

        scops = app.scops

        trs = searchFor(app, "full_split")
        trs = [[index, TrEnum.FULL_SPLIT] for index in trs]
        trs = trs[::-1]
        for t in trs:
            scops[0].reset()
            scops[0].transform_list(full_tr_list)
            valid = scops[0].transform_list([t])
            if valid[-1]:
                full_tr_list.append(t)
            else:
                print("skipped tr:", str(t))
        scops[0].reset()
        valid = scops[0].transform_list(full_tr_list)
        print("FULL_SPLIT list validity:", valid)
        # full_tr_list.extend(trs[::-1])


        trs = searchFor(app, "tile3d")
        toRemoveFrom2D = [a for a in trs]
        toRemoveFrom2D.extend([a + 1 for a in trs])
        toRemoveFrom2D = list(set(toRemoveFrom2D))
        for t in trs:
            if t - 1 in trs:
                trs.pop(trs.index(t - 1))
        trs3D = [
            [index, TrEnum.TILE3D, tile_size, tile_size, tile_size] for index in trs[::-1]
        ]


        trs2 = searchFor(app, "tile2d")
        trs2D = [[index, TrEnum.TILE2D, tile_size, tile_size] for index in trs2[::-1]]
        trs3D.extend(trs2D)
        trs3D.sort()
        trs3D = trs3D[::-1]
        for t in trs3D:
            scops[0].reset()
            scops[0].transform_list(full_tr_list)
            valid = scops[0].transform_list([t])
            if valid[-1]:
                full_tr_list.append(t)
            else:
                print("skipped tr:", str(t))
        scops[0].reset()
        valid = scops[0].transform_list(full_tr_list)
        print("TILE 2D and 3D list validity:", valid)

        if self.allow_omp:
            print("Allowing parallel")
            trs = searchFor(app, "set_parallel")
            trs = [[index, TrEnum.SET_PARALLEL, 0] for index in trs]

            trs = trs[::-1]
            tmp = []
            for t in trs:
                tmp.append( [getDepth(app, t[0]), t] )
            tmp.sort()
            trs = [tmp[-1][1]]

            for t in trs:
                scops[0].reset()
                scops[0].transform_list(full_tr_list)
                valid = scops[0].transform_list([t])
                if valid[-1]:
                    full_tr_list.append(t)
                else:
                    print("skipped tr:", str(t))
            scops[0].reset()
            valid = scops[0].transform_list(full_tr_list)
            print("SET_PARALLEL list validity", valid) 

        print("transformation_list=[")
        [print("   %s," % str(t)) for t in full_tr_list]
        print("]")


        scops[0].reset()

        # EVALUATION

        print("Tiling with size %d ..." % tile_size)

        valid = scops[0].transform_list(full_tr_list)
        print("Is this transformation list valid:", valid)

        tapp = app.generate_code(alt_infix="_tiled%d" % tile_size, ephemeral=False)
        tapp.compile()

        arrays_transformed = tapp.dump_arrays_and_time()["arrays"]

        improved = tapp.measure(repeat=self.n_trials)
        print("Transformed app: %f" %  improved)
        print("Thats a %.2fx speedup!" % (bline/improved))

        print(arrays_original == arrays_transformed)

        print("[FINISHED APP]\n\n")

