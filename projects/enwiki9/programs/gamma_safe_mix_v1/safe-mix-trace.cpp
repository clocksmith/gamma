#include "safe-mix.h"

#include <cerrno>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>

namespace {

const unsigned int kMaximumEvents = 65536;

bool Consume(const char** cursor, const char* literal) {
  const std::size_t length = std::strlen(literal);
  if (std::strncmp(*cursor, literal, length) != 0) return false;
  *cursor += length;
  return true;
}

bool ParseUint32(const char** cursor, std::uint32_t* output) {
  if (**cursor < '0' || **cursor > '9') return false;
  errno = 0;
  char* end = 0;
  const unsigned long long value = std::strtoull(*cursor, &end, 10);
  if (errno != 0 || end == *cursor ||
      value > std::numeric_limits<std::uint32_t>::max()) {
    return false;
  }
  *cursor = end;
  *output = static_cast<std::uint32_t>(value);
  return true;
}

bool ParseRow(
    const char* line,
    std::uint32_t* parent_count,
    std::uint32_t* scale,
    std::uint32_t* treatment_count,
    bool* truth) {
  const char* cursor = line;
  if (!Consume(&cursor, "{\"parent_count\":")) return false;
  if (!ParseUint32(&cursor, parent_count)) return false;
  if (!Consume(&cursor, ",\"scale\":")) return false;
  if (!ParseUint32(&cursor, scale)) return false;
  if (!Consume(&cursor, ",\"treatment_count\":")) return false;
  if (!ParseUint32(&cursor, treatment_count)) return false;
  if (!Consume(&cursor, ",\"truth\":")) return false;
  if (Consume(&cursor, "true")) {
    *truth = true;
  } else if (Consume(&cursor, "false")) {
    *truth = false;
  } else {
    return false;
  }
  if (!Consume(&cursor, "}")) return false;
  if (*cursor == '\n') ++cursor;
  return *cursor == '\0';
}

int Fail(unsigned int event, const char* reason) {
  std::fprintf(stderr, "safe-mix trace event %u: %s\n", event, reason);
  return 2;
}

}  // namespace

int main() {
  GammaSafeMix mix;
  char line[256];
  unsigned int events = 0;
  std::uint32_t frozen_scale = 0;
  while (std::fgets(line, sizeof(line), stdin) != 0) {
    ++events;
    if (events > kMaximumEvents) return Fail(events, "population ceiling exceeded");
    const std::size_t length = std::strlen(line);
    if (length == 0 || (line[length - 1] != '\n' && !std::feof(stdin))) {
      return Fail(events, "row is empty or exceeds the line ceiling");
    }
    std::uint32_t parent_count = 0;
    std::uint32_t scale = 0;
    std::uint32_t treatment_count = 0;
    bool truth = false;
    if (!ParseRow(line, &parent_count, &scale, &treatment_count, &truth)) {
      return Fail(events, "row violates canonical input grammar");
    }
    if (events == 1) {
      frozen_scale = scale;
      if (!mix.Reset(scale)) return Fail(events, "initialization rejected");
    } else if (scale != frozen_scale) {
      return Fail(events, "probability scale changed");
    }
    std::uint32_t mixed_count = 0;
    if (!mix.MixCount(parent_count, treatment_count, &mixed_count)) {
      return Fail(events, "mix event rejected");
    }
    if (!mix.Observe(truth, parent_count, treatment_count)) {
      return Fail(events, "observation rejected");
    }
    std::printf(
        "{\"mixed_count\":%u,\"parent_weight_after\":%llu}\n",
        mixed_count,
        static_cast<unsigned long long>(mix.parent_weight()));
  }
  if (std::ferror(stdin)) return Fail(events, "input read failed");
  if (events == 0) return Fail(0, "population is empty");
  if (!mix.valid() || mix.event_pending()) return Fail(events, "terminal state is invalid");
  if (std::fflush(stdout) != 0) return Fail(events, "output flush failed");
  return 0;
}
