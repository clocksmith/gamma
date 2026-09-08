#pragma once

#ifndef FX3_PROFILE_TIMERS
#define FX3_PROFILE_TIMERS 0
#endif

#if FX3_PROFILE_TIMERS

#include <cstdlib>
#include <cstdio>
#include <ctime>

namespace fx3_profile {

struct Counter {
  const char* name;
  unsigned long long calls;
  unsigned long long total_ns;
  Counter* next;

  explicit Counter(const char* label)
      : name(label), calls(0), total_ns(0), next(Head()) {
    Head() = this;
    RegisterDump();
  }

  static Counter*& Head() {
    static Counter* head = nullptr;
    return head;
  }

  static void Dump() {
    std::fprintf(stderr, "\nFX3_PROFILE_TIMER_SUMMARY_BEGIN\n");
    std::fprintf(stderr, "label\tcalls\ttotal_ns\tavg_ns\n");
    for (Counter* c = Head(); c != nullptr; c = c->next) {
      const unsigned long long avg = c->calls ? c->total_ns / c->calls : 0;
      std::fprintf(stderr, "%s\t%llu\t%llu\t%llu\n", c->name, c->calls,
                   c->total_ns, avg);
    }
    std::fprintf(stderr, "FX3_PROFILE_TIMER_SUMMARY_END\n");
  }

  static void RegisterDump() {
    static bool registered = []() {
      std::atexit(Dump);
      return true;
    }();
    (void)registered;
  }
};

inline unsigned long long NowNs() {
  timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return static_cast<unsigned long long>(ts.tv_sec) * 1000000000ull +
         static_cast<unsigned long long>(ts.tv_nsec);
}

struct Scope {
  Counter& counter;
  unsigned long long start_ns;

  explicit Scope(Counter& c) : counter(c), start_ns(NowNs()) {}

  ~Scope() {
    counter.total_ns += NowNs() - start_ns;
    ++counter.calls;
  }
};

}  // namespace fx3_profile

#define FX3_PROFILE_CONCAT_INNER(a, b) a##b
#define FX3_PROFILE_CONCAT(a, b) FX3_PROFILE_CONCAT_INNER(a, b)
#define FX3_PROFILE_SCOPE(label)                                                \
  static ::fx3_profile::Counter FX3_PROFILE_CONCAT(fx3_profile_counter_,        \
                                                   __LINE__)(label);            \
  ::fx3_profile::Scope FX3_PROFILE_CONCAT(fx3_profile_scope_, __LINE__)(        \
      FX3_PROFILE_CONCAT(fx3_profile_counter_, __LINE__))

#else

#define FX3_PROFILE_SCOPE(label) ((void)0)

#endif
