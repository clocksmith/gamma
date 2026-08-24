  // Review-only v4 midpoint oracle extension. P is a compile/runtime no-op;
  // K executes the complete local update against detached state and must
  // reconstruct the parent's recurrent state bit-for-bit; F commits aligned
  // causal targets; S changes only their 16-position association.
  enum MidpointArm : unsigned char {
    kMidpointParent = 0,
    kMidpointKernelIdentity = 1,
    kMidpointForward = 2,
    kMidpointShifted = 3
  };

  static const unsigned int kMidpointRows = 32;
  static const unsigned int kMidpointSegment = 64;

  void InitMidpointOracle();
  void MidpointBeginSegment();
  int MidpointBeginCapture(unsigned int input);
  void MidpointFinishCapture(unsigned int local);
  bool MidpointApplyClosure();
  void MidpointBuildOutputAdjoints();
  void MidpointApplyOutputUpdate(bool commit);
  void MidpointReplayWindow();
  void MidpointClearScratch();
  [[noreturn]] void MidpointAbort(const char* reason) const;

  float* MidpointAuxRow(unsigned int local);
  float* MidpointProbabilityRow(unsigned int local);
  float* MidpointFeatureRow(unsigned int local);
  float* MidpointErrorRow(unsigned int local);
  float* MidpointAdjointRow(unsigned int local);
  float* MidpointPendingRow(unsigned int phase);
  float* MidpointReplayInput(unsigned int layer);

  MidpointArm midpoint_arm_ = kMidpointParent;
  unsigned int midpoint_segment_start_ = 0;
  unsigned int midpoint_captured_rows_ = 0;
  unsigned long long midpoint_modeled_events_ = 0;
  bool midpoint_segment_active_ = false;
  bool midpoint_preserve_pending_feature_ = false;
  std::vector<unsigned int> midpoint_symbols_;
  std::vector<unsigned int> midpoint_targets_;
  LstmFloatBuf midpoint_start_hidden_, midpoint_closure_hidden_;
  LstmFloatBuf midpoint_auxiliary_, midpoint_probability_;
  LstmFloatBuf midpoint_feature_, midpoint_error_, midpoint_adjoint_;
  LstmFloatBuf midpoint_pending_, midpoint_replay_input_;
  LstmFloatBuf midpoint_output_gradient_, midpoint_output_detached_;
  LstmHalfBuf midpoint_output_detached_h_;
  volatile unsigned long long midpoint_detached_sink_ = 0;
