import networkx as nx
from pulp import *
import random
import time
import math
from collections import Counter

class LpGraphSolver:
    def __init__(self, g: nx.Graph, temp=8, ones=[]):
        self.g = g
        self.n = self.g.number_of_nodes()
        self.vc_res = []
        self.lp_res = []
        self.roundingds = []
        self.roundingds2 = []
        self.temp = temp
        self.ones = ones

    def SolveLP(self):
        self.lp_res = self.SolveDominatingSet(self.ones)
        return sum(self.lp_res)


    def SolveDominatingSet(self, ones=[], zeros=[]):
        problem = LpProblem("DominatingSet", LpMinimize)
        vars = list(LpVariable("node" + str(i), lowBound=0, upBound=1, cat="Continuous") for i in range(self.n + 1))
        for x in ones:
            problem += vars[x] == 1
        for x in zeros:
            problem += vars[x] == 0
        problem += vars[0] == 0
        for i in range(1, self.n + 1):  # constraints
            problem += vars[i] + lpSum([(vars[x] if x != i else 0) for x in self.g.neighbors(i)]) >= 1
        problem += lpSum(vars)
        status = problem.solve(PULP_CBC_CMD(msg=False))
        if LpStatus[status] == 'Optimal':
            return list(value(var) for var in vars)
        else:
            raise Exception("Non optimal LP")

    def LpRoundingDS(self):
        self.roundingds = self.lp_res.copy()
        for i in range(1, self.n + 1):
            if self.roundingds[i] > 0.8:
                self.roundingds[i] = 1
        count = 0
        for i in range(1, self.n + 1):
            v_val = self.roundingds[i]
            max_neig_idx = -1
            max_neig_val = -1
            if v_val == 1:
                continue
            for j in self.g.neighbors(i):
                if j == i:
                    continue
                if self.roundingds[j] > max_neig_val:
                    max_neig_idx = j
                    max_neig_val = self.roundingds[j]
            if v_val > max_neig_val:
                self.roundingds[i] = 1
            else:
                self.roundingds[max_neig_idx] = 1
        for i in range(1, self.n + 1):
            if self.roundingds[i] != 1:
                self.roundingds[i] = 0
        return sum(self.roundingds)

    def LpRoundingDS_ver2(self):
        self.roundingds2 = self.lp_res.copy()
        iters = 0
        while (not all(map(lambda x: x == 0.0 or x == 1.0, self.roundingds2)) and
               any(map(lambda x: x > 0.8 and x != 1.0, self.roundingds2))):
            ones = []
            zeros = []
            for i in range(1, self.n + 1):
                if self.roundingds2[i] > 0.8:
                    self.roundingds2[i] = 1
                    ones.append(i)
            self.roundingds2 = self.SolveDominatingSet(ones)
            if iters == 5:
                break
            iters += 1

        if all(map(lambda x: x == 0.0 or x == 1.0, self.roundingds2)):
            return sum(self.roundingds2)
        for i in range(1, self.n + 1):
            v_val = self.roundingds2[i]
            max_neig_idx = -1
            max_neig_val = -1
            if v_val == 1:
                continue
            for j in self.g.neighbors(i):
                if j == i:
                    continue
                if self.roundingds2[j] > max_neig_val:
                    max_neig_idx = j
                    max_neig_val = self.roundingds2[j]
            if v_val > max_neig_val:
                self.roundingds2[i] = 1
            else:
                self.roundingds2[max_neig_idx] = 1
        for i in range(1, self.n + 1):
            if self.roundingds2[i] != 1:
                self.roundingds2[i] = 0
        return sum(self.roundingds2)


    # BRANCH and BOUND Dominating set
    def BranchBoundDS(self, take=1):
        vertices = set()
        return self.BranchNBoundTreeDS(vertices, [], [], take)


    def BranchNBoundTreeDS(self, vertices, ones, zeros, take):
        if all(map(lambda x: x == 0.0 or x == 1.0, self.lp_res)):
            return sum(self.lp_res)
        if len(vertices) % 10 == 0:
            print(len(vertices))
        v = -1
        if len(vertices) == 0:
            v = min(list(range(1, self.n + 1)), key=lambda x: abs(0.5 - self.lp_res[x]))
        else:
            ans, vals = self.SolveBoundedDS(ones, zeros)
            v = min(list(range(1, self.n + 1)), key=lambda x: abs(0.5 - vals[x]) if not x in vertices else 100)
        vertices.add(v)

        left_res, left_vals = self.SolveBoundedDS(ones + [v], zeros)
        right_res, right_vals = self.SolveBoundedDS(ones, zeros + [v])

        if all(map(lambda x: x == 0.0 or x == 1.0, left_vals)):
            return left_res, len(vertices)
        elif all(map(lambda x: x == 0.0 or x == 1.0, right_vals)):
            return right_res, len(vertices)

        if left_res > right_res:
            if left_res - right_res > self.temp:
                return self.BranchNBoundTreeDS(vertices, ones, zeros + [v], take)

            rnd = random.random()
            if rnd > 0.5:
                return self.BranchNBoundTreeDS(vertices, ones, zeros + [v], take)
            else:
                return self.BranchNBoundTreeDS(vertices, ones + [v], zeros, take)
        else:
            if right_res - left_res > self.temp:
                return self.BranchNBoundTreeDS(vertices, ones + [v], zeros, take)

            rnd = random.random()
            if rnd > 0.5:
                return self.BranchNBoundTreeDS(vertices, ones + [v], zeros, take)
            else:
                return self.BranchNBoundTreeDS(vertices, ones, zeros + [v], take)

    def SolveBoundedDS(self, ones, zeros):
        problem = LpProblem("BoundedDS", LpMinimize)
        vars = list(LpVariable("node" + str(i), lowBound=0, upBound=1, cat="Continuous") for i in range(self.n + 1))
        problem += vars[0] == 0
        for i in ones:
            problem += vars[i] == 1
        for i in zeros:
            problem += vars[i] == 0
        for i in range(1, self.n + 1):  # constraints
            problem += vars[i] + lpSum([(vars[x] if x != i else 0) for x in self.g.neighbors(i)]) >= 1
        problem += lpSum(vars)
        status = problem.solve(PULP_CBC_CMD(msg=False))
        if LpStatus[status] == 'Optimal':
            return (sum(value(var) for var in vars), list(value(var) for var in vars))
        else:
            raise Exception(f"bad status: {LpStatus[status]}")

if __name__ == "__main__":
    g = nx.Graph()

    with open(f"./exact_graphs/exact_026.gr") as f:
        line = f.readline()
        while (line[0] == 'c'):
            line = f.readline()
        _, problem, vertices, edges = line.split()
        vertices, edges = int(vertices), int(edges)
        g.add_nodes_from(range(1, vertices + 1))
        for i in range(edges):
            v, u = map(int, f.readline().split())
            g.add_edge(v, u)

    g_lp = LpGraphSolver(g)
    g_lp.SolveLP()
    print(g_lp.LpRoundingDS())
    print(g_lp.LpRoundingDS_ver2())
