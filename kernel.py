import networkx as nx
import pulp
import random


def exact_min_dominating_set(G):
    """
    Solves for the exact minimum dominating set using ILP.
    Requires PuLP (`pip install pulp`).
    Returns a set of nodes forming a minimum dominating set.
    """
    # Create the ILP problem
    prob = pulp.LpProblem("Minimum_Dominating_Set", pulp.LpMinimize)

    # Binary variable for each node: 1 if node is in the dominating set, 0 otherwise
    x = {v: pulp.LpVariable(f"x_{v}", cat='Binary') for v in G.nodes()}

    # Objective: minimize the size of the dominating set
    prob += pulp.lpSum(x[v] for v in G.nodes()), "TotalNodesInDominatingSet"

    # Constraint: each node must be dominated (by itself or neighbor)
    for v in G.nodes():
        prob += pulp.lpSum(x[u] for u in {v}.union(set(G.neighbors(v)))) >= 1, f"Dominate_{v}"


    # Solve
    prob.solve(pulp.PULP_CBC_CMD(msg=False))

    # Extract solution
    dom_set = {v for v in G.nodes() if pulp.value(x[v]) == 1}
    return dom_set


class Kernel:
    def __init__(self, g: nx.Graph):
        self.g = g
        self.neighbors = {}
        for v in g.nodes:
            self.neighbors[v] = set(g.neighbors(v))
        #degrees = dict(g.degree())
        #sorted_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)
        #self.sample = [node for node, degree in sorted_nodes[:300]]
        self.sample = random.sample(list(g.nodes()), 250)


    def rules(self):
        g = self.g
        flag = False
        nodes_copy = list(g.nodes())
        # rule 1
        for v in nodes_copy:
            if not g.has_node(v):
                continue
            n1 = self.neighbors[v]
            n1.discard(v)
            n1_minus = set()
            for u in n1:
                if len(set(g.neighbors(u)).difference(n1)) <= 1: # no neighbors besides v
                    n1_minus.add(u)
            n1 = n1.difference(n1_minus)
            n2 = self.neighbors[v].difference(n1)
            n2.discard(v)
            n2_minus = set()
            for u in n2:
                if len(self.neighbors[u].intersection(n1)) == 0:
                    n2_minus.add(u)
            n2 = n2.difference(n2_minus)
            n3 = self.neighbors[v].difference(n1).difference(n2)
            n3.discard(v)
            if len(n3) > 0:
                delete_vertices = n2.union(n3)
                temp = delete_vertices.pop()
                delete_vertices.add(temp)
                if len(delete_vertices) > 1 or g.degree[temp] > 1:
                    for w1 in delete_vertices:
                        for w2 in self.neighbors[w1]:
                            if w2 != w1:
                                self.neighbors[w2].discard(w1)
                        self.neighbors.pop(w1)
                    g.remove_nodes_from(delete_vertices)
                    z = max(g.nodes) + 1
                    g.add_edge(v, z)
                    self.neighbors[v].add(z)
                    self.neighbors[z] = {v}
                    flag = True

        nodes_copy = list(g.nodes())
       # rule 2
        for v in self.sample:
            for u in nodes_copy:
                if u == v or not g.has_node(u) or not g.has_node(v):
                    continue
                n1 = self.neighbors[v].union(self.neighbors[u])
                n1.discard(v)
                n1.discard(u)
                n1_minus = set()
                for w in n1:
                    if len(self.neighbors[w].difference(n1).difference({v, u})) == 0:
                        n1_minus.add(w)
                n1 = n1.difference(n1_minus)
                n2 = self.neighbors[v].union(self.neighbors[u]).difference(n1)
                n2.discard(v)
                n2.discard(u)
                n2_minus = set()
                for w in n2:
                    if len(self.neighbors[w].intersection(n1)) == 0:
                        n2_minus.add(w)
                n2 = n2.difference(n2_minus)
                n3 = self.neighbors[v].union(self.neighbors[u]).difference(n1).difference(n2)
                n3.discard(v)
                n3.discard(u)
                if len(n3) > 0:
                    solo_dominated = False
                    for w in n2.union(n3):
                        if self.neighbors[w].union({w}).issuperset(n3):
                            solo_dominated = True
                            break
                    if solo_dominated:
                        continue

                    v_neig = self.neighbors[v]
                    u_neig = self.neighbors[u]
                    z1 = max(g.nodes) + 1
                    z2 = z1 + 1
                    if n3.issubset(v_neig):
                        if n3.issubset(u_neig):
                            delete_vertices = n3.union(n2.difference(v_neig).difference(u_neig))
                            temp = delete_vertices.pop()
                            delete_vertices.add(temp)
                            if len(delete_vertices) > 2 or (len(delete_vertices) >= 1 and g.degree[temp] > 2):
                                for w1 in delete_vertices:
                                    for w2 in self.neighbors[w1]:
                                        if w2 != w1:
                                            self.neighbors[w2].discard(w1)
                                    self.neighbors.pop(w1)
                                g.remove_nodes_from(delete_vertices)
                                g.add_edge(v, z1)
                                g.add_edge(v, z2)
                                g.add_edge(u, z1)
                                g.add_edge(u, z2)
                                self.neighbors[v].add(z1)
                                self.neighbors[v].add(z2)
                                self.neighbors[u].add(z1)
                                self.neighbors[u].add(z2)
                                self.neighbors[z1] = {v, u}
                                self.neighbors[z2] = {v, u}
                                flag = True
                        else:
                            delete_vertices = n3.union(n2.difference(v_neig))
                            temp = delete_vertices.pop()
                            delete_vertices.add(temp)
                            if len(delete_vertices) > 1 or (len(delete_vertices) == 1 and g.degree[temp] > 1):
                                for w1 in delete_vertices:
                                    for w2 in self.neighbors[w1]:
                                        if w2 != w1:
                                            self.neighbors[w2].discard(w1)
                                    self.neighbors.pop(w1)
                                g.remove_nodes_from(delete_vertices)
                                g.add_edge(v, z1)
                                self.neighbors[v].add(z1)
                                self.neighbors[z1] = {v}
                                flag = True
                    else:
                        if n3.issubset(u_neig):
                            delete_vertices = n3.union(n2.difference(u_neig))
                            temp = delete_vertices.pop()
                            delete_vertices.add(temp)
                            if len(delete_vertices) > 1 or (len(delete_vertices) == 1 and g.degree[temp] > 1):
                                for w1 in delete_vertices:
                                    for w2 in self.neighbors[w1]:
                                        if w2 != w1:
                                            self.neighbors[w2].discard(w1)
                                    self.neighbors.pop(w1)
                                g.remove_nodes_from(delete_vertices)
                                g.add_edge(u, z1)
                                self.neighbors[u].add(z1)
                                self.neighbors[z1] = {u}
                                flag = True
                        else:
                            delete_vertices = n3.union(n2)
                            temp = delete_vertices.pop()
                            delete_vertices.add(temp)
                            if len(delete_vertices) > 2 or (len(delete_vertices) >= 1 and g.degree[temp] > 1):
                                for w1 in delete_vertices:
                                    for w2 in self.neighbors[w1]:
                                        if w2 != w1:
                                            self.neighbors[w2].discard(w1)
                                    self.neighbors.pop(w1)
                                g.remove_nodes_from(delete_vertices)
                                g.add_edge(v, z1)
                                g.add_edge(u, z2)
                                self.neighbors[v].add(z1)
                                self.neighbors[u].add(z2)
                                self.neighbors[z1] = {v}
                                self.neighbors[z2] = {u}
                                flag = True
        return flag

    def kernelise(self):
        g = self.g
        x = len(g.nodes())
        counter = 0
        while (self.rules()):
            if len(g.nodes) != x:
                x = len(g.nodes)
                counter += 1
                print(g)
            else:
                break
