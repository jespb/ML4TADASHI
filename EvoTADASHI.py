#!/usr/bin/env python

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

from util import *



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


def multiProcess_fitnessEval(a):
    """
    EvoTADASHI Model evaluation using multiprocessing
    app: app
    trials: number of trials
    timeout: timeout for each trial
    pre_evaluated: dictionary with previous models fitnesses (if the model is present, evaluation is skipped)
    """
    app, trials, timeout, pre_evaluated = a

    if pre_evaluated != 0:
        return pre_evaluated

    evals = []
    for _ in range(trials):
        try:
            evals.append(app.measure(timeout=timeout))
        except TimeoutExpired:
            # If the evaluations takes too long, it gets a bad fitness
            evals.append(timeout)

    # multiplied by -1 so fitness is meant to be maximized
    return -1 * min(evals)


class Individual:
    operation_list: list = None
    fitness: float = None
    broken = False

    def __init__(self, op: list = []):
        self.operation_list = op

    def __str__(self):
        f = "%.8f" % self.fitness if not self.fitness is None else "Not evaluated"
        tmp = "["
        for op in self.operation_list:
            tmp += "[%s, %s, %s], " % (
                str(op[0]),
                "tadashi.TrEnum." + op[1].name,
                ", ".join(str(x) for x in op[2:]),
            )
        tmp += "]"
        return "%s --- %s" % (tmp, f)

    def __gt__(self, other):
        """
        You must calculate everyones fitness before sorting
        """
        return self.getFitness() > other.getFitness()

    def generateCode(self, app_factory, evaluations={}):
        try:
            valid = "not checked for validity"
            app = app_factory.generate_code(populate_scops=True)
            app.reset_scops()
            scops = app.scops[0]
            valid = scops.transform_list(self.operation_list)
            tapp = app.generate_code()
            tapp.compile()
            return tapp
        except:
            print("[ERROR GENERATING CODE] -- %s -- %s " % (str(valid), str(self)))
            evaluations[str(self)] = -9999
            self.broken = True
            #assert False
            return app_factory

    def getFitness(
        self, app_factory=None, n_trials: int = None, timeout=9999, evaluations=None
    ):
        """
        app_factory and n_trials are not requires if the fitness is already calculated
        """
        if not evaluations is None and str(self.operation_list) in evaluations:
            self.fitness = evaluations[str(self.operation_list)]

        if self.fitness is None:
            app = self.generateCode(app_factory)
            evals = []
            for _ in range(n_trials):
                try:
                    evals.append(app.measure(timeout=timeout))
                except TimeoutExpired:
                    # If the evaluations takes too long, it gets a bad fitness
                    evals.append(timeout)

            # multiplied by -1 so fitness is meant to be maximized
            self.fitness = -1 * min(evals)

        if not evaluations is None:
            evaluations[str(self.operation_list)] = self.fitness

        return self.fitness

    def isLegal(self, app_factory=None):
        app = app_factory.generate_code(populate_scops=True)
        app.reset_scops()
        scops = app.scops[0]
        try:
            valid = scops.transform_list(self.operation_list)
            tapp = app.generate_code()
            tapp.compile()
            # At least one operation is not valid
            return sum([0 if v else 1 for v in valid]) == 0
        except:
            # If it cant transform, its not valid
            return False

    def crossover(self, other, app_factory=None):
        # 20% chance to crossover, 0% if either parents have length 0
        if (
            randint(0, 9) < 2
            and len(self.operation_list) * len(other.operation_list) > 0
        ):
            p1 = self.operation_list
            p2 = other.operation_list

            xop1 = randint(0, len(p1) - 1)
            xop2 = randint(0, len(p2) - 1)

            o1 = p1[:xop1] + p2[:xop2]
            o2 = p2[:xop2] + p1[:xop1]

            i1 = Individual(o1)
            i2 = Individual(o2)

            ret = []
            for i in [i1, i2]:
                if i.isLegal(app_factory):
                    ret.append(i)

            return ret

        else:
            return [self, other]

    def mutate(self, app_factory=None):
        # 10% not mutate
        # 10% lose last operation or not mutate
        # 80% of appending a new operation at the end
        mutationType = randint(0, 19)

        # No mutation
        if mutationType == 0:
            return self

        # Delete last node, if exists:
        if mutationType == 1:
            op_list = self.operation_list[:-1]
            ret = Individual(op_list)
            return ret if ret.isLegal(app_factory) else self

        # Appends a transformation to the end of the list
        if mutationType > 1:
            app = app_factory.generate_code(populate_scops=True)
            app.reset_scops()
            scops = app.scops[0]

            op_list = self.operation_list[:]
            
            scops.transform_list(op_list)

            st = scops.schedule_tree

            possible = []
            for x2 in range(len(st)):
                node = st[x2]
                possible.extend([(x2, p) for p in node.available_transformations])

            possible = [
                p for p in possible if not ("parallel" in p[1] or "shift" in p[1])
            ]

            at = 0
            found = False
            max_attempts = 10
            while not found and at <= max_attempts and len(possible) > 0:
                at += 1

                x2, tran = possible.pop(randint(0, len(possible) - 1))
                node = st[x2]
                args = random_args(node, tran)

                op = [x2, tran, *args]
                # print("IN MUT", op)

                valid = st[x2].transform(tran, *args)
                if valid:
                    op_list.append(op)
                    return Individual(op_list)
                else:
                    st[x2].rollback()

            print(
                "Mutation failed (attempts: %d, remaining possibilities: %d)"
                % (at, len(possible))
            )
            return self


class EvoTADASHI:
    population = None
    max_gen = None
    best_individual = None
    n_trials = None
    app = None
    t_size = None
    n_threads = None
    evaluations = None

    def __init__(self, args):
        seed(args.seed)
        print(f"Opening {args.benchmark}")
        dataset = f"-D{args.dataset}_DATASET"
        oflag = f"-O{args.oflag}"
        print(f"Using {dataset}")
        self.app_factory = Polybench(args.benchmark, compiler_options=[dataset, oflag])
        self.app_factory.compile()
        self.timeout = timeit.timeit(self.app_factory.measure, number=1) * 2

        print("USING TIME LIMIT:", self.timeout)

        self.population_size=args.population_size
        self.max_gen=args.max_gen
        self.n_trials=args.n_trials
        self.n_threads=args.n_threads
        self.use_heuristic=args.use_heuristic
        self.t_size = args.tournament_size
        self.population = []
        self.evaluations = {}


        # The initial population is an individual without transformations
        # so the algorithm starts by searching for simpler solutions first

        #
        # <heuristic initialization>
        #

        app = self.app_factory

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
        scops[0].reset()
        valid = scops[0].transform_list(full_tr_list)

        trs = searchFor(app, "tile3d")
        toRemoveFrom2D = [a for a in trs]
        toRemoveFrom2D.extend([a + 1 for a in trs])
        toRemoveFrom2D = list(set(toRemoveFrom2D))
        for t in trs:
            if t - 1 in trs:
                trs.pop(trs.index(t - 1))
        trs3D = [
            [index, TrEnum.TILE3D, tile_size, tile_size, tile_size]
            for index in trs[::-1]
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
        scops[0].reset()

        #
        # </heuristic initialization>
        #

        self.population.append(Individual())

        if not self.use_heuristic:
            full_tr_list = []
        print(full_tr_list)

        for i in range(1, len(full_tr_list)):
            ind = Individual(op=full_tr_list[:1])
            legal = ind.isLegal(self.app_factory)
            self.population.append(Individual(op=full_tr_list[:i]))




    def tournament(self):
        """
        Requires: sorted population
        """
        return self.population[
            min([randint(0, len(self.population) - 1) for _ in range(self.t_size)])
        ]

    def fit(self):

        self.best_individual = self.population[0]
        self.best_individual.getFitness(
            self.app_factory, self.n_trials, evaluations=self.evaluations
        )
        print(
            "Measure without transformations:",
            self.best_individual.getFitness(
                self.app_factory, self.n_trials, evaluations=self.evaluations
            ),
        )

        for gen in range(self.max_gen):
            print("Gen %d" % gen)

            start_time = time.time()
            if self.n_threads > 1:
                with mp.Pool(processes=self.n_threads) as pool:
                    results = pool.map(
                        multiProcess_fitnessEval,
                        [
                            (
                                ind.generateCode(
                                    self.app_factory, self.evaluations
                                ),  # sending evals as a tmp fix
                                self.n_trials,
                                self.timeout,
                                (
                                    self.evaluations[str(ind.operation_list)]
                                    if str(ind.operation_list) in self.evaluations
                                    else 0
                                ),
                            )
                            for ind in self.population
                        ],
                    )
                    for i in range(len(self.population)):
                        self.population[i].fitness = results[i]
                        self.evaluations[str(self.population[i].operation_list)] = (
                            results[i]
                        )
            else:
                [
                    i.getFitness(
                        self.app_factory,
                        self.n_trials,
                        timeout=self.timeout,
                        evaluations=self.evaluations,
                    )
                    for i in self.population
                ]

            self.population.sort(reverse=True)

            self.population = [p for p in self.population if not p.broken]

            end_time = time.time()
            print("Evaluation time:", end_time - start_time)

            print("  Fitness values obtained:")
            [print("   ", i.fitness, i) for i in self.population[:3]]

            if self.population[0] > self.best_individual:
                self.best_individual = self.population[0]
                print("  Updating best_individual to", self.best_individual)

            # print("  Breeding phase")
            start_time = time.time()
            new_pop = []
            while len(new_pop) < self.population_size:
                # print("Breeding %d"%len(new_pop))
                ind1 = self.tournament()
                ind2 = self.tournament()
                # print("	MUT")
                ind1 = ind1.mutate(self.app_factory)
                ind2 = ind2.mutate(self.app_factory)
                # print("	XO")
                if False:
                    ret = ind1.crossover(ind2, self.app_factory)
                else:
                    ret = [ind1, ind2] # no crossover
                new_pop.extend(ret)
            new_pop = new_pop[: self.population_size]
            self.population = new_pop
            end_time = time.time()
            print("Breeding time:", end_time - start_time)

            be = self.evaluations[str(self.best_individual.operation_list)]
            print(
                "  Fitness on generation %d: %.8f (%.3fx speedup)"
                % (gen, be, self.evaluations["[]"] / be)
            )

        print("Final model:", self.best_individual)

        #
        # < use parellel in the final model >
        #

        try:
            full_tr_list = self.best_individual.operation_list

            app = self.app_factory
            app.reset_scops()
            scops = app.scops
            valid = scops[0].transform_list(full_tr_list)

            trs = searchFor(app, "set_parallel")
            trs = [[index, TrEnum.SET_PARALLEL, 0] for index in trs]

            trs = trs[::-1]
            tmp = []
            for t in trs:
                tmp.append([getDepth(app, t[0]), t])
            tmp.sort()
            trs = [tmp[-1][1]]

            for t in trs:
                scops[0].reset()
                scops[0].transform_list(full_tr_list)
                valid = scops[0].transform_list([t])
                if valid[-1]:
                    full_tr_list.append(t)
            scops[0].reset()
            valid = scops[0].transform_list(full_tr_list)
            print(valid)

            tiled = app.generate_code()
            tiled.compile()

            improved = tiled.measure()
            print(
                "Time with parallel: %f (%.3fx speedup)"
                % (improved, self.evaluations["[]"] / improved)
            )

            print("FINAL transformation_list=[")
            [print("   %s," % str(t)) for t in full_tr_list]
            print("]")
        except ValueError:
            print("[ERROR TRYING TO PARALLEL]", self.best_individual)

        #
        # </ use parellel in the final model >
        #


def main(args):
    seed(args.seed)
    print(f"Opening {args.benchmark}")
    dataset = f"-D{args.dataset}_DATASET"
    oflag = f"-O{args.oflag}"
    print(f"Using {dataset}")
    app_factory = Polybench(args.benchmark, compiler_options=[dataset, oflag])
    app_factory.compile()
    timeout = timeit.timeit(app_factory.measure, number=1) * 2

    print("USING TIME LIMIT:", timeout)
    m = EvoTADASHI(
        app_factory,
        population_size=args.population_size,
        max_gen=args.max_gen,
        n_trials=args.n_trails,
        n_threads=args.n_threads,
        use_heuristic=args.use_heuristic,
        timeout=timeout,
    )
    m.fit()
