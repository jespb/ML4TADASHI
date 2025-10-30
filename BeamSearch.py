
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

from util import *

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



class BeamSearch:

    def __init__(self, args):
        seed(args.seed)
        print(f"Opening {args.benchmark}")
        dataset = f"-D{args.dataset}_DATASET"
        oflag = f"-O{args.oflag}"
        print(f"Using {dataset}")
        self.app_factory = Polybench(args.benchmark, compiler_options=[dataset, oflag])
        app_factory.compile()
        self.timeout = timeit.timeit(app_factory.measure, number=1) * 2

        self.timeout = timeout
        self.n_trials = args.n_trials
        self.n_threads = args.n_threads
        self.beam_width = 50
        self.max_depth = 10


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
        beams = [(baseline_time, op_list)]

        for depth in range(max_depth):
            candidates = []
            new_paths = []
            for score, path in beams:
                for action in getNextOperations(app_factory, path):
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
            
            #print(f"Depth {depth+1}: top 1 path")
            for s, p in beams[:3]:
                print(f"Depth {depth+1}: score={s}, path={p}, speedup={baseline_time/s}")
            #print("-" * 40)

        # Return the best path found
        best_score, best_path = max(beams, key=lambda x: x[0])

        print("\nBest found path --", best_score,"--", best_path)
        return best_score, best_path
























