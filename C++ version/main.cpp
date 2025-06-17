#include <iostream>
#include <fstream>
#include <string>
#include <boost/graph/adjacency_list.hpp>
#include <vector>
#include <filesystem>
#include "annealing.cpp"

using namespace std;
using namespace boost;
namespace fs = std::filesystem;

typedef adjacency_list<vecS, vecS, undirectedS> Graph;

// Using unique_ptr to ensure graph ownership is transferred
void read_dimacs(Graph& g, const std::string& filename) {
    fs::path file_path(filename);
    if (!fs::exists(file_path)) {
        file_path = fs::absolute(file_path);
        if (!fs::exists(file_path)) {
            throw std::runtime_error("File not found: " + file_path.string());
        }
    }

    std::ifstream f(file_path);
    if (!f.is_open()) {
        throw std::runtime_error("Failed to open file: " + file_path.string());
    }

    std::string line;
    int vertices = 0, edges = 0;

    // Skip comments
    while (std::getline(f, line) && line[0] == 'c') {}

    // Parse problem line
    if (line.empty() || line[0] != 'p') {
        throw std::runtime_error("Invalid DIMACS format");
    }

    std::istringstream iss(line);
    std::string p, problem;
    iss >> p >> problem >> vertices >> edges;

    // Clear and resize graph
    g.clear();
    for (int i = 0; i < vertices + 1; ++i) {  // +1 for 1-based indexing
        boost::add_vertex(g);
    }

    // Read edges
    for (int i = 0; i < edges; ++i) {
        if (!std::getline(f, line)) break;

        std::istringstream edge_iss(line);
        int u, v;
        edge_iss >> u >> v;

        if (u > 0 && u <= vertices && v > 0 && v <= vertices) {
            boost::add_edge(u, v, g);
        }
    }
}

bool compare_graph_files(const fs::directory_entry& a, const fs::directory_entry& b) {
    std::string a_num = a.path().stem().string().substr(10); // Extract number after "heuristic_"
    std::string b_num = b.path().stem().string().substr(10);
    return std::stoi(a_num) < std::stoi(b_num);
}

void process_all_graphs(const std::string& input_dir, const std::string& output_file) {
    std::ofstream out(output_file);
    if (!out.is_open()) {
        std::cerr << "Failed to open output file: " << output_file << std::endl;
        return;
    }

    std::vector<fs::directory_entry> graph_files;
    for (const auto& entry : fs::directory_iterator(input_dir)) {
        if (entry.path().extension() == ".gr" &&
            entry.path().stem().string().find("heuristic_") == 0) {
            graph_files.push_back(entry);
        }
    }
    std::sort(graph_files.begin(), graph_files.end(), compare_graph_files);

    for (const auto& entry : graph_files) {
        if (entry.path().extension() != ".gr") continue;

        const std::string graph_path = entry.path().string();
        const std::string graph_name = entry.path().stem().string();
        if (graph_name < "heuristic_080") {
            continue;
        }

        try {
            Graph g;
            read_dimacs(g, graph_path);

            DSAnnealing annealer(g);
            double result = annealer.annealing("poly");

            // Simple space-separated output: GraphName FinalSize
            out << graph_name << " " << result << "\n";
            std::cout << graph_name << " " << result << std::endl;  // Also print to console

        } catch (const std::exception& e) {
            std::cerr << "Error processing " << graph_name << ": " << e.what() << std::endl;
            out << graph_name << " ERROR\n";
        }
    }

    std::cout << "\nResults saved to: " << output_file << std::endl;
}


int main() {
    process_all_graphs("/home/mikhail/CLionProjects/untitled/heuristic_graphs", "results.txt");
    return 0;
}