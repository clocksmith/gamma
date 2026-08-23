#ifndef WIKI_PDA_OVERLAY_H
#define WIKI_PDA_OVERLAY_H

#include <array>
#include <cstddef>
#include <cstdint>

class WikiPdaOverlay {
 public:
  enum class Arm : unsigned char {
    PARENT = 0,
    BOOKKEEPING = 1,
    DIRECT = 2,
    RANDOM_PERMUTATION = 3,
    SHIFTED = 4
  };

  WikiPdaOverlay();

  void Observe(unsigned char byte);
  bool NextPrediction(unsigned char* expected, float* probability) const;
  std::uint64_t StateDigest() const;
  Arm arm() const { return arm_; }

 private:
  static const std::size_t kMaxDepth = 16;
  static const std::size_t kMaxName = 64;
  static const std::size_t kStatBuckets = 16;

  struct Name {
    std::array<unsigned char, kMaxName> bytes;
    unsigned char length;
    bool valid;
  };

  enum class Mode : unsigned char {
    OUTSIDE,
    AFTER_LT,
    OPEN_NAME,
    OPEN_REST,
    CLOSE_NAME,
    CLOSE_REST,
    IGNORED_TAG
  };

  static bool IsSpace(unsigned char byte);
  static bool NamesEqual(const Name& left, const Name& right);
  static void ClearName(Name* name);
  static void AppendNameByte(Name* name, unsigned char byte);

  void ResetParser();
  bool TrackLine(unsigned char byte);
  void ParseByte(unsigned char byte);
  void PushOpeningName();
  void FinishClosingName();
  void BeginClosingReplay();
  void PrepareNextReplay();
  void BuildRandomPermutation();
  void UpdatePriorTrial(unsigned char actual);
  float ReplayProbability() const;
  void HashByte(std::uint64_t* hash, unsigned char value) const;
  void HashU32(std::uint64_t* hash, std::uint32_t value) const;

  Arm arm_;
  Mode mode_;
  std::array<Name, kMaxDepth> stack_;
  std::size_t depth_;
  Name current_name_;
  unsigned char quote_;
  unsigned char last_nonspace_;

  std::size_t close_position_;
  std::array<unsigned char, kMaxName> random_order_;
  bool next_valid_;
  unsigned char next_truth_;
  unsigned char next_arm_;
  unsigned char next_bucket_;

  std::array<std::uint32_t, kStatBuckets> correct_;
  std::array<std::uint32_t, kStatBuckets> total_;

  std::array<unsigned char, 4> line_prefix_;
  std::size_t line_length_;
};

#endif
