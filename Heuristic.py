
import argparse

import tadashi
from tadashi import TrEnum
from tadashi.apps import Polybench

apps_miniAMR = [
    "examples/evaluation/miniAMR/",
]

def getDepth_aux(node, depth=0):
    cl = node.children
    if len(cl) == 0:
        return depth
    else:
        return max( [getDepth_aux(c, depth+1) for c in cl] )

def getDepth(app, node_id):
    base_node = app.scops[0].schedule_tree[node_id]
    return getDepth_aux(base_node)


def searchFor(app, tr_name):
    scops = app.scops
    ret = []
    for si in range(len(scops[0].schedule_tree)):
        s = scops[0].schedule_tree[si]
        av = s.available_transformations
        for t in av:
            if t == tr_name:
                ret.append(si)
    return ret


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
        self.useOMP = args.allow_omp


    def fit(self):

        print("-----------------------------------------\n\n[STARTING NEW APP]")

        print(self.app_name)

        app = self.app_factory


        app.compile()

        bline = app.measure(repeat=self.n_trials)

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
        # for t in toRemoveFrom2D:
        # 	if t in trs2:
        # 		trs2.pop(trs2.index(t))
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
        # full_tr_list.extend(trs3D[::-1])


        if self.allow_omp:
            print("Allowing parallel")
            trs = searchFor(app, "set_parallel")
            trs = [[index, TrEnum.SET_PARALLEL, 0] for index in trs]
            #trs = [[trs[4], TrEnum.SET_PARALLEL, 0]]


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

        tiled = app.generate_code(alt_infix="_tiled%d" % tile_size, ephemeral=False)
        tiled.compile()

        improved = tiled.measure(repeat=self.n_trials)
        print("Tiling with size %d: %f" % (tile_size, improved))
        print("Thats a %.2fx speedup!" % (bline/improved))

        print("[FINISHED APP]\n\n")


