#include <stdio.h>

// This file is an inert, review-only overlay until the v4 activation gate
// materializes it beside the sealed q1 lstm-layer.hpp. It contains no coder,
// mixer, context, frontend, or ordinary-tape writes.

inline void MidpointLayerAbort(const char* reason) {
  fprintf(stderr, "cmix-midpoint-oracle: %s\n", reason);
  abort();
}

inline void MidpointRequireFinite(const float* values, size_t count,
    const char* reason) {
  for (size_t i = 0; i < count; ++i) {
    if (!std::isfinite(values[i])) MidpointLayerAbort(reason);
  }
}

inline float* LstmLayer::MidpointGateError(unsigned int gate,
    unsigned int local) {
  return midpoint_gate_error_.get() +
      ((size_t)gate * kMidpointRows + local) * scell_;
}

inline float* LstmLayer::MidpointSymbolGradient(unsigned int gate,
    unsigned int symbol) {
  return midpoint_symbol_gradient_.get() +
      ((size_t)gate * output_size_ + symbol) * scell_;
}

inline float* LstmLayer::MidpointDenseGradient(unsigned int gate,
    unsigned int cell) {
  return midpoint_dense_gradient_.get() +
      ((size_t)gate * num_cells_ + cell) * sdense_;
}

inline float* LstmLayer::MidpointGammaGradient(unsigned int gate) {
  return midpoint_gamma_gradient_.get() + (size_t)gate * scell_;
}

inline float* LstmLayer::MidpointBetaGradient(unsigned int gate) {
  return midpoint_beta_gradient_.get() + (size_t)gate * scell_;
}

inline float* LstmLayer::MidpointTranspose(unsigned int gate,
    unsigned int row) {
  return midpoint_transpose_.get() +
      ((size_t)gate * forget_gate_.trows_ + row) * scell_;
}

inline LstmHistElem* LstmLayer::MidpointGateState(unsigned int gate,
    unsigned int local) {
  return midpoint_gate_state_.get() +
      ((size_t)gate * kMidpointRows + local) * scell_;
}

inline LstmHistElem* LstmLayer::MidpointGateNorm(unsigned int gate,
    unsigned int local) {
  return midpoint_gate_norm_.get() +
      ((size_t)gate * kMidpointRows + local) * scell_;
}

inline void LstmLayer::InitMidpointOracle() {
  const size_t scratch_stride = std::max(scell_, sdense_);
  const size_t detached_width = scratch_stride;
  midpoint_start_state_ = LstmAllocFloats(scell_);
  midpoint_closure_state_ = LstmAllocFloats(scell_);
  midpoint_tanh_state_ = LstmAllocHist((size_t)kMidpointRows * scell_);
  midpoint_input_gate_state_ =
      LstmAllocHist((size_t)kMidpointRows * scell_);
  midpoint_last_state_ = LstmAllocHist((size_t)kMidpointRows * scell_);
  midpoint_input_history_ = LstmAllocHist((size_t)kMidpointRows * sdense_);
  midpoint_gate_state_ = LstmAllocHist(
      (size_t)kMidpointGates * kMidpointRows * scell_);
  midpoint_gate_norm_ = LstmAllocHist(
      (size_t)kMidpointGates * kMidpointRows * scell_);
  midpoint_ivar_ = LstmAllocFloats(
      (size_t)kMidpointGates * kMidpointRows);
  midpoint_gate_error_ = LstmAllocFloats(
      (size_t)kMidpointGates * kMidpointRows * scell_);
  midpoint_symbol_gradient_ = LstmAllocFloats(
      (size_t)kMidpointGates * output_size_ * scell_);
  midpoint_dense_gradient_ = LstmAllocFloats(
      (size_t)kMidpointGates * num_cells_ * sdense_);
  midpoint_gamma_gradient_ =
      LstmAllocFloats((size_t)kMidpointGates * scell_);
  midpoint_beta_gradient_ =
      LstmAllocFloats((size_t)kMidpointGates * scell_);
  midpoint_temporal_ = LstmAllocFloats((size_t)2 * scell_);
  midpoint_transpose_ = LstmAllocFloats(
      (size_t)kMidpointGates * forget_gate_.trows_ * scell_);
  midpoint_scratch_ = LstmAllocFloats((size_t)8 * scratch_stride);
  midpoint_detached_ = LstmAllocFloats((size_t)3 * detached_width);
#if SIMD_ACT_F16
  midpoint_detached_h_ = LstmAllocHalf(detached_width);
#endif
}

inline void LstmLayer::MidpointCaptureStart() {
  memcpy(midpoint_start_state_.get(), state_.get(), scell_ * sizeof(float));
}

inline void LstmLayer::MidpointCaptureClosure() {
  memcpy(midpoint_closure_state_.get(), state_.get(),
      scell_ * sizeof(float));
}

inline void LstmLayer::MidpointCaptureRow(unsigned int local,
    unsigned int absolute_epoch, const float* input) {
  if (local >= kMidpointRows || absolute_epoch >= horizon_) {
    MidpointLayerAbort("capture coordinate outside frozen window");
  }
  const size_t hist_bytes = scell_ * sizeof(LstmHistElem);
  memcpy(midpoint_tanh_state_.get() + (size_t)local * scell_,
      tanh_state_.get() + (size_t)absolute_epoch * scell_, hist_bytes);
  memcpy(midpoint_input_gate_state_.get() + (size_t)local * scell_,
      input_gate_state_.get() + (size_t)absolute_epoch * scell_, hist_bytes);
  memcpy(midpoint_last_state_.get() + (size_t)local * scell_,
      last_state_.get() + (size_t)absolute_epoch * scell_, hist_bytes);
#if SIMD_ACT_F16
  memcpy(midpoint_input_history_.get() + (size_t)local * sdense_,
      inp_hist_.get() + (size_t)absolute_epoch * sdense_,
      sdense_ * sizeof(LstmHistElem));
#else
  memcpy(midpoint_input_history_.get() + (size_t)local * sdense_, input,
      dense_width_ * sizeof(float));
#endif
  NeuronLayer* gates[kMidpointGates] = {
      &forget_gate_, &input_node_, &output_gate_};
  for (unsigned int gate = 0; gate < kMidpointGates; ++gate) {
    memcpy(MidpointGateState(gate, local),
        gates[gate]->state(absolute_epoch), hist_bytes);
    memcpy(MidpointGateNorm(gate, local),
        gates[gate]->norm(absolute_epoch), hist_bytes);
    midpoint_ivar_.get()[(size_t)gate * kMidpointRows + local] =
        gates[gate]->ivar_[absolute_epoch];
  }
}

inline void LstmLayer::MidpointRestoreStart() {
  memcpy(state_.get(), midpoint_start_state_.get(), scell_ * sizeof(float));
}

inline bool LstmLayer::MidpointStateEqualsClosure() const {
  return memcmp(state_.get(), midpoint_closure_state_.get(),
      scell_ * sizeof(float)) == 0;
}

inline void LstmLayer::MidpointBackward(unsigned int local, int layer,
    int input_symbol, float* hidden_error, bool commit) {
  if (local >= kMidpointRows || input_symbol < 0 ||
      (unsigned int)input_symbol >= output_size_) {
    MidpointLayerAbort("backward coordinate or symbol outside contract");
  }
  const size_t scratch_stride = std::max(scell_, sdense_);
  NeuronLayer* gates[kMidpointGates] = {
      &forget_gate_, &input_node_, &output_gate_};

  if (local == kMidpointRows - 1) {
    memset(midpoint_temporal_.get(), 0, (size_t)2 * scell_ * sizeof(float));
    memset(midpoint_gate_error_.get(), 0,
        (size_t)kMidpointGates * kMidpointRows * scell_ * sizeof(float));
    memset(midpoint_symbol_gradient_.get(), 0,
        (size_t)kMidpointGates * output_size_ * scell_ * sizeof(float));
    memset(midpoint_dense_gradient_.get(), 0,
        (size_t)kMidpointGates * num_cells_ * sdense_ * sizeof(float));
    memset(midpoint_gamma_gradient_.get(), 0,
        (size_t)kMidpointGates * scell_ * sizeof(float));
    memset(midpoint_beta_gradient_.get(), 0,
        (size_t)kMidpointGates * scell_ * sizeof(float));
    for (unsigned int gate = 0; gate < kMidpointGates; ++gate) {
      NeuronLayer& neurons = *gates[gate];
      for (size_t j0 = 0; j0 < neurons.trows_; j0 += 16) {
        const size_t jend = std::min(j0 + 16, neurons.trows_);
        for (size_t i0 = 0; i0 < num_cells_; i0 += 16) {
          const size_t iend = std::min(i0 + 16, (size_t)num_cells_);
          for (size_t j = j0; j < jend; ++j) {
            float* tr = MidpointTranspose(gate, j);
            for (size_t i = i0; i < iend; ++i) {
              tr[i] = neurons.wdense(i)[input_size_ + j];
            }
          }
        }
      }
    }
  }

  float* tsd = midpoint_scratch_.get();
  float* igsd = tsd + scratch_stride;
  float* lsd = igsd + scratch_stride;
  float* fgsd = lsd + scratch_stride;
  float* insd = fgsd + scratch_stride;
  float* ogsd = insd + scratch_stride;
#if SIMD_ACT_F16
  simd_act::F16DecodeRow(midpoint_tanh_state_.get() +
      (size_t)local * scell_, tsd, scell_);
  simd_act::F16DecodeRow(midpoint_input_gate_state_.get() +
      (size_t)local * scell_, igsd, scell_);
  simd_act::F16DecodeRow(midpoint_last_state_.get() +
      (size_t)local * scell_, lsd, scell_);
  simd_act::F16DecodeRow(MidpointGateState(0, local), fgsd, scell_);
  simd_act::F16DecodeRow(MidpointGateState(1, local), insd, scell_);
  simd_act::F16DecodeRow(MidpointGateState(2, local), ogsd, scell_);
  const float* ts = tsd;
  const float* igs = igsd;
  const float* ls = lsd;
  const float* fgs = fgsd;
  const float* ins = insd;
  const float* ogs = ogsd;
#else
  const float* ts = midpoint_tanh_state_.get() + (size_t)local * scell_;
  const float* igs = midpoint_input_gate_state_.get() +
      (size_t)local * scell_;
  const float* ls = midpoint_last_state_.get() + (size_t)local * scell_;
  const float* fgs = MidpointGateState(0, local);
  const float* ins = MidpointGateState(1, local);
  const float* ogs = MidpointGateState(2, local);
#endif

  float* state_error = midpoint_temporal_.get();
  float* stored_error = state_error + scell_;
  if (local == kMidpointRows - 1) {
    for (unsigned int i = 0; i < num_cells_; ++i) {
      stored_error[i] = hidden_error[i];
      state_error[i] = 0;
    }
  } else {
    for (unsigned int i = 0; i < num_cells_; ++i) {
      stored_error[i] += hidden_error[i];
    }
  }

  float* fge = MidpointGateError(0, local);
  float* ine = MidpointGateError(1, local);
  float* oge = MidpointGateError(2, local);
  for (unsigned int i = 0; i < num_cells_; ++i) {
    oge[i] = ts[i] * stored_error[i] * ogs[i] * (1.0f - ogs[i]);
  }
  for (unsigned int i = 0; i < num_cells_; ++i) {
    state_error[i] +=
        stored_error[i] * ogs[i] * (1.0f - ts[i] * ts[i]);
  }
  for (unsigned int i = 0; i < num_cells_; ++i) {
    ine[i] = state_error[i] * igs[i] * (1.0f - ins[i] * ins[i]);
  }
  for (unsigned int i = 0; i < num_cells_; ++i) {
    fge[i] = (ls[i] - ins[i]) * state_error[i] * fgs[i] * igs[i];
  }
  for (unsigned int i = 0; i < num_cells_; ++i) hidden_error[i] = 0;
  if (local > 0) {
    for (unsigned int i = 0; i < num_cells_; ++i) state_error[i] *= fgs[i];
    memset(stored_error, 0, scell_ * sizeof(float));
  }

  unsigned long long midpoint_step = update_steps_;
  if (local == 0 && midpoint_step < UPDATE_LIMIT) ++midpoint_step;
  const AdamParams adam = MakeAdamParams(learning_rate_, midpoint_step);
  const size_t detached_width = scratch_stride;
  float* detached_m = midpoint_detached_.get();
  float* detached_v = detached_m + detached_width;
  float* detached_w = detached_v + detached_width;

  auto absorb_detached = [&](size_t n) {
    uint32_t bits = 0;
    memcpy(&bits, detached_w + n - 1, sizeof(bits));
    midpoint_detached_sink_ =
        midpoint_detached_sink_ * 1099511628211ULL + bits + 1ULL;
  };
  auto apply_adam = [&](float* gradient, float* moment1, float* moment2,
      float* weight, size_t update_width, size_t copy_width,
      uint16_t* live_shadow) {
    MidpointRequireFinite(gradient, update_width,
        "non-finite midpoint recurrent gradient");
    if (commit) {
      Adam(adam, gradient, moment1, moment2, weight, update_width);
      MidpointRequireFinite(weight, update_width,
          "non-finite midpoint recurrent master");
      MidpointRequireFinite(moment1, update_width,
          "non-finite midpoint recurrent first moment");
      MidpointRequireFinite(moment2, update_width,
          "non-finite midpoint recurrent second moment");
#if SIMD_ACT_F16
      if (live_shadow != nullptr) {
        simd_act::F16EncodeRow(weight, live_shadow, copy_width);
      }
#else
      (void)copy_width;
      (void)live_shadow;
#endif
    } else {
      memcpy(detached_m, moment1, update_width * sizeof(float));
      memcpy(detached_v, moment2, update_width * sizeof(float));
      memcpy(detached_w, weight, copy_width * sizeof(float));
      Adam(adam, gradient, detached_m, detached_v, detached_w, update_width);
      MidpointRequireFinite(detached_w, update_width,
          "non-finite detached recurrent master");
#if SIMD_ACT_F16
      if (live_shadow != nullptr) {
        simd_act::F16EncodeRow(detached_w, midpoint_detached_h_.get(),
            copy_width);
        midpoint_detached_sink_ = midpoint_detached_sink_ *
            1099511628211ULL + midpoint_detached_h_.get()[update_width - 1] +
            1ULL;
      }
#endif
      absorb_detached(update_width);
    }
  };

  for (unsigned int gate = 0; gate < kMidpointGates; ++gate) {
    NeuronLayer& neurons = *gates[gate];
    float* err = MidpointGateError(gate, local);
    float* nrm = midpoint_scratch_.get() + (size_t)6 * scratch_stride;
#if SIMD_ACT_F16
    simd_act::F16DecodeRow(MidpointGateNorm(gate, local), nrm, scell_);
#else
    nrm = MidpointGateNorm(gate, local);
#endif
    float* beta_gradient = MidpointBetaGradient(gate);
    float* gamma_gradient = MidpointGammaGradient(gate);
    for (unsigned int i = 0; i < num_cells_; ++i) {
      beta_gradient[i] += err[i];
      gamma_gradient[i] += err[i] * nrm[i];
    }
    const float ivar = midpoint_ivar_.get()[
        (size_t)gate * kMidpointRows + local];
    for (unsigned int i = 0; i < num_cells_; ++i) {
      err[i] *= neurons.gamma_[i] * ivar;
    }
    float projection = 0;
    for (unsigned int i = 0; i < num_cells_; ++i) {
      projection += err[i] * nrm[i];
    }
    const float scale = projection / num_cells_;
    for (unsigned int i = 0; i < num_cells_; ++i) {
      err[i] -= scale * nrm[i];
    }
    if (layer > 0) {
      for (unsigned int i = 0; i < num_cells_; ++i) {
        float propagated = 0;
        const float* tr = MidpointTranspose(gate, num_cells_ + i);
        for (unsigned int j = 0; j < num_cells_; ++j) {
          propagated += err[j] * tr[j];
        }
        hidden_error[i] += propagated;
      }
    }
    if (local > 0) {
      for (unsigned int i = 0; i < num_cells_; ++i) {
        float propagated = 0;
        const float* tr = MidpointTranspose(gate, i);
        for (unsigned int j = 0; j < num_cells_; ++j) {
          propagated += err[j] * tr[j];
        }
        stored_error[i] += propagated;
      }
    }
    float* symbol_gradient = MidpointSymbolGradient(gate, input_symbol);
    for (unsigned int i = 0; i < num_cells_; ++i) {
      symbol_gradient[i] += err[i];
    }

    if (local == 0) {
      for (unsigned int i0 = 0; i0 < num_cells_; i0 += 16) {
        const unsigned int iend = std::min(i0 + 16, num_cells_);
        for (unsigned int i = i0; i < iend; ++i) {
          memset(MidpointDenseGradient(gate, i), 0,
              sdense_ * sizeof(float));
        }
        for (unsigned int event = 0; event < kMidpointRows; ++event) {
          const float* event_error = MidpointGateError(gate, event);
#if SIMD_ACT_F16
          const uint16_t* input_row = midpoint_input_history_.get() +
              (size_t)event * sdense_;
          for (unsigned int i = i0; i < iend; ++i) {
            simd_act::F16Axpy(MidpointDenseGradient(gate, i), input_row,
                event_error[i], sdense_);
          }
#else
          const float* input_row = midpoint_input_history_.get() +
              (size_t)event * sdense_;
          for (unsigned int i = i0; i < iend; ++i) {
            const float error = event_error[i];
            float* gradient = MidpointDenseGradient(gate, i);
            for (unsigned int j = 0; j < dense_width_; ++j) {
              gradient[j] += error * input_row[j];
            }
          }
#endif
        }
        for (unsigned int i = i0; i < iend; ++i) {
#if SIMD_ACT_F16
          uint16_t* live_shadow = neurons.whdense(i);
#else
          uint16_t* live_shadow = nullptr;
#endif
          apply_adam(MidpointDenseGradient(gate, i), neurons.mdense(i),
              neurons.vdense(i), neurons.wdense(i), neurons.dense_width_,
              neurons.sdense_, live_shadow);
        }
      }
      for (size_t symbol = 0; symbol < neurons.sym_width_; ++symbol) {
        apply_adam(MidpointSymbolGradient(gate, symbol),
            neurons.msymt(symbol), neurons.vsymt(symbol),
            neurons.wsymt(symbol), num_cells_, num_cells_, nullptr);
      }
      apply_adam(gamma_gradient, &neurons.gamma_m_[0],
          &neurons.gamma_v_[0], &neurons.gamma_[0], num_cells_,
          num_cells_, nullptr);
      apply_adam(beta_gradient, &neurons.beta_m_[0], &neurons.beta_v_[0],
          &neurons.beta_[0], num_cells_, num_cells_, nullptr);
    }
  }
  if (local == 0 && commit) update_steps_ = midpoint_step;
  ClipGradients(state_error, num_cells_);
  ClipGradients(stored_error, num_cells_);
  ClipGradients(hidden_error, num_cells_);
}

inline void LstmLayer::MidpointReplayStateOnly(const float* input,
    int input_symbol, float* hidden, int hidden_start) {
  if (input_symbol < 0 || (unsigned int)input_symbol >= output_size_) {
    MidpointLayerAbort("replay symbol outside contract");
  }
  const size_t scratch_stride = std::max(scell_, sdense_);
  float* nf = midpoint_scratch_.get();
  float* ni = nf + scratch_stride;
  float* no = ni + scratch_stride;
  float* fgs = no + scratch_stride;
  float* ins = fgs + scratch_stride;
  float* ogs = ins + scratch_stride;
  float* igs = ogs + scratch_stride;
  float* ts = igs + scratch_stride;
  memset(midpoint_scratch_.get(), 0,
      (size_t)8 * scratch_stride * sizeof(float));

  const float* wsf = forget_gate_.wsymt(input_symbol);
  const float* wsi = input_node_.wsymt(input_symbol);
  const float* wso = output_gate_.wsymt(input_symbol);
#if SIMD_ACT_F16
  const size_t sdense = forget_gate_.sdense_;
  for (unsigned int i = 0; i < num_cells_; ++i) {
    float ff, fi, fo;
    const uint16_t* rf = forget_gate_.whdense(i);
    simd_act::F16Dot3(input, rf, rf + sdense, rf + 2 * sdense, sdense,
        &ff, &fi, &fo);
    nf[i] = wsf[i] + ff;
    ni[i] = wsi[i] + fi;
    no[i] = wso[i] + fo;
  }
#else
  for (unsigned int i = 0; i < num_cells_; ++i) {
    float ff = wsf[i];
    float fi = wsi[i];
    float fo = wso[i];
    const float* rf = forget_gate_.wdense(i);
    const float* ri = input_node_.wdense(i);
    const float* ro = output_gate_.wdense(i);
    for (unsigned int j = 0; j < dense_width_; ++j) {
      ff += input[j] * rf[j];
      fi += input[j] * ri[j];
      fo += input[j] * ro[j];
    }
    nf[i] = ff;
    ni[i] = fi;
    no[i] = fo;
  }
#endif

  NeuronLayer* gates[kMidpointGates] = {
      &forget_gate_, &input_node_, &output_gate_};
  float* normalized[kMidpointGates] = {nf, ni, no};
  float* activated[kMidpointGates] = {fgs, ins, ogs};
  for (unsigned int gate = 0; gate < kMidpointGates; ++gate) {
    float sum_squares = 0;
    for (unsigned int i = 0; i < num_cells_; ++i) {
      sum_squares += normalized[gate][i] * normalized[gate][i];
    }
    const float ivar = 1.0f / sqrt((sum_squares / num_cells_) + 1e-5f);
    for (unsigned int i = 0; i < num_cells_; ++i) {
      normalized[gate][i] *= ivar;
    }
    for (unsigned int i = 0; i < num_cells_; ++i) {
      activated[gate][i] = normalized[gate][i] * gates[gate]->gamma_[i] +
          gates[gate]->beta_[i];
    }
  }
  simd_act::Logistic(fgs, num_cells_);
  simd_act::Tanh(ins, num_cells_);
  simd_act::Logistic(ogs, num_cells_);
  for (unsigned int i = 0; i < num_cells_; ++i) igs[i] = 1.0f - fgs[i];
  float* cell = state_.get();
  for (unsigned int i = 0; i < num_cells_; ++i) cell[i] *= fgs[i];
  for (unsigned int i = 0; i < num_cells_; ++i) cell[i] += ins[i] * igs[i];
  simd_act::Tanh(ts, cell, num_cells_);
  for (unsigned int i = 0; i < num_cells_; ++i) {
    hidden[hidden_start + i] = ogs[i] * ts[i];
  }
  MidpointRequireFinite(hidden + hidden_start, num_cells_,
      "non-finite midpoint replay hidden state");
  MidpointRequireFinite(cell, num_cells_,
      "non-finite midpoint replay cell state");
}

inline void LstmLayer::MidpointClearScratch() {
  memset(midpoint_start_state_.get(), 0, scell_ * sizeof(float));
  memset(midpoint_closure_state_.get(), 0, scell_ * sizeof(float));
  memset(midpoint_tanh_state_.get(), 0,
      (size_t)kMidpointRows * scell_ * sizeof(LstmHistElem));
  memset(midpoint_input_gate_state_.get(), 0,
      (size_t)kMidpointRows * scell_ * sizeof(LstmHistElem));
  memset(midpoint_last_state_.get(), 0,
      (size_t)kMidpointRows * scell_ * sizeof(LstmHistElem));
  memset(midpoint_input_history_.get(), 0,
      (size_t)kMidpointRows * sdense_ * sizeof(LstmHistElem));
  memset(midpoint_gate_state_.get(), 0,
      (size_t)kMidpointGates * kMidpointRows * scell_ *
      sizeof(LstmHistElem));
  memset(midpoint_gate_norm_.get(), 0,
      (size_t)kMidpointGates * kMidpointRows * scell_ *
      sizeof(LstmHistElem));
  memset(midpoint_ivar_.get(), 0,
      (size_t)kMidpointGates * kMidpointRows * sizeof(float));
  memset(midpoint_gate_error_.get(), 0,
      (size_t)kMidpointGates * kMidpointRows * scell_ * sizeof(float));
  memset(midpoint_symbol_gradient_.get(), 0,
      (size_t)kMidpointGates * output_size_ * scell_ * sizeof(float));
  memset(midpoint_dense_gradient_.get(), 0,
      (size_t)kMidpointGates * num_cells_ * sdense_ * sizeof(float));
  memset(midpoint_gamma_gradient_.get(), 0,
      (size_t)kMidpointGates * scell_ * sizeof(float));
  memset(midpoint_beta_gradient_.get(), 0,
      (size_t)kMidpointGates * scell_ * sizeof(float));
  memset(midpoint_temporal_.get(), 0, (size_t)2 * scell_ * sizeof(float));
  memset(midpoint_transpose_.get(), 0,
      (size_t)kMidpointGates * forget_gate_.trows_ * scell_ * sizeof(float));
  const size_t scratch_stride = std::max(scell_, sdense_);
  memset(midpoint_scratch_.get(), 0,
      (size_t)8 * scratch_stride * sizeof(float));
  memset(midpoint_detached_.get(), 0,
      (size_t)3 * scratch_stride * sizeof(float));
#if SIMD_ACT_F16
  memset(midpoint_detached_h_.get(), 0,
      scratch_stride * sizeof(uint16_t));
#endif
  midpoint_detached_sink_ = 0;
}
