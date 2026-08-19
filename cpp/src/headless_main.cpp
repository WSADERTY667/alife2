#include <iostream>
#include <string>
#include <optional>
#include "alife/version.h"
#include "alife/world.h"

void print_help(const std::string& program_name) {
    std::cout << "Usage: " << program_name << " [OPTIONS]\n"
        << "\n"
        << "ALife Headless Simulation\n"
        << "\n"
        << "Options:\n"
        << "  --help       Show this help message and exit\n"
        << "  --seed <N>   Set random seed (default: 42)\n"
        << "  --ticks <N>  Set number of simulation ticks (default: 100)\n"
        << "  --agents <N> Set number of agents (default: 24)\n"
        << "  --food <N>   Set initial food amount (default: 90)\n"
        << "  --out <PATH> Set output file path (default: stdout)\n"
        << "\n"
        << "Version: " << alife::get_version() << "\n";
}

struct Config {
    int seed = 42;
    int ticks = 100;
    int agents = 24;
    int food = 90;
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

    // Создание мира с заданными параметрами
    alife::World world(
        static_cast<uint64_t>(config.seed),
        config.agents,
        config.food
    );

    // Запуск симуляции
    for (int t = 0; t < config.ticks; ++t) {
        world.update();
        
        // Проверка на NaN в энергии агентов
        for (const auto& agent : world.get_agents()) {
            if (std::isnan(agent.energy) || std::isinf(agent.energy)) {
                std::cerr << "Error: NaN/Inf detected in agent energy at tick " << t << "\n";
                return 1;
            }
        }
    }

    // Вывод результата в JSON
    std::string json_output = world.to_json(config.out);
    
    if (!config.out.has_value()) {
        std::cout << json_output;
    } else {
        std::cout << "Simulation completed. Output saved to: " << config.out.value() << "\n";
        std::cout << "Final tick: " << world.get_tick() << "\n";
        std::cout << "Final agent count: " << world.get_agent_count() << "\n";
        std::cout << "Final food count: " << world.get_food_count() << "\n";
    }

    return 0;
}