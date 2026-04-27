#!/usr/bin/env python

import argparse
from ReinforcementLearning import ReinforcementLearning


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tadashi RL Optimization")
    
    # Benchmark settings
    parser.add_argument("--benchmark", type=str, default="jacobi-1d",
                        help="Benchmark to optimize")
    parser.add_argument("--dataset", type=str, default="LARGE",
                        help="Dataset size (SMALL, MEDIUM, LARGE, EXTRALARGE)")
    parser.add_argument("--oflag", type=int, default=3,
                        help="Optimization flag (0-3)")
    
    # RL settings
    parser.add_argument("--seed", type=int, default=47,
                        help="Random seed")
    parser.add_argument("--n-trials", type=int, default=2,
                        help="Number of trials for evaluation")
    parser.add_argument("--max-gen", type=int, default=50,
                        help="Maximum number of episodes (generations)")
    parser.add_argument("--max-depth", type=int, default=20,
                        help="Maximum steps per episode")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Tadashi Reinforcement Learning Optimization")
    print("=" * 60)
    print(f"Benchmark: {args.benchmark}")
    print(f"Dataset: {args.dataset}")
    print(f"Optimization Flag: -O{args.oflag}")
    print(f"Max Episodes: {args.max_gen}")
    print(f"Max Steps per Episode: {args.max_depth}")
    print(f"Random Seed: {args.seed}")
    print("=" * 60)
    print()
    
    # Create and run RL optimizer
    rl_optimizer = ReinforcementLearning(args)
    rl_optimizer.fit()
