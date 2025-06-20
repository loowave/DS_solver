import os
import networkx as nx
from lower_bound_lp import LpGraphSolver
from local_search import DSAnnealing
import csv
from math import ceil
import signal
from contextlib import contextmanager

class TimeoutException(Exception):
    pass

@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

directory = './exact_graphs'

if __name__ == "__main__":
    """
    with open('results.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        # Write header
        writer.writerow(['graph', 'vertices', 'edges', 'LP_lower_bound', 'Best_upper_bound',
                         'Ln_approx', 'Ln_approx_annealing',
                         'LpRound_approx', 'LpRound_approx_annealing'])

        for filename in os.listdir(directory):
            if not filename.endswith('.gr'):
                continue
            g = nx.Graph()
            graph = filename
            vertices, edges = 0, 0
            filepath = os.path.join(directory, filename)
            if not os.path.isfile(filepath):
                raise FileExistsError
            with open(filepath) as f:
                line = f.readline()
                while (line[0] == 'c'):
                    line = f.readline()
                _, problem, vertices, edges = line.split()
                vertices, edges = int(vertices), int(edges)
                g.add_nodes_from(range(1, vertices + 1))
                for i in range(edges):
                    v, u = map(int, f.readline().split())
                    g.add_edge(v, u)
            lp_lower_bound = ceil(LpGraphSolver(g).SolveDominatingSet())
            ds_annealing_ln = DSAnnealing(g, 'ln')
            ln_approx = len(ds_annealing_ln.ds)
            ln_approx_anneal = ds_annealing_ln.annealing()
            ds_annealing_lp = DSAnnealing(g, 'lp')
            lp_approx = len(ds_annealing_lp.ds)
            lp_approx_anneal = ds_annealing_lp.annealing(0.05)
            best_anneal = min(ln_approx_anneal, lp_approx_anneal)
            writer.writerow([graph, vertices, edges, lp_lower_bound, best_anneal,
                             ln_approx, ln_approx_anneal,
                             lp_approx, lp_approx_anneal])
        """
    with open('results.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        # Write header
        writer.writerow(['graph', 'vertices', 'LpRoundAnnealing'])

        for filename in sorted(os.listdir(directory)):
            if not filename.endswith('.gr'):
                continue
            g = nx.Graph()
            graph = filename
            vertices = 0
            filepath = os.path.join(directory, filename)
            if not os.path.isfile(filepath):
                raise FileExistsError
            with open(filepath) as f:
                line = f.readline()
                while (line[0] == 'c'):
                    line = f.readline()
                _, problem, vertices, edges = line.split()
                vertices = int(vertices)
                g.add_nodes_from(range(1, vertices + 1))
                for i in range(int(edges)):
                    v, u = map(int, f.readline().split())
                    g.add_edge(v, u)

            try:
                with time_limit(40):  # 40 second timeout
                    ds_annealing_lp = DSAnnealing(g, 'lp')
                    lp_approx_anneal = ds_annealing_lp.annealing('poly')
            except TimeoutException:
                lp_approx_anneal = 'TIMEOUT'

            writer.writerow([graph, vertices, lp_approx_anneal])