import random
from math import exp, floor
from approxes import approx_ln_ds
from lower_bound_lp import LpGraphSolver
from time import time
import networkx as nx

class DSAnnealing:
    def __init__(self, g: nx.Graph, approx_type='ln'):
        if (approx_type == 'ln'):
            self.ds = approx_ln_ds(g)
        elif (approx_type == 'lp'):
            g_lp = LpGraphSolver(g)
            g_lp.SolveDominatingSet()
            self.ds = g_lp.LpRoundingDS()

        self.n = len(g.nodes)
        self.g = g

    def move(self):
        ver = random.choice(self.ds)
        new_ds = self.ds.copy()
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
                    new_ds.append(neighbor)
        flag = False
        for neighbor in self.g.neighbors(ver):
            if neighbor in new_ds:
                flag = True
        if not flag:
            if len(list(self.g.neighbors(ver))) > 0:
                new_ds.append(next(self.g.neighbors(ver)))
            else:
                return self.ds

        return new_ds


    def annealing(self, temp = 0.1, alpha = 0.1):
        while temp > 0.01:
            for i in range(floor(self.n * alpha)):
                new_ds = self.move()
                new_size = len(new_ds)
                size = len(self.ds)
                normalized_delta = (size - new_size) / size
                try:
                    prob = min(exp(normalized_delta * floor(self.n * alpha) / temp), 1.0)
                except OverflowError:
                    prob = 1.0 if normalized_delta > 0 else 0.0
                rand_n = random.random()
                if prob >= rand_n:
                    self.ds = new_ds
            temp *= 0.9
        if self.check():
            return len(self.ds)
        else:
            return 'NOT DS'


    def check(self):
        for i in range(1, self.n + 1):
            if i not in self.ds:
                flag = True
                for j in self.g.neighbors(i):
                    if j in self.ds:
                        flag = False
                if flag:
                    return False
        return True


if __name__ == "__main__":
    g = nx.Graph()

    with open(f"./exact_graphs/exact_050.gr") as f:
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
    print("Ln approx anneal")
    ds_annealing_ln = DSAnnealing(g, 'ln')
    print(len(ds_annealing_ln.ds))
    print(ds_annealing_ln.annealing())
    print(f"Time: {time() - start}")
    start = time()
    print("LpRounding approx anneal")
    g_lp_anneal = DSAnnealing(g, 'lp')
    print(len(g_lp_anneal.ds))
    print(g_lp_anneal.annealing(0.5))
    print(f"Time: {time() - start}")
