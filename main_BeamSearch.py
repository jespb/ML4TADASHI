
import argparse
import time
import timeit
from pathlib import Path
from random import choice, randint, randrange, seed
from subprocess import CalledProcessError, TimeoutExpired

import multiprocess as mp
import tadashi
from tadashi import TRANSFORMATIONS, LowerUpperBound, Scops, TrEnum
from tadashi.apps import Polybench, Simple


import random

def random_args(node, tr):
    """
    Get random arguments for the transformation
    Tiling is done using a number from [8, 16, 32, 64]
    Other transformation use a random number from -64 to 64
    """
    tiles = [TrEnum.TILE1D, TrEnum.TILE2D, TrEnum.TILE3D]
    if tr in tiles:
        tile_size = choice([2**x for x in range(3, 7)])
        return [tile_size] * (1 + tiles.index(tr))
    return choice(node.get_args(tr, start=-64, end=64))

def getAllPossible(app):
    scops = app.scops
    tmp = []
    for si in range(len(scops[0].schedule_tree)):
        s = scops[0].schedule_tree[si]
        av = s.available_transformations
        tmp.append( (si, av) )

    ret = []
    for x2, trans in tmp:
        for tran in trans:
            ret.append([x2, tran])

    return ret


def isLegal(app, nextStep):
    scop = app.scops[0]
    valid = -1
    try:
        valid = scop.transform_list([nextStep])
        tapp = app.generate_code()
        tapp.compile()
        scop.schedule_tree[nextStep[0]].rollback()
        # At least one operation is not valid
        return sum([0 if v else 1 for v in valid]) == 0
    except:
        if valid != -1:
            scop.schedule_tree[nextStep[0]].rollback()
        # If it cant transform, its not valid
        return False


def getNextOperations(app_factory, op_list, beam_width=3, max_depth=6):
    """
    Given a list of previous steps, returns a list of (action, delta_score) pairs.
    This is just an example — replace it with your own logic.
    """
    depth = len(op_list)
    if depth >= 6:  # stop expanding after some depth
        return []
    
    app = app_factory.generate_code(populate_scops=True)
    scop = app.scops[0]
    scop.transform_list(op_list)

    possible = getAllPossible(app)
    random.shuffle(possible)

    # get arguments for possible
    for i in range(len(possible)):
        x2 = possible[i][0]
        node = scop.schedule_tree[x2]
        tran = possible[i][1]
        args = random_args(node, tran)
        possible[i] = [x2, tran, *args]

    possible = [
        p for p in possible if not ("parallel" in p[1] )
    ]

    # check legality and fetch |beam_width| solution
    legalSteps = []
    for i in range(len(possible)):
        if isLegal(app, possible[i]):
            legalSteps.append(possible[i])
            if len(legalSteps) >= beam_width:
                return legalSteps

    return legalSteps


def evaluateList(app_factory, op_list, n_trials=2, timeout = 99):
    app = app_factory.generate_code(populate_scops=True)
    scop = app.scops[0]
    scop.transform_list(op_list)
    app.compile()

    evals = []
    for _ in range(n_trials):
        try:
            evals.append(app.measure(timeout=timeout))
        except TimeoutExpired:
            # If the evaluations takes too long, it gets a bad fitness
            evals.append(timeout)

    # multiplied by -1 so fitness is meant to be maximized
    return -1 * min(evals) 


def beam_search(app_factory, n_trials=2, timeout=99, beam_width=5, max_depth=6):

    # each beam element is (total_score, steps)

    op_list = []
    baseline_time = evaluateList(app_factory, op_list, timeout=timeout, n_trials=n_trials)
    beams = [(baseline_time, op_list)]

    for depth in range(max_depth):
        candidates = []
        for score, path in beams:
            for action in getNextOperations(app_factory, path):
                new_path = path + [action]
                new_score = evaluateList(app_factory, new_path, timeout=timeout, n_trials=n_trials)
                candidates.append((new_score, new_path))
        
        # sort candidates by descending score and keep only top beam_width
        if not candidates:
            break
        candidates.sort(key=lambda x: x[0], reverse=True)
        beams = candidates[:beam_width]
        
        #print(f"Depth {depth+1}: top 1 path")
        for s, p in beams[:1]:
            print(f"Depth {depth+1}: score={s}, path={p}, speedup={baseline_time/s}")
        #print("-" * 40)

    # Return the best path found
    best_score, best_path = max(beams, key=lambda x: x[0])
    return best_score, best_path






def main(args):
    seed(args.seed)
    print(f"Opening {args.benchmark}")
    dataset = f"-D{args.dataset}_DATASET"
    oflag = f"-O{args.oflag}"
    print(f"Using {dataset}")
    app_factory = Polybench(args.benchmark, compiler_options=[dataset, oflag])
    app_factory.compile()
    timeout = timeit.timeit(app_factory.measure, number=1) * 2

    best_score, best_path = beam_search(app_factory, timeout=timeout, n_trials = args.n_trials)
    print("\nBest found path --", best_score,"--", best_path)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=str, default="jacobi-1d")
    parser.add_argument("--dataset", type=str, default="LARGE")
    parser.add_argument("--oflag", type=int, default=3)
    parser.add_argument("--seed", type=int, default=47)
    parser.add_argument("--n-trials", type=int, default=2)
    args = parser.parse_args()

    if args.benchmark == "all":
        pb = [
            "jacobi-1d",
            "bicg",
            "atax",
            "gesummv",
            "trisolv",
            "durbin",
            "mvt",
            "gemver",
            "deriche",
            "doitgen",
            "gemm",
            "syrk",
            "2mm",
            "trmm",
            "symm",
            "jacobi-2d",
            "fdtd-2d",
            "cholesky",
            "syr2k",
            "3mm",
            "correlation",
            "covariance",
            "heat-3d",
            "gramschmidt",
            "ludcmp",
            "lu",
            "nussinov",
            "adi",
            "floyd-warshall",
            "seidel-2d",
        ]
        pb = pb[:]
        for benchmark in pb:
            print("\n\n\n")
            args.benchmark = benchmark
            print(str(args) + "\n")
            main(args)
    else:
        print(str(args) + "\n")
        main(args)




















