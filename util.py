
from random import choice
from tadashi import TrEnum


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


def getDepth_aux(node, depth=0):
    cl = node.children
    if len(cl) == 0:
        return depth
    else:
        return max( [getDepth_aux(c, depth+1) for c in cl] )

def getDepth(app, node_id):
    base_node = app.scops[0].schedule_tree[node_id]
    return getDepth_aux(base_node)



def isTransformationListLegal(app_factory, tr_list):
    app = app_factory.generate_code(populate_scops=True)
    scop = app.scops[0]
    valid = -1
    try:
        valid = scop.transform_list(tr_list)
        tapp = app.generate_code()
        tapp.compile()
        # At least one operation is not valid
        return sum([0 if v else 1 for v in valid]) == 0
    except ValueError:
        assert False
        return False
    except:
        assert False
        # If it cant transform, its not valid
        return False


def isNextTransformationLegal(app, nextStep):
    scop = app.scops[0]
    valid = -1
    try:
        valid = scop.transform_list([nextStep])
        tapp = app.generate_code()
        tapp.compile()
        scop.schedule_tree[nextStep[0]].rollback()
        # At least one operation is not valid
        return sum([0 if v else 1 for v in valid]) == 0
    except ValueError:
        assert False
        return False
    except:
        assert False
        if valid != -1:
            scop.schedule_tree[nextStep[0]].rollback()
        # If it cant transform, its not valid
        return False

def generateAndCompile(app, op_list):
    app = app.generate_code(populate_scops=True)
    app.reset_scops()
    scop = app.scops[0]
    valid = -1
    try:
        valid = scop.transform_list(op_list)
        tapp = app.generate_code()
        tapp.compile()
        # At least one operation is not valid
        return tapp
    except ValueError:
        assert False
        return False
    except:
        assert False
        return False


def transformAndCompile(app_factory, op_list):
    app = app_factory.generate_code(populate_scops=True)
    app.reset_scops()
    scops = app.scops[0]
    valid = scops.transform_list(op_list)
    tapp = app.generate_code()
    tapp.compile()
    return tapp


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


def isOutputMatching(instr, app_factory, op_list):
    app = app_factory.generate_code(populate_scops=True)
    scops = app.scops
    scops[0].reset()
    valid = scops[0].transform_list(op_list)
    tapp = app.generate_code()
    arrays_transformed = tapp.dump_arrays_and_time()["arrays"]
    if instr == arrays_transformed:
        print("The output matches the original")
    else:
        print("The output does not match the original")

def evaluateList(app_factory, op_list, n_trials=2, timeout = 99):
    app = app_factory.generate_code(populate_scops=True)
    scop = app.scops[0]
    scop.transform_list(op_list)
    app.compile()
    return evaluate(app, n_trials, timeout)



def multiProcess_evaluation(a):
    app, n_trials, timeout, pre_evaluated = a
    
    if not app:
        return "E"

    return evaluate(app, n_trials, timeout)