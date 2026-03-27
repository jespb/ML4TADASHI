
from random import choice
from tadashi import TrEnum
from subprocess import CalledProcessError, TimeoutExpired

def random_args(node, tr):
    """
    Get random arguments for the transformation
    Tiling is done using a number from [8, 16, 32, 64]
    Other transformation use a random number from -64 to 64
    """
    tiles = [TrEnum.TILE_1D, TrEnum.TILE_2D, TrEnum.TILE_3D]
    if tr in tiles:
        tile_size = choice([2**x for x in range(3, 7)])
        return [tile_size] * (1 + tiles.index(tr))
    return choice(node.get_args(tr, start=-64, end=64))

def getAllPossible(app, ignore=[]):
    scops = app.scops
    tmp = []
    for si in range(len(scops)):
        for sti in range(len(scops[si].schedule_tree)):
            s = scops[si].schedule_tree[sti]
            av = s.available_transformations
            tmp.append( (si, sti, av) )

    ret = []
    for x1, x2, trans in tmp:
        for tran in trans:
            if not tran in ignore:
                ret.append([x1, x2, tran])
    return ret


def searchFor(app, tr_name):
    assert False
    scops = app.scops
    ret = []
    for si in range(len(scops[0].schedule_tree)):
        s = scops[0].schedule_tree[si]
        av = s.available_transformations
        for t in av:
            if t == tr_name:
                ret.append(si)
    return ret


def getDepth_aux(node, depth=0):
    cl = node.children
    if len(cl) == 0:
        return depth
    else:
        return max( [getDepth_aux(c, depth+1) for c in cl] )

def getDepth(app, scop_id, node_id):
    base_node = app.scops[scop_id].schedule_tree[node_id]
    return getDepth_aux(base_node)

def isTransformationListLegal(app, tr_list):
    app.reset_scops()
    try:
        app.transform_list(tr_list)
        return app.legal
    except:
        print("Failed to verify legality:", tr_list)
        return False
        
def isNextTransformationLegal(app, tr):
    try:
        app.transform_list(tr)
        return app.legal
    except:
        print("Failed to verify legality:", tr_list)
        return False



def transformAndCompile(app, op_list):
    app.reset_scops()
    app.transform_list(op_list)
    tapp = app.generate_code()
    tapp.compile()
    return tapp





def isOutputMatching(instr, app, op_list):
    app.reset_scops()
    app.transform_list(op_list)
    tapp = app_factory.generate_code()
    arrays_transformed = tapp.dump_arrays()
    if instr == arrays_transformed:
        print("The output matches the original")
    else:
        print("The output does not match the original")


def evaluateList(app, op_list, n_trials=2, timeout = 99):
    app.reset_scops()
    app.transform_list(op_list)
    tapp = app.generate_code()
    return evaluate(tapp, n_trials, timeout)

def evaluate(app, n_trials, timeout):
    evals = []
    for _ in range(n_trials):
        try:
            evals.append(app.measure(timeout=timeout))
        except TimeoutExpired:
            # If the evaluations takes too long, it gets a bad fitness
            evals.append(timeout)

    # multiplied by -1 so fitness is meant to be maximized
    return -1 * min(evals) 


def multiProcess_evaluation(a):
    app, n_trials, timeout, pre_evaluated = a
    
    if not app:
        return "E"

    return evaluate(app, n_trials, timeout)





from mpi4py.futures import MPIPoolExecutor, as_completed
from tadashi import TrEnum
from tadashi.apps import Polybench
from tadashi.translators import Polly
import socket

def app_from_kwargs(kwargs):
    kwargs["translator"] = Polly()
    return Polybench(**kwargs)

def remote_measure(kwargs, trs):
    print(f"{trs=}")
    hostname = socket.gethostname()
    print(f"{hostname=}")
    app = app_from_kwargs(kwargs)
    app.transform_list(trs)
    tapp = app.generate_code(alt_infix=f"_evot_{hostname}", ephemeral=False)
    tapp.compile()
    rv = tapp.measure()
    return rv, hostname
