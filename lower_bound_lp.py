import networkx as nx
from pulp import *
import random
import time
import math

class LpGraphSolver:
    def __init__(self, g: nx.Graph, temp=8):
        self.g = g
        self.n = self.g.number_of_nodes()
        self.vc_res = []
        self.ds_res = []
        self.roundingds = []
        self.temp = temp

    def SolveDominatingSet(self):
        problem = LpProblem("DominatingSet", LpMinimize)
        vars = list(LpVariable("node" + str(i), lowBound=0, upBound=1, cat="Continuous") for i in range(self.n + 1))
        problem += vars[0] == 0
        for i in range(1, self.n + 1):  # constraints
            problem += vars[i] + lpSum([(vars[x] if x != i else 0) for x in self.g.neighbors(i)]) >= 1
        problem += lpSum(vars)
        status = problem.solve(PULP_CBC_CMD(msg=False))
        if LpStatus[status] == 'Optimal':
            self.ds_res = list(value(var) for var in vars)
            return sum(value(var) for var in vars)
        else:
            return f"Non optimal: {sum(value(var) for var in vars)}"

    def LpRoundingDS(self):
        self.roundingds = self.ds_res.copy()
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
        return list(filter(lambda x: self.roundingds[x] == 1, list(range(1, self.n + 1))))

    # BRANCH and BOUND Dominating set
    def BranchBoundDS(self, take=1):
        vertices = set()
        return self.BranchNBoundTreeDS(vertices, [], [], take)


    def BranchNBoundTreeDS(self, vertices, ones, zeros, take):
        if all(map(lambda x: x == 0.0 or x == 1.0, self.ds_res)):
            return sum(self.ds_res)
        if len(vertices) % 10 == 0:
            print(len(vertices))
        v = -1
        if len(vertices) == 0:
            v = min(list(range(1, self.n + 1)), key=lambda x: abs(0.5 - self.ds_res[x]))
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

    g_lp = LpGraphSolver(g)
    print(g_lp.SolveDominatingSet())