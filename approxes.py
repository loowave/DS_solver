import random
import networkx as nx

def approx_2_ds(g_orig: nx.Graph):
    g = g_orig.copy()
    n = len(g.nodes)
    answer = 0
    ds = set()
    dominated = set()
    while len(g.edges) > 0:
        edge = random.choice(list(g.edges))
        ds.add(edge[0])
        ds.add(edge[1])
        answer += 2
        if edge[0] == edge[1]:
            answer -= 1
        d = set(g.neighbors(edge[0]))
        d = d.union(g.neighbors(edge[1]))
        d.discard(edge[0])
        d.discard(edge[1])
        dominated.update(d)
        dominated.update(set(edge))
        g.remove_nodes_from(d)
        g.remove_nodes_from(edge)
    for i in range(1, n):
        if i not in dominated:
            ds.add(i)
            answer += 1
    return list(ds)


def approx_ln_ds(g_orig: nx.Graph):
    g = g_orig.copy()
    ds = set()
    dominated = set()
    answer = 0
    n = len(g.nodes)
    while len(g.edges) > 0:
        v = max(g.degree, key=lambda x: x[1])
        ds.add(v[0])
        d = set(g.neighbors(v[0]))
        d.discard(v[0])
        dominated.update(d)
        dominated.add(v[0])
        g.remove_nodes_from(d)
        g.remove_node(v[0])
        answer += 1
    for i in range(1, n + 1):
        if i not in dominated:
            ds.add(i)
            answer += 1
    return list(ds)
