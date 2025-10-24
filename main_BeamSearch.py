
import argparse

import tadashi
from tadashi import TrEnum
from tadashi.apps import Polybench







import random


def getAllPossible(app):
    scops = app.scops
    ret = []
    for si in range(len(scops[0].schedule_tree)):
        s = scops[0].schedule_tree[si]
        av = s.available_transformations
        ret.append( (si, av) )
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

    evals = []
    for _ in range(n_trials):
        try:
            evals.append(app.measure(timeout=timeout))
        except TimeoutExpired:
            # If the evaluations takes too long, it gets a bad fitness
            evals.append(timeout)

    # multiplied by -1 so fitness is meant to be maximized
    return -1 * min(evals) 


def beam_search(app_factory, timeout=99, beam_width=5, max_depth=6):

    # each beam element is (total_score, steps)
    beams = [(0, [])]

    test_eval = evaluateList(app_factory, [], timeout=timeout)


    assert False
    
    for depth in range(max_depth):
        candidates = []
        for score, path in beams:
            for action, delta in getNextOperation(path):
                new_path = path + [action]
                new_score = score + delta
                candidates.append((new_score, new_path))
        
        # sort candidates by descending score and keep only top beam_width
        if not candidates:
            break
        candidates.sort(key=lambda x: x[0], reverse=True)
        beams = candidates[:beam_width]
        
        print(f"Depth {depth+1}: top {len(beams)} paths")
        for s, p in beams:
            print(f"  score={s}, path={p}")
        print("-" * 40)

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

    best_score, best_path = beam_search(app_factory, timeout)
    print("\n Best found path:")
    print("Score:", best_score)
    print("Steps:", best_path)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=str, default="all")
    parser.add_argument("--dataset", type=str, default="LARGE")
    parser.add_argument("--oflag", type=int, default=3)
    parser.add_argument("--seed", type=int, default=47)
    parser.add_argument("--population-size", type=int, default=50)
    parser.add_argument("--max-gen", type=int, default=10)
    parser.add_argument("--n-trails", type=int, default=5)
    parser.add_argument("--n-threads", type=int, default=2)
    parser.add_argument("--use-heuristic", action=argparse.BooleanOptionalAction)
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




















