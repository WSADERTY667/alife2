#include <iostream>
#include <string>
#include <optional>
#include "alife/version.h"

void print_help(const std::string& program_name) {
    std::cout << "Usage: " << program_name << " [OPTIONS]\n"
        << "\n"
        << "ALife Headless Simulation Stub\n"
        << "\n"
        << "Options:\n"
        << "  --help       Show this help message and exit\n"
        << "  --seed <N>   Set random seed (default: 42)\n"
        << "  --ticks <N>  Set number of simulation ticks (default: 100)\n"
        << "  --agents <N> Set number of agents (default: 50)\n"
        << "  --food <N>   Set initial food amount (default: 100)\n"
        << "  --out <PATH> Set output file path (default: stdout)\n"
        << "\n"
        << "Version: " << alife::get_version() << "\n";
}

struct Config {
    std::optional<int> seed;
    std::optional<int> ticks;
    std::optional<int> agents;
    std::optional<int> food;
    std::optional<std::string> out;
};

bool parse_args(int argc, char* argv[], Config& config) {
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];

        if (arg == "--help") {
            return false; // Show help
        }

        if (i + 1 >= argc) {
            std::cerr << "Error: Option '" << arg << "' requires an argument\n";
            return false;
        }

        std::string value = argv[++i];

        if (arg == "--seed") {
            config.seed = std::stoi(value);
        }
        else if (arg == "--ticks") {
            config.ticks = std::stoi(value);
        }
        else if (arg == "--agents") {
            config.agents = std::stoi(value);
        }
        else if (arg == "--food") {
            config.food = std::stoi(value);
        }
        else if (arg == "--out") {
            config.out = value;
        }
        else {
            std::cerr << "Error: Unknown option '" << arg << "'\n";
            return false;
        }
    }
    return true;
}

int main(int argc, char* argv[]) {
    Config config;

    if (!parse_args(argc, argv, config)) {
        print_help(argv[0]);
        return 0;
    }

    // Print configuration (stub - no actual simulation)
    std::cout << "ALife Headless Simulation (stub)\n";
    std::cout << "Version: " << alife::get_version() << "\n";

    if (config.seed.has_value()) {
        std::cout << "Seed: " << config.seed.value() << "\n";
    }
    if (config.ticks.has_value()) {
        std::cout << "Ticks: " << config.ticks.value() << "\n";
    }
    if (config.agents.has_value()) {
        std::cout << "Agents: " << config.agents.value() << "\n";
    }
    if (config.food.has_value()) {
        std::cout << "Food: " << config.food.value() << "\n";
    }
    if (config.out.has_value()) {
        std::cout << "Output: " << config.out.value() << "\n";
    }

    std::cout << "Simulation not implemented (stub).\n";

    return 0;
}