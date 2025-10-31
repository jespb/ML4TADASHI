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

    def generateCode(self, app_factory):
        return transformAndCompile(app_factory, self.operation_list)


    def getFitness(
        self, app_factory=None, n_trials: int = None, timeout=9999, evaluations=None
    ):
        """
        app_factory and n_trials are not requires if the fitness is already calculated
        """
        if not evaluations is None and str(self.operation_list) in evaluations:
            self.fitness = evaluations[str(self.operation_list)]

        if self.fitness is None:
            self.fitness = evaluateList(app_factory, self.operation_list, n_trials, timeout)

        if not evaluations is None:
            evaluations[str(self.operation_list)] = self.fitness

        return self.fitness

    def isLegal(self, app_factory):
        return isTransformationListLegal(app_factory, self.operation_list)

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

    def mutate(self, app=None):
        #  5% not mutate
        #  5% lose last operation or not mutate
        # 90% of appending a new operation at the end
        mutationType = randint(0, 19)

        # No mutation
        if mutationType == 0:
            return self

        # Delete last node, if exists:
        if mutationType == 1:
            op_list = self.operation_list[:-1]
            ret = Individual(op_list)
            return ret

        # Appends a transformation to the end of the list
        if mutationType > 1:
            app.reset_scops()
            scops = app.scops[0]

            op_list = self.operation_list[:]
            
            scops.transform_list(op_list)

            st = scops.schedule_tree

            possible = getAllPossible(app, ignore=["set_parallel"])


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

                if isNextTransformationLegal(app, op):
                    op_list.append(op)
                    return Individual(op_list)

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
        self.population_size=args.population_size
        self.max_gen=args.max_gen
        self.n_trials=args.n_trials
        self.n_threads=args.n_threads
        self.use_heuristic=args.use_heuristic
        self.t_size = args.tournament_size
        self.population = []
        self.evaluations = {}

        print("USING TIME LIMIT:", self.timeout)

        #
        # <heuristic initialization>
        #
        if not self.use_heuristic:
            full_tr_list = []

            app = self.app_factory

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

            print("Transformations retrieved by Heuristic:")
            for i in range(1, len(full_tr_list)):
                op_list = full_tr_list[:1]
                print("  ", op_list)
                ind = Individual(op=op_list)
                legal = ind.isLegal(self.app_factory)
                self.population.append(Individual(op=full_tr_list[:i]))
        #
        # </heuristic initialization>
        #

        # The initial population is an individual without transformations
        # so the algorithm starts by searching for simpler solutions first
        self.population.append(Individual())


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
                        multiProcess_evaluation,
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
