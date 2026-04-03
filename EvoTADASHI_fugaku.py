#!/usr/bin/env python

import argparse
import time
import timeit
from pathlib import Path
from random import choice, randint, randrange, seed
from subprocess import CalledProcessError, TimeoutExpired

#import multiprocess as mp
import tadashi
from tadashi import TrEnum
from tadashi.apps import Polybench, Simple
from tadashi.translators import Polly

from util import *


class Individual:
    operation_list: list = None
    fitness: float = None

    def __init__(self, op: list = []):
        self.operation_list = op

    def __str__(self):
        f = "%.8f" % self.fitness if not self.fitness is None else "Not evaluated"
        tmp = "["
        for op in self.operation_list:
            tmp += "[%s, %s, %s, %s], " % (
                str(op[0]), str(op[1]),
                "tadashi.TrEnum." + op[2].name,
                ", ".join(str(x) for x in op[3:]),
            )
        tmp += "]"
        return "%s --- %s" % (tmp, f)

    def __gt__(self, other):
        """
        You must calculate everyones fitness before sorting
        """
        return self.getFitness() > other.getFitness()

    def getFitness(
        self, app=None, n_trials: int = None, timeout=9999, evaluations=None
    ):
        """
        app: your app
        n_trials: how many times your are running the app during evaluation
        timeout: how many seconds are you allowed to run the app
        evaluatation: a dictionary of transformations lists and previous measures, to avoid evaluating to identical solutions
        ---
        app and n_trials are not requires if the fitness is already calculated (e.g., for sorting)
        """

        # The dictionary is provided and the solution is in it
        if not evaluations is None and str(self.operation_list) in evaluations:
            self.fitness = evaluations[str(self.operation_list)]

        if self.fitness is None:
            self.fitness = evaluateList(app, self.operation_list, n_trials, timeout)

        # Update dictionary
        if not evaluations is None:
            evaluations[str(self.operation_list)] = self.fitness

        return self.fitness

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

            op_list = self.operation_list[:]       
            app.transform_list(op_list)

            possible = getAllPossible(app, ignore=["set_parallel", "scale"])

            at = 0
            found = False
            max_attempts = 10
            while not found and at <= max_attempts and len(possible) > 0:
                at += 1

                x1, x2, tran = possible.pop(randint(0, len(possible) - 1))
                node = app.scops[x1].schedule_tree[x2] # here (check below)
                args = random_args(node, tran)

                op = [x1, x2, tran, *args]
                #print("IN MUT", op)

                if isNextTransformationLegal(app, [op]):
                    op_list.append(op)
                    return Individual(op_list)
                else:
                    # needed for ~0 lines above
                    app.scops[x1].rollback()
                    #app.reset_scops()
                    #app.transform_list(op_list)

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
    base = "examples/polybench"

    def __init__(self, args):
        seed(args.seed)
        print(f"Opening {args.benchmark}")
        self.dataset = f"-D{args.dataset}_DATASET"
        oflag = f"-O{args.oflag}"
        print(f"Using {self.dataset}")
        self.benchmark = args.benchmark
        self.base = args.base
        self.app_factory = Polybench(args.benchmark, base=self.base, compiler_options=[self.dataset], translator=Polly("clang"))
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

        if self.n_threads > 1:
            self.executor = MPIPoolExecutor()


        # The initial population is an individual without transformations
        # so the algorithm starts by searching for simpler solutions first
        self.population.append(Individual())


    def tournament(self):
        """
        Requires: sorted population (best to worst)
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
                # Using the MPI Executor previously initialized
                kwargs = {
                    "benchmark":self.benchmark,
                    "base":self.base,
                    "compiler_options":["-fopenmp", self.dataset],
                    "translator":"Polly",
                }
                results = list(self.executor.map(
                    remote_measure, 
                    [Polybench] * len(self.population),
                    [kwargs] * len(self.population), 
                    [ind.operation_list for ind in self.population] 
                ))
                for i in range(len(results)):
                    self.population[i].fitness = results[i][0] * -1 # so bigger fitness is better
                    self.evaluations[str(self.population[i].operation_list)]=results[i][0]*-1
            else:
                fitnesses = [
                    i.getFitness(
                        self.app_factory,
                        self.n_trials,
                        timeout=self.timeout,
                        evaluations=self.evaluations,
                    )
                    for i in self.population
                ]

            # Sort best to worst
            self.population.sort(reverse=True)

            end_time = time.time()
            print("Evaluation time:", end_time - start_time)

            print("  Top-3 solutions found:")
            [print("   ", i.fitness, i) for i in self.population[:3]]

            if self.population[0] > self.best_individual:
                self.best_individual = self.population[0]
                print("  Updating best_individual to", self.best_individual)

            # print("  Generating new population")
            start_time = time.time()
            new_pop = []
            while len(new_pop) < self.population_size:
                ind1 = self.tournament()
                ind2 = self.tournament()
                ind1 = ind1.mutate(self.app_factory)
                ind2 = ind2.mutate(self.app_factory)
                if False:
                    # TODO: Implement crossover
                else:
                    ret = [ind1, ind2] # no crossover
                new_pop.extend(ret)
            new_pop = new_pop[: self.population_size]
            self.population = new_pop
            end_time = time.time()
            print("Reproduction time:", end_time - start_time)

            be = self.evaluations[str(self.best_individual.operation_list)]
            print(
                "  Fitness on generation %d: %.8f (%.3fx speedup)"
                % (gen, be, self.evaluations["[]"] / be)
            )

        print("Final model:", self.best_individual)
    
    return self.best_individual
