  // Review-only v4 midpoint oracle extension. This declaration fragment is
  // copied beside lstm-layer.h only after the q1 v3 qualification authority
  // gate passes. It deliberately owns every local-32 history, adjoint,
  // gradient, transpose, replay, and detached-control byte: the ordinary
  // 128-event tape and its optimizer scratch are never borrowed.
  friend class Lstm;

  static const unsigned int kMidpointRows = 32;
  static const unsigned int kMidpointGates = 3;

  void InitMidpointOracle();
  void MidpointCaptureStart();
  void MidpointCaptureRow(unsigned int local, unsigned int absolute_epoch,
      const float* input);
  void MidpointCaptureClosure();
  void MidpointBackward(unsigned int local, int layer, int input_symbol,
      float* hidden_error, bool commit);
  void MidpointRestoreStart();
  void MidpointReplayStateOnly(const float* input, int input_symbol,
      float* hidden, int hidden_start);
  bool MidpointStateEqualsClosure() const;
  void MidpointClearScratch();

  float* MidpointGateError(unsigned int gate, unsigned int local);
  float* MidpointSymbolGradient(unsigned int gate, unsigned int symbol);
  float* MidpointDenseGradient(unsigned int gate, unsigned int cell);
  float* MidpointGammaGradient(unsigned int gate);
  float* MidpointBetaGradient(unsigned int gate);
  float* MidpointTranspose(unsigned int gate, unsigned int row);
  LstmHistElem* MidpointGateState(unsigned int gate, unsigned int local);
  LstmHistElem* MidpointGateNorm(unsigned int gate, unsigned int local);

  LstmFloatBuf midpoint_start_state_, midpoint_closure_state_;
  LstmHistBuf midpoint_tanh_state_, midpoint_input_gate_state_;
  LstmHistBuf midpoint_last_state_, midpoint_input_history_;
  LstmHistBuf midpoint_gate_state_, midpoint_gate_norm_;
  LstmFloatBuf midpoint_ivar_, midpoint_gate_error_;
  LstmFloatBuf midpoint_symbol_gradient_, midpoint_dense_gradient_;
  LstmFloatBuf midpoint_gamma_gradient_, midpoint_beta_gradient_;
  LstmFloatBuf midpoint_temporal_, midpoint_transpose_;
  LstmFloatBuf midpoint_scratch_, midpoint_detached_;
  LstmHalfBuf midpoint_detached_h_;
  volatile unsigned long long midpoint_detached_sink_ = 0;
