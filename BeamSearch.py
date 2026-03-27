
import argparse
import time
import timeit
from pathlib import Path
from random import choice, randint, randrange, seed
from subprocess import CalledProcessError, TimeoutExpired

import multiprocess as mp
import tadashi
from tadashi import TrEnum
from tadashi.apps import Polybench, Simple


import random

from util import *

def getNextOperations(app, op_list, beam_width=3, max_depth=6):
    """
    Given a list of previous steps, returns a list of (action, delta_score) pairs.
    This is just an example — replace it with your own logic.
    """
    depth = len(op_list)
    if depth >= 6:  # stop expanding after some depth
        return []
    
    app.reset_scops()
    scop = app.scops[0]
    scop.transform_list(op_list)

    possible = getAllPossible(app, ignore=["set_parallel"])
    random.shuffle(possible)

    # get arguments for possible
    for i in range(len(possible)):
        x2 = possible[i][0]
        node = scop.schedule_tree[x2]
        tran = possible[i][1]
        args = random_args(node, tran)
        possible[i] = [x2, tran, *args]


    # check legality and fetch |beam_width| solution
    legalSteps = []
    for i in range(len(possible)):
        if isTransformationListLegal(app, op_list + [possible[i]] ):
            legalSteps.append(possible[i])
            if len(legalSteps) >= beam_width:
                return legalSteps

    return legalSteps



class BeamSearch:

    def __init__(self, args):
        seed(args.seed)
        print(f"Opening {args.benchmark}")
        dataset = f"-D{args.dataset}_DATASET"
        oflag = f"-O{args.oflag}"
        base=f"{args.base}"
        print(f"Using {dataset}")
        self.app_name = args.benchmark
        self.app_factory = Polybench(args.benchmark, base=base, compiler_options=[dataset, oflag])
        self.app_factory.compile()
        self.timeout = timeit.timeit(self.app_factory.measure, number=1) * 2

        self.n_trials = args.n_trials
        self.n_threads = args.n_threads
        self.beam_width = args.beam_width
        self.max_depth = args.max_depth


    def fit(self):
        app_factory = self.app_factory
        n_trials = self.n_trials
        timeout = self.timeout 
        beam_width = self.beam_width 
        max_depth = self.max_depth 
        n_threads = self.n_threads

        # each beam element is (total_score, steps)

        op_list = []
        baseline_time = evaluateList(app_factory, op_list, timeout=timeout, n_trials=n_trials)
        arrays_original = app_factory.dump_arrays()
        beams = [(baseline_time, op_list)]
        best = (baseline_time, op_list)

        for depth in range(max_depth):
            candidates = []
            new_paths = []
            for score, path in beams:
                for action in getNextOperations(app_factory, path, beam_width=beam_width):
                    new_path = path + [action]
                    new_paths.append(new_path)

            if n_threads == 1:
                for path in new_paths:
                    new_score = evaluateList(app_factory, path, timeout=timeout, n_trials=n_trials)
                    candidates.append((new_score, path))
            else:
                with mp.Pool(processes=n_threads) as pool:
                    results = pool.map(
                        multiProcess_evaluation,
                        [
                            (
                                generateAndCompile(app_factory, path),
                                n_trials,
                                timeout,
                                0 # previous score for EvoTADASHI, Ill add here later
                            )
                            for path in new_paths
                        ]
                    )
                    for i in range(len(new_paths)):
                        if results[i] != "E":
                            candidates.append((results[i], new_paths[i]))

            
            # sort candidates by descending score and keep only top beam_width
            if not candidates:
                break
            candidates.sort(key=lambda x: x[0], reverse=True)
            beams = candidates[:beam_width]

            if beams[0][0]<best[0]:
                best = beams[0]
            
            #print(f"Depth {depth+1}: top 1 path")
            for s, p in beams[:]:
                print("Depth: %2d, Score: %.6f, Speed up: %.4f, Path: %s" % (depth+1, s, baseline_time/s, str(p)) )
                isOutputMatching(arrays_original, app_factory, p)
            #print("-" * 40)

        # Return the best path found
        best_score, best_path = best

        isOutputMatching(arrays_original, app_factory, best_path)


        print("\nBest found path --", best_score,"--", best_path)
        return best_score, best_path
























