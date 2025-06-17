import random
from math import exp, floor
from approxes import approx_ln_ds, approx_greedy_ds, approx_2_ds
from lower_bound_lp import LpGraphSolver
from time import time
import networkx as nx

class DSAnnealing:
    def __init__(self, g: nx.Graph, approx_type='ln'):
        self.n = len(g.nodes)
        self.g = g
        if (approx_type == 'ln'):
            self.ds = approx_ln_ds(g)
            self.temp = 0.1
        elif (approx_type == '2'):
            self.ds = approx_2_ds(g)
            self.temp = 0.2
        elif (approx_type == 'lp'):
            g_lp = LpGraphSolver(g)
            g_lp.SolveLP()
            g_lp.LpRoundingDS_ver2()
            self.ds = set(filter(lambda x: g_lp.roundingds2[x] == 1, range(1, self.n + 1)))
            self.temp = 0.05
        elif (approx_type == 'greedy'):
            self.ds = approx_greedy_ds(g)
            self.remove_not_needed()
            self.temp = 0.5
        elif (approx_type == 'no_approx'):
            self.ds = set(range(1, self.n))
            self.remove_not_needed()
            self.temp = 0.1


    def move(self, k):
        vers = random.sample(tuple(self.ds), k)
        new_ds = self.ds.copy().difference(set(vers))
        for ver in vers:
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
                    new_ds.add(ver)
        return new_ds


    def annealing(self, type='exp', temp_base=0.001, alpha = 0.1, cooling_rate=0.95):
        start_temp = self.temp
        k = 0
        while self.temp > temp_base:
            accepted_moves = 0
            for i in range(3000):
                new_ds = self.move(max(1, floor(self.n / 100 - 1.7 ** k)))
                new_size = len(new_ds)
                size = len(self.ds)
                normalized_delta = (size - new_size) / size
                try:
                    prob = min(exp(normalized_delta * floor(self.n * alpha) / self.temp), 1.0)
                except OverflowError:
                    prob = 1.0 if normalized_delta > 0 else 0.0
                rand_n = random.random()
                if prob >= rand_n:
                    self.ds = new_ds
                    accepted_moves += 1
            k += 1
            if type == 'exp':
                self.temp *= cooling_rate
            elif type == 'poly':
                self.temp = start_temp / pow(1 + k, 0.8)
            elif type == 'adaptive':
                # Adjust cooling based on acceptance rate
                acceptance_rate = accepted_moves / 1000
                if acceptance_rate > 0.5:
                    # Cooling too fast, slow it down
                    self.temp *= 0.9 + cooling_rate
                else:
                    # Cooling too slow, speed it up
                    self.temp *= 0.9 - cooling_rate
            elif type == 'step':
                if k % 5 == 0:
                    self.temp *= cooling_rate
        self.remove_not_needed()
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

    def remove_not_needed(self):
        for ver in tuple(self.ds):
            has_neig_in_ds = False
            all_neig_are_covered = True
            for neig in self.g.neighbors(ver):
                if neig == ver:
                    continue
                if neig in self.ds:
                    has_neig_in_ds = True
                else:
                    covered = False
                    for neig_neig in self.g.neighbors(neig):
                        if neig_neig == ver or neig_neig == neig:
                            continue
                        elif neig_neig in self.ds:
                            covered = True
                    if not covered:
                        all_neig_are_covered = False
            if has_neig_in_ds and all_neig_are_covered:
                self.ds.remove(ver)


if __name__ == "__main__":
    g = nx.Graph()

    with open(f"./heuristic_graphs/heuristic_001.gr") as f:
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
    print(f"Lp finished Time: {time() - start}")
    print(f"Poly: {g_lp_anneal.annealing('poly')} Time: {time() - start}")

