// brain.cpp
// Спайковая нейронная сеть (SNN) агента - реализация
#include "alife/brain.h"
#include "alife/math_utils.h"
#include <cmath>
#include <stdexcept>

namespace alife {

Brain::Brain(
    const Genome& genome,
    std::optional<int> n_hidden_opt,
    const std::optional<std::vector<double>>& parent_weights,
    RNG* rng
) : rng_(rng ? rng : &default_rng_),
    n_in(DEFAULT_INPUT_SIZE),
    n_out(DEFAULT_OUTPUT_SIZE),
    n_hidden(n_hidden_opt.value_or(DEFAULT_N_HIDDEN)),
    n(n_in + n_hidden + n_out),
    decay_base(genome.get("membrane_decay", 0.85)),
    threshold_base(genome.get("threshold", 1.0)),
    stdp_rate(genome.get("stdp_rate", 0.01)),
    max_w(genome.get("weight_max", 2.0)),
    learning(true)
{
    // Инициализация массивов
    v.assign(n, 0.0);
    spikes.assign(n, 0.0);
    out_rate.assign(n_out, 0.0);
    
    // Маска связей и веса
    size_t total_size = static_cast<size_t>(n) * static_cast<size_t>(n);
    mask.assign(total_size, false);
    W.assign(total_size, 0.0);
    
    // Генерация маски соединений
    double conn_prob = genome.get("conn_prob", 0.1);
    double weight_scale = genome.get("weight_scale", 0.5);
    
    // Основная маска соединений
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            if (i == j) continue;  // Диагональ всегда False
            
            if (rng_->next_float() < conn_prob) {
                mask[idx(i, j)] = true;
                W[idx(i, j)] = rng_->gauss(0.0, weight_scale);
            }
        }
    }
    
    // Усиленные связи от входов
    double in_conn_prob = std::max(conn_prob, 0.12);
    for (int i = 0; i < n_in; ++i) {
        for (int j = 0; j < n; ++j) {
            if (rng_->next_float() < in_conn_prob) {
                mask[idx(i, j)] = true;
                if (W[idx(i, j)] == 0.0) {
                    W[idx(i, j)] = rng_->gauss(0.0, weight_scale);
                }
            }
        }
    }
    
    // Усиленные связи к выходам
    double out_conn_prob = std::max(conn_prob, 0.15);
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n_out; ++j) {
            int col = n - n_out + j;
            if (rng_->next_float() < out_conn_prob) {
                mask[idx(i, col)] = true;
                if (W[idx(i, col)] == 0.0) {
                    W[idx(i, col)] = rng_->gauss(0.0, weight_scale);
                }
            }
        }
    }
    
    // Снова обнуляем диагональ
    for (int i = 0; i < n; ++i) {
        mask[idx(i, i)] = false;
        W[idx(i, i)] = 0.0;
    }
    
    // Наследование родительских весов
    if (parent_weights.has_value() && 
        parent_weights->size() == total_size) {
        double lamarckian = clamp(
            genome.get("lamarckian_weight", 0.0),
            0.0, 1.0
        );
        
        for (size_t i = 0; i < total_size; ++i) {
            W[i] = ((1.0 - lamarckian) * W[i] + lamarckian * (*parent_weights)[i]);
            if (!mask[i]) {
                W[i] = 0.0;
            }
        }
    }
    
    // Eligibility trace только если обучение включено
    int total_neurons = n_in + n_hidden + n_out;
    if (learning && total_neurons <= 1200) {
        E.assign(total_size, 0.0);
    } else {
        learning = false;
        E.clear();
    }
}

std::vector<double> Brain::step(
    const std::vector<double>& sensors,
    const std::map<std::string, double>& mod
) {
    // Проверка размера сенсоров
    if (sensors.size() != static_cast<size_t>(n_in)) {
        throw std::invalid_argument(
            "Ожидается " + std::to_string(n_in) + " сенсоров, получено " + 
            std::to_string(sensors.size())
        );
    }
    
    // pre = spikes (предыдущие спайки)
    std::vector<double> pre = spikes;
    
    // current = pre @ W (матричное умножение)
    std::vector<double> current(n, 0.0);
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            current[i] += pre[j] * W[idx(j, i)];
        }
    }
    
    // Получение модуляторов
    double arousal = 0.0;
    auto it_arousal = mod.find("arousal");
    if (it_arousal != mod.end()) {
        arousal = it_arousal->second;
    }
    
    double plasticity = 0.0;
    auto it_plasticity = mod.find("plasticity");
    if (it_plasticity != mod.end()) {
        plasticity = it_plasticity->second;
    }
    
    double dopamine = 0.0;
    auto it_dopamine = mod.find("dopamine");
    if (it_dopamine != mod.end()) {
        dopamine = it_dopamine->second;
    }
    
    // Вычисление затухания и порога с учётом arousal
    double decay = clamp(decay_base + arousal * 0.02, 0.50, 0.99);
    double threshold = clamp(threshold_base - arousal * 0.05, 0.30, 2.0);
    
    // Обновление мембранного потенциала
    for (int i = 0; i < n; ++i) {
        v[i] = v[i] * decay + current[i] * DEFAULT_SYNAPTIC_SCALE;
    }
    
    // Добавление шума при высоком arousal
    if (arousal > 0.8) {
        double noise_std = (arousal - 0.8) * 0.02;
        for (int i = n_in; i < n; ++i) {
            v[i] += rng_->gauss(0.0, noise_std);
        }
    }
    
    // Генерация новых спайков
    std::vector<double> new_spikes(n, 0.0);
    
    // Скрытые нейроны: проверка порога
    int hidden_start = n_in;
    int hidden_end = n_in + n_hidden;
    for (int i = hidden_start; i < hidden_end; ++i) {
        if (v[i] >= threshold) {
            new_spikes[i] = 1.0;
            v[i] = 0.0;  // Сброс после спайка
        }
    }
    
    // Входные нейроны: просто копируем сенсоры
    for (int i = 0; i < n_in; ++i) {
        new_spikes[i] = clamp(sensors[i], 0.0, 1.0);
    }
    
    // Выходные rates: экспоненциальное скользящее среднее
    for (int i = 0; i < n_out; ++i) {
        int spike_idx = n - n_out + i;
        out_rate[i] = 0.75 * out_rate[i] + 0.25 * new_spikes[spike_idx];
    }
    
    // STDP обучение
    if (learning && !E.empty()) {
        double learn_rate = clamp(plasticity * dopamine, -2.0, 2.0);
        
        if (std::abs(learn_rate) > 1e-6) {
            std::vector<double> post = new_spikes;
            
            // Вычисление delta = outer(pre, post) - outer(post, pre)
            // и обновление eligibility trace
            for (int i = 0; i < n; ++i) {
                for (int j = 0; j < n; ++j) {
                    double delta = pre[i] * post[j] - post[i] * pre[j];
                    E[idx(i, j)] = E[idx(i, j)] * 0.95 + delta * stdp_rate;
                }
            }
            
            // Обновление весов
            for (size_t i = 0; i < W.size(); ++i) {
                W[i] += learn_rate * E[i] * (mask[i] ? 1.0 : 0.0);
                W[i] = clamp(W[i], -max_w, max_w);
                if (!mask[i]) {
                    W[i] = 0.0;
                }
            }
        }
    }
    
    // Сохранение новых спайков
    spikes = new_spikes;
    
    return out_rate;
}

} // namespace alife
