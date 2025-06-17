from local_search import DSAnnealing
from lower_bound_lp import LpGraphSolver
import networkx as nx
import random
from math import floor, exp
from time import time


class DSGenetic:
    def __init__(self, g: nx.Graph):
        self.population = list()
        for i in range(20):
          g_lp_anneal = DSAnnealing(g, 'lp')
          g_lp_anneal.annealing(0.04)
          self.population.append(g_lp_anneal.ds)

        print("init_finish")
        self.n = len(g.nodes)
        self.g = g
        self.best = float('inf')
        self.best_ds = []

    def move(self, idx):
        ds = self.population[idx]
        ver = random.choice(tuple(ds))
        new_ds = ds.copy()
        new_ds.remove(ver)
        for neighbor in self.g.neighbors(ver):
          if neighbor == ver:
            continue
          if neighbor not in new_ds:
            flag = False
            for neighbor2 in self.g.neighbors(neighbor):
              if neighbor2 in new_ds:
                flag = True
            if not flag:
              new_ds.add(neighbor)
        flag = False
        for neighbor in self.g.neighbors(ver):
          if neighbor in new_ds:
            flag = True
        if not flag:
          if len(list(self.g.neighbors(ver))) > 0:
            new_ds.add(next(self.g.neighbors(ver)))
          else:
            return ds
        return new_ds

    def cross(self, idx1, idx2):
        ds1 = self.population[idx1]
        ds2 = self.population[idx2]

        ds = ds1 & ds2  # intersection

        g_lp = LpGraphSolver(self.g, ds)
        g_lp.SolveLP()
        g_lp.LpRoundingDS()
        ds = set(filter(lambda x: g_lp.roundingds[x] == 1, range(1, self.n + 1)))

        return ds

    def work(self, temp=0.05, alpha=0.1):
        steps = 0

        while temp > 0.01:
            # MOVES
            for i in range(len(self.population)):
                for _ in range(10):
                    new_ds = self.move(i)
                    new_size = len(new_ds)
                    size = len(self.population[i])
                    normalized_delta = (size - new_size) / size
                    try:
                        prob = min(exp(normalized_delta * floor(self.n * alpha) / temp), 1.0)
                    except OverflowError:
                        prob = 1.0 if normalized_delta > 0 else 0.0
                    rand_n = random.random()
                    if prob >= rand_n:
                        self.population[i] = new_ds

            # CROSSOVER
            children = []
            for i in range(len(self.population)):
                for j in range(i + 1, len(self.population)):
                    children.append(self.cross(i, j))

            # SELECTION
            self.population = sorted(self.population, key=lambda x: len(x))
            survivors = self.population[:5] + random.sample(self.population[10:20], 5)
            children = sorted(children, key=lambda x: len(x))
            survivors += children[:5] + random.sample(children[10:20], 5)
            self.population = survivors[:20]  # Ensure fixed population size

            temp *= 0.9
            current_best = len(self.population[0])
            if self.best == current_best:
                steps += 1
            else:
                self.best = current_best
                self.best_ds = self.population[0]
                steps = 0

            if steps >= 3:
                break
        return self.best

if __name__ == "__main__":
    g = nx.Graph()

    with open(f"./exact_graphs/exact_020.gr") as f:
        line = f.readline()
        while (line[0] == 'c'):
            line = f.readline()
        _, problem, vertices, edges = line.split()
        vertices, edges = int(vertices), int(edges)
        g.add_nodes_from(range(1, vertices + 1))
        for i in range(edges):
            v, u = map(int, f.readline().split())
            g.add_edge(v, u)

    start = time()
    g_lp_anneal = DSAnnealing(g, 'lp')
    g_lp_anneal.remove_not_needed()
    print(len(g_lp_anneal.ds))
    print(f"LP: {g_lp_anneal.annealing()} Time: {time() - start}")
    start = time()
    genetic = DSGenetic(g)
    print(f"GENETIC: {genetic.work()} Time: {time() - start}")