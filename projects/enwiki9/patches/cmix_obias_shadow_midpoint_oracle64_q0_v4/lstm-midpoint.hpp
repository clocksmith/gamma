#include <stdio.h>

// Review-only v4 midpoint oracle controller. This file is copied into a new
// content-addressed candidate only after canonical q1 qualification. The
// currently running parent source tree is never edited.

inline float* Lstm::MidpointAuxRow(unsigned int local) {
  return midpoint_auxiliary_.get() + (size_t)local * input_size_;
}

inline float* Lstm::MidpointProbabilityRow(unsigned int local) {
  return midpoint_probability_.get() + (size_t)local * so_;
}

inline float* Lstm::MidpointFeatureRow(unsigned int local) {
  return midpoint_feature_.get() + (size_t)local * soh_;
}

inline float* Lstm::MidpointErrorRow(unsigned int local) {
  return midpoint_error_.get() + (size_t)local * so_;
}

inline float* Lstm::MidpointAdjointRow(unsigned int local) {
  return midpoint_adjoint_.get() + (size_t)local * soh_;
}

inline float* Lstm::MidpointPendingRow(unsigned int phase) {
  return midpoint_pending_.get() + (size_t)phase * so_;
}

inline float* Lstm::MidpointReplayInput(unsigned int layer) {
  return midpoint_replay_input_.get() + (size_t)layer * sli_;
}

[[noreturn]] inline void Lstm::MidpointAbort(const char* reason) const {
  fprintf(stderr, "cmix-midpoint-oracle: %s\n", reason);
  abort();
}

inline void Lstm::InitMidpointOracle() {
  if (horizon_ != 128 || num_layers_ == 0 || output_size_ == 0 ||
      input_size_ == 0 || (horizon_ % kMidpointSegment) != 0) {
    MidpointAbort("sealed parent geometry does not match v4 contract");
  }
  midpoint_symbols_.resize(kMidpointRows);
  midpoint_targets_.resize(kMidpointRows);
  midpoint_start_hidden_ = LstmAllocFloats(soh_);
  midpoint_closure_hidden_ = LstmAllocFloats(soh_);
  midpoint_auxiliary_ =
      LstmAllocFloats((size_t)kMidpointRows * input_size_);
  midpoint_probability_ = LstmAllocFloats((size_t)kMidpointRows * so_);
  midpoint_feature_ = LstmAllocFloats((size_t)kMidpointRows * soh_);
  midpoint_error_ = LstmAllocFloats((size_t)kMidpointRows * so_);
  midpoint_adjoint_ = LstmAllocFloats((size_t)kMidpointRows * soh_);
  midpoint_pending_ = LstmAllocFloats((size_t)horizon_ * so_);
  midpoint_replay_input_ = LstmAllocFloats((size_t)num_layers_ * sli_);
  midpoint_output_gradient_ =
      LstmAllocFloats((size_t)output_size_ * soh_);
  midpoint_output_detached_ = LstmAllocFloats(soh_);
#if SIMD_ACT_F16
  midpoint_output_detached_h_ = LstmAllocHalf(soh_);
#endif
  for (unsigned int layer = 0; layer < num_layers_; ++layer) {
    layers_[layer].InitMidpointOracle();
  }

  const char* arm = getenv("KH_MIDPOINT_ARM");
  if (arm == nullptr || (arm[0] == 'P' && arm[1] == '\0')) {
    midpoint_arm_ = kMidpointParent;
  } else if (arm[0] == 'K' && arm[1] == '\0') {
    midpoint_arm_ = kMidpointKernelIdentity;
  } else if (arm[0] == 'F' && arm[1] == '\0') {
    midpoint_arm_ = kMidpointForward;
  } else if (arm[0] == 'S' && arm[1] == '\0') {
    midpoint_arm_ = kMidpointShifted;
  } else {
    MidpointAbort("KH_MIDPOINT_ARM must be exactly P, K, F, or S");
  }
}

inline void Lstm::MidpointBeginSegment() {
  if (midpoint_segment_active_ || midpoint_captured_rows_ != 0 ||
      (epoch_ != 0 && epoch_ != 64) ||
      midpoint_modeled_events_ % horizon_ != epoch_) {
    MidpointAbort("segment-start alignment failure");
  }
  midpoint_segment_start_ = epoch_;
  memcpy(midpoint_start_hidden_.get(), hidden_.get(), soh_ * sizeof(float));
  for (unsigned int layer = 0; layer < num_layers_; ++layer) {
    if (layers_[layer].epoch_ != epoch_) {
      MidpointAbort("layer epoch disagrees at segment start");
    }
    layers_[layer].MidpointCaptureStart();
  }
  midpoint_segment_active_ = true;
}

inline int Lstm::MidpointBeginCapture(unsigned int input) {
  if (!midpoint_segment_active_ ||
      midpoint_captured_rows_ >= kMidpointRows) return -1;
  const unsigned int expected = midpoint_segment_start_ +
      midpoint_captured_rows_;
  if (epoch_ != expected || midpoint_modeled_events_ % horizon_ != epoch_) {
    MidpointAbort("forward capture alignment failure");
  }
  const unsigned int local = midpoint_captured_rows_;
  memcpy(MidpointAuxRow(local), LayerInputRow(epoch_, 0),
      input_size_ * sizeof(float));
  midpoint_symbols_[local] = input;
  return (int)local;
}

inline void Lstm::MidpointFinishCapture(unsigned int local) {
  if (!midpoint_segment_active_ || local != midpoint_captured_rows_ ||
      local >= kMidpointRows) {
    MidpointAbort("forward capture completion failure");
  }
  memcpy(MidpointProbabilityRow(local), OutputRow(epoch_),
      so_ * sizeof(float));
  memcpy(MidpointFeatureRow(local), hidden_.get(), soh_ * sizeof(float));
  MidpointRequireFinite(MidpointProbabilityRow(local), output_size_,
      "non-finite captured probability");
  MidpointRequireFinite(MidpointFeatureRow(local), hidden_size_,
      "non-finite captured output feature");
  ++midpoint_captured_rows_;
}

inline void Lstm::MidpointBuildOutputAdjoints() {
  const unsigned int last_phase = midpoint_segment_start_ +
      kMidpointRows - 1;
  memcpy(MidpointPendingRow(0), err0_.get(), so_ * sizeof(float));
  for (unsigned int phase = 1; phase <= last_phase; ++phase) {
    memcpy(MidpointPendingRow(phase), OutputRow(phase - 1),
        so_ * sizeof(float));
    MidpointPendingRow(phase)[input_history_[phase - 1]] -= 1.0f;
  }

  for (unsigned int local = 0; local < kMidpointRows; ++local) {
    float* error = MidpointErrorRow(local);
    memcpy(error, MidpointProbabilityRow(local), so_ * sizeof(float));
    const unsigned int target_index = midpoint_arm_ == kMidpointShifted
        ? (local + 16) % kMidpointRows : local;
    error[midpoint_targets_[target_index]] -= 1.0f;
    MidpointRequireFinite(error, output_size_,
        "non-finite midpoint output error");

    float* adjoint = MidpointAdjointRow(local);
    memset(adjoint, 0, soh_ * sizeof(float));
    for (unsigned int symbol = 0; symbol < output_size_; ++symbol) {
      const float coefficient = error[symbol];
      const float* weight = OutputLayerRow(symbol);
      for (unsigned int hidden = 0; hidden < soh_; ++hidden) {
        adjoint[hidden] += coefficient * weight[hidden];
      }
    }
    const unsigned int phase = midpoint_segment_start_ + local;
    for (unsigned int pending = 0; pending <= phase; ++pending) {
      float dot = 0;
      const float* factor = MidpointPendingRow(pending);
      for (unsigned int symbol = 0; symbol < so_; ++symbol) {
        dot += error[symbol] * factor[symbol];
      }
      const float scale = learning_rate_ * dot;
      const float* feature = HHistRow(pending);
      for (unsigned int hidden = 0; hidden < soh_; ++hidden) {
        adjoint[hidden] -= scale * feature[hidden];
      }
    }
    MidpointRequireFinite(adjoint, hidden_size_,
        "non-finite midpoint output adjoint");
  }
}

inline void Lstm::MidpointApplyOutputUpdate(bool commit) {
  memset(midpoint_output_gradient_.get(), 0,
      (size_t)output_size_ * soh_ * sizeof(float));
  for (unsigned int symbol = 0; symbol < output_size_; ++symbol) {
    float* gradient = midpoint_output_gradient_.get() +
        (size_t)symbol * soh_;
    for (unsigned int local = 0; local < kMidpointRows; ++local) {
      const float coefficient = MidpointErrorRow(local)[symbol];
      const float* feature = MidpointFeatureRow(local);
      for (unsigned int hidden = 0; hidden < soh_; ++hidden) {
        gradient[hidden] += coefficient * feature[hidden];
      }
    }
    MidpointRequireFinite(gradient, hidden_size_,
        "non-finite midpoint output gradient");
    if (commit) {
      float* weight = OutputLayerRow(symbol);
      for (unsigned int hidden = 0; hidden < soh_; ++hidden) {
        weight[hidden] -= learning_rate_ * gradient[hidden];
      }
      MidpointRequireFinite(weight, hidden_size_,
          "non-finite midpoint output master");
#if SIMD_ACT_F16
      simd_act::F16EncodeRow(weight, OutputLayerRowH(symbol), soh_);
#endif
    } else {
      memcpy(midpoint_output_detached_.get(), OutputLayerRow(symbol),
          soh_ * sizeof(float));
      for (unsigned int hidden = 0; hidden < soh_; ++hidden) {
        midpoint_output_detached_.get()[hidden] -=
            learning_rate_ * gradient[hidden];
      }
      MidpointRequireFinite(midpoint_output_detached_.get(), hidden_size_,
          "non-finite detached output master");
#if SIMD_ACT_F16
      simd_act::F16EncodeRow(midpoint_output_detached_.get(),
          midpoint_output_detached_h_.get(), soh_);
      midpoint_detached_sink_ = midpoint_detached_sink_ *
          1099511628211ULL +
          midpoint_output_detached_h_.get()[hidden_size_ - 1] + 1ULL;
#endif
      uint32_t bits = 0;
      memcpy(&bits, midpoint_output_detached_.get() + hidden_size_ - 1,
          sizeof(bits));
      midpoint_detached_sink_ =
          midpoint_detached_sink_ * 1099511628211ULL + bits + 1ULL;
    }
  }
}

inline void Lstm::MidpointReplayWindow() {
  memcpy(hidden_.get(), midpoint_start_hidden_.get(), soh_ * sizeof(float));
  for (unsigned int layer = 0; layer < num_layers_; ++layer) {
    layers_[layer].MidpointRestoreStart();
  }
  for (unsigned int local = 0; local < kMidpointRows; ++local) {
    for (unsigned int layer = 0; layer < num_layers_; ++layer) {
      float* row = MidpointReplayInput(layer);
      memset(row, 0, sli_ * sizeof(float));
      memcpy(row, MidpointAuxRow(local), input_size_ * sizeof(float));
      memcpy(row + input_size_, hidden_.get() + layer * num_cells_,
          num_cells_ * sizeof(float));
      if (layer > 0) {
        memcpy(row + input_size_ + num_cells_,
            hidden_.get() + (layer - 1) * num_cells_,
            num_cells_ * sizeof(float));
      }
      row[layer_input_len_[layer] - 1] = 1.0f;
      layers_[layer].MidpointReplayStateOnly(row, midpoint_symbols_[local],
          hidden_.get(), layer * num_cells_);
    }
  }
}

inline bool Lstm::MidpointApplyClosure() {
  if (!midpoint_segment_active_ ||
      midpoint_captured_rows_ != kMidpointRows ||
      epoch_ != midpoint_segment_start_ + kMidpointRows ||
      midpoint_modeled_events_ % horizon_ != epoch_) {
    MidpointAbort("causal closure alignment failure");
  }
  memcpy(midpoint_closure_hidden_.get(), hidden_.get(), soh_ * sizeof(float));
  for (unsigned int layer = 0; layer < num_layers_; ++layer) {
    if (layers_[layer].epoch_ != epoch_) {
      MidpointAbort("layer epoch disagrees at causal closure");
    }
    layers_[layer].MidpointCaptureClosure();
  }
  for (unsigned int local = 0; local < kMidpointRows; ++local) {
    midpoint_targets_[local] =
        input_history_[midpoint_segment_start_ + local];
  }

  MidpointBuildOutputAdjoints();
  memset(hidden_error_.get(), 0, she_ * sizeof(float));
  const bool commit = midpoint_arm_ == kMidpointForward ||
      midpoint_arm_ == kMidpointShifted;
  for (int local = (int)kMidpointRows - 1; local >= 0; --local) {
    for (int layer = (int)num_layers_ - 1; layer >= 0; --layer) {
      const float* adjoint = MidpointAdjointRow(local) +
          (size_t)layer * num_cells_;
      for (unsigned int cell = 0; cell < num_cells_; ++cell) {
        hidden_error_.get()[cell] += adjoint[cell];
      }
      layers_[layer].MidpointBackward(local, layer,
          midpoint_symbols_[local], hidden_error_.get(), commit);
    }
  }
  MidpointApplyOutputUpdate(commit);
  MidpointReplayWindow();

  if (midpoint_arm_ == kMidpointKernelIdentity) {
    if (memcmp(hidden_.get(), midpoint_closure_hidden_.get(),
        soh_ * sizeof(float)) != 0) {
      MidpointAbort("K replay hidden state is not bit-identical");
    }
    for (unsigned int layer = 0; layer < num_layers_; ++layer) {
      if (!layers_[layer].MidpointStateEqualsClosure()) {
        MidpointAbort("K replay cell state is not bit-identical");
      }
    }
  }
  midpoint_preserve_pending_feature_ = true;
  midpoint_segment_active_ = false;
  return true;
}

inline void Lstm::MidpointClearScratch() {
  memset(midpoint_start_hidden_.get(), 0, soh_ * sizeof(float));
  memset(midpoint_closure_hidden_.get(), 0, soh_ * sizeof(float));
  memset(midpoint_auxiliary_.get(), 0,
      (size_t)kMidpointRows * input_size_ * sizeof(float));
  memset(midpoint_probability_.get(), 0,
      (size_t)kMidpointRows * so_ * sizeof(float));
  memset(midpoint_feature_.get(), 0,
      (size_t)kMidpointRows * soh_ * sizeof(float));
  memset(midpoint_error_.get(), 0,
      (size_t)kMidpointRows * so_ * sizeof(float));
  memset(midpoint_adjoint_.get(), 0,
      (size_t)kMidpointRows * soh_ * sizeof(float));
  memset(midpoint_pending_.get(), 0,
      (size_t)horizon_ * so_ * sizeof(float));
  memset(midpoint_replay_input_.get(), 0,
      (size_t)num_layers_ * sli_ * sizeof(float));
  memset(midpoint_output_gradient_.get(), 0,
      (size_t)output_size_ * soh_ * sizeof(float));
  memset(midpoint_output_detached_.get(), 0, soh_ * sizeof(float));
#if SIMD_ACT_F16
  memset(midpoint_output_detached_h_.get(), 0, soh_ * sizeof(uint16_t));
#endif
  std::fill(midpoint_symbols_.begin(), midpoint_symbols_.end(), 0);
  std::fill(midpoint_targets_.begin(), midpoint_targets_.end(), 0);
  for (unsigned int layer = 0; layer < num_layers_; ++layer) {
    layers_[layer].MidpointClearScratch();
  }
  midpoint_detached_sink_ = 0;
  midpoint_segment_start_ = 0;
  midpoint_captured_rows_ = 0;
  midpoint_segment_active_ = false;
  midpoint_preserve_pending_feature_ = false;
}
