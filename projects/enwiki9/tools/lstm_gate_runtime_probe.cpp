// Runtime probe for stream-preserving LSTM gate scheduling alternatives.

#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <iomanip>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

#include <omp.h>

namespace {

struct State {
  std::array<std::vector<float>, 3> weights;
  std::array<std::vector<float>, 3> norm;
  std::array<std::vector<float>, 3> gate;
  std::array<std::vector<float>, 3> gamma;
  std::array<std::vector<float>, 3> beta;
  std::vector<float> input;
  std::vector<float> cell;
  std::vector<float> hidden;
};

float Logistic(float value) {
  return 1.0f / (1.0f + std::exp(-value));
}

State MakeState(unsigned int cells, unsigned int inputs) {
  std::mt19937 generator(0x5eeda11u);
  std::uniform_real_distribution<float> weight(-0.08f, 0.08f);
  std::uniform_real_distribution<float> input(-1.0f, 1.0f);
  State state;
  for (unsigned int gate = 0; gate < 3; ++gate) {
    state.weights[gate].resize(static_cast<std::size_t>(cells) * inputs);
    state.norm[gate].resize(cells);
    state.gate[gate].resize(cells);
    state.gamma[gate].assign(cells, 1.0f);
    state.beta[gate].assign(cells, 0.0f);
    for (float& value : state.weights[gate]) value = weight(generator);
  }
  state.input.resize(inputs);
  for (float& value : state.input) value = input(generator);
  state.cell.resize(cells);
  for (float& value : state.cell) value = input(generator) * 0.25f;
  state.hidden.resize(cells);
  return state;
}

void DotCells(State* state, unsigned int cells, unsigned int inputs,
              unsigned int threads) {
#pragma omp parallel for num_threads(threads) schedule(static)
  for (unsigned int cell = 0; cell < cells; ++cell) {
    std::array<float, 3> sum{};
    for (unsigned int column = 0; column < inputs; ++column) {
      const float value = state->input[column];
      const std::size_t index = static_cast<std::size_t>(cell) * inputs + column;
      for (unsigned int gate = 0; gate < 3; ++gate) {
        sum[gate] += value * state->weights[gate][index];
      }
    }
    for (unsigned int gate = 0; gate < 3; ++gate) {
      state->norm[gate][cell] = sum[gate];
    }
  }
}

std::array<float, 3> InverseVariance(const State& state, unsigned int cells) {
  std::array<float, 3> inverse{};
  for (unsigned int gate = 0; gate < 3; ++gate) {
    float squares = 0.0f;
    for (unsigned int cell = 0; cell < cells; ++cell) {
      squares += state.norm[gate][cell] * state.norm[gate][cell];
    }
    inverse[gate] = 1.0f / std::sqrt(squares / cells + 1e-5f);
  }
  return inverse;
}

void TransformCell(State* state, const std::array<float, 3>& inverse,
                   unsigned int cell) {
  for (unsigned int gate = 0; gate < 3; ++gate) {
    const float normalized = state->norm[gate][cell] * inverse[gate];
    const float affine = normalized * state->gamma[gate][cell] +
        state->beta[gate][cell];
    state->gate[gate][cell] = gate == 1 ? std::tanh(affine) : Logistic(affine);
  }
  const float forget = state->gate[0][cell];
  state->cell[cell] *= forget;
  state->cell[cell] += state->gate[1][cell] * (1.0f - forget);
  state->hidden[cell] = state->gate[2][cell] * std::tanh(state->cell[cell]);
}

void CurrentStep(State* state, unsigned int cells, unsigned int inputs,
                 unsigned int threads) {
  DotCells(state, cells, inputs, threads);
  const auto inverse = InverseVariance(*state, cells);
  for (unsigned int cell = 0; cell < cells; ++cell) {
    TransformCell(state, inverse, cell);
  }
}

void PersistentStep(State* state, unsigned int cells, unsigned int inputs,
                    unsigned int threads) {
  std::array<float, 3> inverse{};
#pragma omp parallel num_threads(threads)
  {
#pragma omp for schedule(static)
    for (unsigned int cell = 0; cell < cells; ++cell) {
      std::array<float, 3> sum{};
      for (unsigned int column = 0; column < inputs; ++column) {
        const float value = state->input[column];
        const std::size_t index =
            static_cast<std::size_t>(cell) * inputs + column;
        for (unsigned int gate = 0; gate < 3; ++gate) {
          sum[gate] += value * state->weights[gate][index];
        }
      }
      for (unsigned int gate = 0; gate < 3; ++gate) {
        state->norm[gate][cell] = sum[gate];
      }
    }
#pragma omp single
    { inverse = InverseVariance(*state, cells); }
#pragma omp for schedule(static)
    for (unsigned int cell = 0; cell < cells; ++cell) {
      TransformCell(state, inverse, cell);
    }
  }
}

void SerialStep(State* state, unsigned int cells, unsigned int inputs) {
  for (unsigned int cell = 0; cell < cells; ++cell) {
    std::array<float, 3> sum{};
    for (unsigned int column = 0; column < inputs; ++column) {
      const float value = state->input[column];
      const std::size_t index = static_cast<std::size_t>(cell) * inputs + column;
      for (unsigned int gate = 0; gate < 3; ++gate) {
        sum[gate] += value * state->weights[gate][index];
      }
    }
    for (unsigned int gate = 0; gate < 3; ++gate) {
      state->norm[gate][cell] = sum[gate];
    }
  }
  const auto inverse = InverseVariance(*state, cells);
  for (unsigned int cell = 0; cell < cells; ++cell) {
    TransformCell(state, inverse, cell);
  }
}

bool Identical(const State& left, const State& right) {
  for (unsigned int gate = 0; gate < 3; ++gate) {
    if (left.norm[gate].size() != right.norm[gate].size() ||
        std::memcmp(left.norm[gate].data(), right.norm[gate].data(),
                    left.norm[gate].size() * sizeof(float)) != 0 ||
        std::memcmp(left.gate[gate].data(), right.gate[gate].data(),
                    left.gate[gate].size() * sizeof(float)) != 0) {
      return false;
    }
  }
  return std::memcmp(left.cell.data(), right.cell.data(),
                     left.cell.size() * sizeof(float)) == 0 &&
      std::memcmp(left.hidden.data(), right.hidden.data(),
                  left.hidden.size() * sizeof(float)) == 0;
}

std::uint64_t Checksum(const State& state) {
  std::uint64_t hash = 1469598103934665603ULL;
  const auto append = [&hash](const std::vector<float>& values) {
    const auto* bytes = reinterpret_cast<const unsigned char*>(values.data());
    for (std::size_t index = 0; index < values.size() * sizeof(float); ++index) {
      hash ^= bytes[index];
      hash *= 1099511628211ULL;
    }
  };
  append(state.cell);
  append(state.hidden);
  return hash;
}

template <typename Step>
double Measure(const State& seed, unsigned int iterations, Step step,
               std::uint64_t* checksum) {
  State state = seed;
  const auto start = std::chrono::steady_clock::now();
  for (unsigned int iteration = 0; iteration < iterations; ++iteration) {
    step(&state);
  }
  const auto end = std::chrono::steady_clock::now();
  *checksum = Checksum(state);
  return std::chrono::duration<double>(end - start).count();
}

unsigned int Argument(char** argv, int index) {
  const unsigned long value = std::stoul(argv[index]);
  if (value == 0 || value > 1'000'000) {
    throw std::runtime_error("arguments must be in [1, 1000000]");
  }
  return static_cast<unsigned int>(value);
}

}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc != 5) {
      throw std::runtime_error(
          "usage: lstm_gate_runtime_probe CELLS INPUTS ITERATIONS THREADS");
    }
    const unsigned int cells = Argument(argv, 1);
    const unsigned int inputs = Argument(argv, 2);
    const unsigned int iterations = Argument(argv, 3);
    const unsigned int threads = Argument(argv, 4);
    const State seed = MakeState(cells, inputs);

    State current = seed;
    State persistent = seed;
    State serial = seed;
    CurrentStep(&current, cells, inputs, threads);
    PersistentStep(&persistent, cells, inputs, threads);
    SerialStep(&serial, cells, inputs);
    const bool persistent_identity = Identical(current, persistent);
    const bool serial_identity = Identical(current, serial);

    std::uint64_t current_checksum = 0;
    std::uint64_t persistent_checksum = 0;
    std::uint64_t serial_checksum = 0;
    const double current_seconds = Measure(
        seed, iterations,
        [&](State* state) { CurrentStep(state, cells, inputs, threads); },
        &current_checksum);
    const double persistent_seconds = Measure(
        seed, iterations,
        [&](State* state) { PersistentStep(state, cells, inputs, threads); },
        &persistent_checksum);
    const double serial_seconds = Measure(
        seed, iterations,
        [&](State* state) { SerialStep(state, cells, inputs); },
        &serial_checksum);

    std::cout << std::fixed << std::setprecision(9)
              << "{\n"
              << "  \"schema\": \"lstm_gate_runtime_probe_v1\",\n"
              << "  \"cells\": " << cells << ",\n"
              << "  \"inputs\": " << inputs << ",\n"
              << "  \"iterations\": " << iterations << ",\n"
              << "  \"threads\": " << threads << ",\n"
              << "  \"persistent_step_identity\": "
              << (persistent_identity ? "true" : "false") << ",\n"
              << "  \"serial_step_identity\": "
              << (serial_identity ? "true" : "false") << ",\n"
              << "  \"current_seconds\": " << current_seconds << ",\n"
              << "  \"persistent_seconds\": " << persistent_seconds << ",\n"
              << "  \"serial_seconds\": " << serial_seconds << ",\n"
              << "  \"persistent_speedup\": "
              << current_seconds / persistent_seconds << ",\n"
              << "  \"serial_speedup\": " << current_seconds / serial_seconds
              << ",\n"
              << "  \"current_checksum\": " << current_checksum << ",\n"
              << "  \"persistent_checksum\": " << persistent_checksum << ",\n"
              << "  \"serial_checksum\": " << serial_checksum << "\n"
              << "}\n";
    return persistent_identity && serial_identity ? 0 : 2;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
