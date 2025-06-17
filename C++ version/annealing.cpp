#include <iostream>
#include <vector>
#include <unordered_set>
#include <random>
#include <cmath>
#include <chrono>
#include <boost/graph/adjacency_list.hpp>
#include <boost/graph/graph_traits.hpp>
#include <queue>
#include <functional>

using namespace boost;

// Graph type definitions
typedef adjacency_list<vecS, vecS, undirectedS> Graph;
typedef graph_traits<Graph>::vertex_descriptor Vertex;
typedef graph_traits<Graph>::vertex_iterator VertexIterator;
typedef graph_traits<Graph>::adjacency_iterator AdjacencyIterator;

class DSAnnealing {
private:
    Graph g;
    int n;
    std::unordered_set<int> ds;
    double temp;
    std::random_device rd;
    std::mt19937 gen;

public:
    DSAnnealing(const Graph& graph, const std::string& approx_type = "ln")
            : g(graph), gen(rd()) {
        n = num_vertices(g);

        if (approx_type == "ln") {
            approx_ln_ds(g);
            temp = 0.1;
        } else if (approx_type == "2") {
            ds = approx_2_ds(g);
            temp = 0.2;
        } else if (approx_type == "greedy") {
            ds = approx_greedy_ds(g);
            remove_not_needed();
            temp = 0.5;
        } else if (approx_type == "no_approx") {
            for (int i = 1; i < n; ++i) {
                ds.insert(i);
            }
            remove_not_needed();
            temp = 0.1;
        }
    }

    std::unordered_set<int> move() {
        if (ds.empty()) return ds;  // Return empty set if no vertices to remove

        // Convert current DS to vector for random selection
        std::vector<int> ds_vec(ds.begin(), ds.end());

        // Select random vertex to remove
        std::uniform_int_distribution<size_t> dist(0, ds_vec.size() - 1);
        size_t i = dist(gen);
        int ver = ds_vec[i];

        std::unordered_set<int> new_ds = ds;
        new_ds.erase(ver);

        // Add necessary neighbors to maintain domination
        AdjacencyIterator ai, a_end;

        // 1. Ensure all neighbors of 'ver' are covered
        for (std::tie(ai, a_end) = adjacent_vertices(vertex(ver, g), g); ai != a_end; ++ai) {
            int neighbor = *ai;
            if (neighbor == ver) continue;  // Skip self-loops

            // If neighbor not in new DS and not dominated by others
            if (new_ds.find(neighbor) == new_ds.end()) {
                bool is_dominated = false;
                AdjacencyIterator ai2, a_end2;
                for (std::tie(ai2, a_end2) = adjacent_vertices(vertex(neighbor, g), g);
                     ai2 != a_end2; ++ai2) {
                    if (new_ds.find(*ai2) != new_ds.end()) {
                        is_dominated = true;
                        break;
                    }
                }
                if (!is_dominated) {
                    new_ds.insert(neighbor);
                }
            }
        }

        // 2. Ensure 'ver' itself is covered (if it has neighbors)
        bool is_covered = false;
        for (std::tie(ai, a_end) = adjacent_vertices(vertex(ver, g), g); ai != a_end; ++ai) {
            if (new_ds.find(*ai) != new_ds.end()) {
                is_covered = true;
                break;
            }
        }

        if (!is_covered) {
            auto [ai, a_end] = adjacent_vertices(vertex(ver, g), g);
            if (ai != a_end) {
                // Add first available neighbor
                new_ds.insert(*ai);
            } else {
                // Isolated vertex must be in DS
                new_ds.insert(ver);
            }
        }

        return new_ds;
    }

    double annealing(const std::string& type = "poly", double temp_base = 0.001,
                     double alpha = 0.1, double cooling_rate = 0.95,
                     double max_time_seconds = 120.0) {
        auto start_time = std::chrono::high_resolution_clock::now();
        double start_temp = temp;
        int k = 0;
        std::uniform_real_distribution<double> dist(0.0, 1.0);

        while (temp > temp_base) {
            auto current_time = std::chrono::high_resolution_clock::now();
            double elapsed = std::chrono::duration<double>(current_time - start_time).count();
            if (elapsed >= max_time_seconds) {
                break;
            }
            //int accepted = 0;
            for (int i = 0; i < 300; ++i) {
                auto new_ds = move();
                int new_size = new_ds.size();
                int size = ds.size();

                if (size == 0) continue; // Avoid division by zero

                double normalized_delta = static_cast<double>(size - new_size);
                double prob;

                try {
                    prob = std::min(exp(normalized_delta / temp), 1.0);
                } catch (...) {
                    prob = (normalized_delta > 0) ? 1.0 : 0.0;
                }

                double rand_n = dist(gen);
                if (prob >= rand_n) {
                    ds = new_ds;
                    //++accepted;
                }
            }
            //std::cout << accepted << std::endl;

            k++;
            if (type == "exp") {
                temp *= cooling_rate;
            } else if (type == "poly") {
                temp = start_temp / std::pow(k, 0.8);
            } else if (type == "step") {
                if (k % 5 == 0) {
                    temp *= cooling_rate;
                }
            }
        }

        //remove_not_needed();
        if (check()) {
            return ds.size();
        } else {
            return -1; // -1 indicates "NOT DS"
        }
    }

    bool check() {
        for (int i = 1; i <= n; ++i) {
            if (ds.find(i) == ds.end()) {
                bool flag = true;
                AdjacencyIterator ai, a_end;
                for (tie(ai, a_end) = adjacent_vertices(vertex(i, g), g); ai != a_end; ++ai) {
                    if (ds.find(*ai) != ds.end()) {
                        flag = false;
                        break;
                    }
                }
                if (flag) {
                    return false;
                }
            }
        }
        return true;
    }

    int get_size() {
        return ds.size();
    }

    void remove_not_needed() {
        std::vector<int> to_remove;

        for (int ver : ds) {
            bool has_neig_in_ds = false;
            bool all_neig_are_covered = true;

            AdjacencyIterator ai, a_end;
            for (tie(ai, a_end) = adjacent_vertices(vertex(ver, g), g); ai != a_end; ++ai) {
                int neig = *ai;
                if (neig == ver) continue;

                if (ds.find(neig) != ds.end()) {
                    has_neig_in_ds = true;
                } else {
                    bool covered = false;
                    AdjacencyIterator ai2, a_end2;
                    for (tie(ai2, a_end2) = adjacent_vertices(vertex(neig, g), g); ai2 != a_end2; ++ai2) {
                        int neig_neig = *ai2;
                        if (neig_neig == ver || neig_neig == neig) continue;

                        if (ds.find(neig_neig) != ds.end()) {
                            covered = true;
                            break;
                        }
                    }
                    if (!covered) {
                        all_neig_are_covered = false;
                    }
                }
            }

            if (has_neig_in_ds && all_neig_are_covered) {
                to_remove.push_back(ver);
            }
        }

        for (int ver : to_remove) {
            ds.erase(ver);
        }
    }

private:
    // Placeholder for approximation functions - these would need to be implemented
    void approx_ln_ds(const Graph& g) {
        const int n = num_vertices(g);
        ds = {};
        std::vector<bool> dominated(n + 1, false);
        std::vector<bool> active(n + 1, true);
        std::vector<int> degrees(n + 1, 0);

        // Priority queue: (degree, vertex) pairs
        using VertexPriority = std::pair<int, Vertex>;
        std::priority_queue<VertexPriority> max_heap;

        // Initialize degrees and heap
        VertexIterator vi, vi_end;
        for (tie(vi, vi_end) = vertices(g); vi != vi_end; ++vi) {
            Vertex v = *vi;
            if (v == 0) {
                continue;
            }
            degrees[v] = out_degree(v, g);
            max_heap.emplace(degrees[v], v);
        }

        while (!max_heap.empty()) {
            auto [current_degree, v] = max_heap.top();
            max_heap.pop();

            // Skip if no longer active or degree is stale
            if (!active[v] || degrees[v] != current_degree) {
                continue;
            }

            // Skip if degree is 0 (isolated vertex)
            if (current_degree <= 0) {
                break;
            }

            // Add to dominating set
            ds.insert(v);
            dominated[v] = true;
            active[v] = false;

            // Process neighbors
            AdjacencyIterator ai, ai_end;
            for (tie(ai, ai_end) = adjacent_vertices(v, g); ai != ai_end; ++ai) {
                Vertex neighbor = *ai;
                if (active[neighbor]) {
                    dominated[neighbor] = true;
                    active[neighbor] = false;

                    // Update degrees of neighbor's neighbors
                    AdjacencyIterator ai2, ai2_end;
                    for (tie(ai2, ai2_end) = adjacent_vertices(neighbor, g); ai2 != ai2_end; ++ai2) {
                        Vertex neighbor_neighbor = *ai2;
                        if (active[neighbor_neighbor]) {
                            degrees[neighbor_neighbor]--;
                            max_heap.emplace(degrees[neighbor_neighbor], neighbor_neighbor);
                        }
                    }
                }
            }
        }

        // Add remaining isolated nodes
        for (Vertex v = 1; v <= n; ++v) {
            if (!dominated[v]) {
                ds.insert(v);
            }
        }
    }

    std::unordered_set<int> approx_2_ds(const Graph& g) {
        // Implement 2 approximation
        return {};
    }

    std::unordered_set<int> approx_greedy_ds(const Graph& g) {
        // Implement greedy approximation
        return {};
    }
};
