/**
 * Agreement-Based Ensemble (ABE) for Mind Meld system
 * Port of Python src/mind_meld/core/abe_ensemble.py
 *
 * Detects surface-form agreement across models with potentially different tokenizers
 */

import { MathUtils } from '../utils/math.js';

/**
 * Agreement candidate
 */
export class AgreementCandidate {
  constructor(data = {}) {
    this.text = data.text ?? '';
    this.normalizedText = data.normalizedText ?? '';
    this.combinedProb = data.combinedProb ?? 0;
    this.agreement = data.agreement ?? 0;
    this.modelContributions = data.modelContributions ?? [];
    this.tokenIds = data.tokenIds ?? [];
  }
}

/**
 * ABE Ensemble - finds agreement across models
 */
export class ABEEnsemble {
  constructor(options = {}) {
    this.topK = options.topK ?? 10;
    this.minAgreement = options.minAgreement ?? 0.5;
    this.normalizeWhitespace = options.normalizeWhitespace ?? true;
    this.caseSensitive = options.caseSensitive ?? false;
    this.verbose = options.verbose ?? false;
  }

  /**
   * Find agreement among predictions from multiple models
   */
  findAgreement(predictions) {
    if (!predictions || predictions.length < 2) {
      return null;
    }

    // Extract top tokens from each model
    const topTokensByModel = predictions.map((pred, modelIdx) => {
      const logits = pred.logitsProcessed || pred.logits || [];
      const probs = MathUtils.softmax(logits);

      // Get top-k tokens
      const indexed = Array.from(probs).map((prob, tokenId) => ({
        prob,
        tokenId,
        text: pred.topTokens?.[tokenId]?.text || this._getTokenText(pred, tokenId),
        modelIndex: modelIdx
      }));

      indexed.sort((a, b) => b.prob - a.prob);
      return indexed.slice(0, this.topK);
    });

    // Find surface-form agreements
    const candidates = this._findSurfaceAgreements(topTokensByModel, predictions);

    if (candidates.length === 0) {
      return null;
    }

    // Sort by combined probability
    candidates.sort((a, b) => b.combinedProb - a.combinedProb);

    // Return best candidate that meets agreement threshold
    for (const candidate of candidates) {
      if (candidate.agreement >= this.minAgreement) {
        return candidate;
      }
    }

    // Return best candidate even if below threshold
    return candidates[0];
  }

  /**
   * Find surface-form agreements across models
   */
  _findSurfaceAgreements(topTokensByModel, predictions) {
    const candidates = [];
    const numModels = topTokensByModel.length;

    // Use first model's tokens as reference
    for (const refToken of topTokensByModel[0]) {
      const normalizedRef = this._normalizeText(refToken.text);
      if (!normalizedRef) continue;

      // Look for matches in other models
      const matches = [refToken];
      const modelContributions = [{
        modelIndex: 0,
        prob: refToken.prob,
        tokenId: refToken.tokenId,
        text: refToken.text
      }];

      for (let m = 1; m < numModels; m++) {
        const match = this._findMatchingToken(normalizedRef, topTokensByModel[m]);
        if (match) {
          matches.push(match);
          modelContributions.push({
            modelIndex: m,
            prob: match.prob,
            tokenId: match.tokenId,
            text: match.text
          });
        }
      }

      // Calculate agreement and combined probability
      const agreement = matches.length / numModels;
      const combinedProb = matches.reduce((sum, t) => sum + t.prob, 0) / matches.length;

      if (matches.length >= 2) {
        candidates.push(new AgreementCandidate({
          text: refToken.text,
          normalizedText: normalizedRef,
          combinedProb,
          agreement,
          modelContributions,
          tokenIds: matches.map(m => m.tokenId)
        }));
      }
    }

    return candidates;
  }

  /**
   * Find matching token by normalized text
   */
  _findMatchingToken(normalizedText, tokens) {
    for (const token of tokens) {
      const normalized = this._normalizeText(token.text);
      if (normalized === normalizedText) {
        return token;
      }
    }
    return null;
  }

  /**
   * Normalize text for comparison
   */
  _normalizeText(text) {
    if (!text) return '';

    let normalized = text;

    // Normalize whitespace
    if (this.normalizeWhitespace) {
      normalized = normalized.trim();
      // Common subword markers
      normalized = normalized.replace(/^[▁Ġ]/, ''); // Remove leading space markers
      normalized = normalized.replace(/##/g, ''); // Remove BERT-style markers
    }

    // Case normalization
    if (!this.caseSensitive) {
      normalized = normalized.toLowerCase();
    }

    return normalized;
  }

  /**
   * Get token text from prediction
   */
  _getTokenText(prediction, tokenId) {
    // Try topTokens first
    if (prediction.topTokens) {
      const found = prediction.topTokens.find(t => t.tokenId === tokenId || t.id === tokenId);
      if (found) return found.text;
    }

    // Try decode function
    if (prediction.decode) {
      try {
        return prediction.decode([tokenId]);
      } catch {
        // Ignore
      }
    }

    return `[${tokenId}]`;
  }

  /**
   * Find partial agreement (subword level)
   */
  findPartialAgreement(predictions) {
    if (!predictions || predictions.length < 2) {
      return null;
    }

    // Get top tokens with their text
    const topTokensByModel = predictions.map((pred, modelIdx) => {
      const logits = pred.logitsProcessed || pred.logits || [];
      const probs = MathUtils.softmax(logits);

      const indexed = Array.from(probs).map((prob, tokenId) => ({
        prob,
        tokenId,
        text: this._getTokenText(pred, tokenId),
        modelIndex: modelIdx
      }));

      indexed.sort((a, b) => b.prob - a.prob);
      return indexed.slice(0, this.topK * 2); // Use more tokens for partial matching
    });

    // Find partial matches (prefix matches)
    const candidates = [];

    for (const refToken of topTokensByModel[0]) {
      const refText = this._normalizeText(refToken.text);
      if (refText.length < 2) continue; // Skip very short tokens

      const partialMatches = [{
        modelIndex: 0,
        prob: refToken.prob,
        tokenId: refToken.tokenId,
        text: refToken.text,
        matchType: 'exact'
      }];

      for (let m = 1; m < topTokensByModel.length; m++) {
        for (const token of topTokensByModel[m]) {
          const tokenText = this._normalizeText(token.text);

          // Check for prefix match
          if (refText.startsWith(tokenText) || tokenText.startsWith(refText)) {
            partialMatches.push({
              modelIndex: m,
              prob: token.prob,
              tokenId: token.tokenId,
              text: token.text,
              matchType: refText === tokenText ? 'exact' : 'prefix'
            });
            break;
          }
        }
      }

      if (partialMatches.length >= 2) {
        const exactCount = partialMatches.filter(m => m.matchType === 'exact').length;
        const agreement = partialMatches.length / topTokensByModel.length;
        const combinedProb = partialMatches.reduce((sum, t) => sum + t.prob, 0) / partialMatches.length;

        candidates.push({
          text: refToken.text,
          combinedProb,
          agreement,
          exactMatchRatio: exactCount / partialMatches.length,
          modelContributions: partialMatches
        });
      }
    }

    // Sort by combined score (agreement * combinedProb)
    candidates.sort((a, b) => (b.agreement * b.combinedProb) - (a.agreement * a.combinedProb));

    return candidates.length > 0 ? candidates[0] : null;
  }

  /**
   * Get agreement statistics
   */
  getAgreementStats(predictions) {
    if (!predictions || predictions.length < 2) {
      return { topAgreement: 1.0, averageAgreement: 1.0, disagreementTokens: [] };
    }

    // Get top-1 token from each model
    const top1Tokens = predictions.map((pred, modelIdx) => {
      const logits = pred.logitsProcessed || pred.logits || [];
      const probs = MathUtils.softmax(logits);
      const topIdx = MathUtils.argmax(probs);

      return {
        tokenId: topIdx,
        text: this._getTokenText(pred, topIdx),
        prob: probs[topIdx],
        modelIndex: modelIdx
      };
    });

    // Check top-1 agreement
    const normalizedTop1 = top1Tokens.map(t => this._normalizeText(t.text));
    const uniqueTop1 = new Set(normalizedTop1);
    const topAgreement = 1 - (uniqueTop1.size - 1) / predictions.length;

    // Find agreement candidate
    const agreement = this.findAgreement(predictions);
    const averageAgreement = agreement?.agreement ?? 0;

    // Find tokens where models disagree
    const disagreementTokens = [];
    if (uniqueTop1.size > 1) {
      const tokenCounts = new Map();
      for (const token of normalizedTop1) {
        tokenCounts.set(token, (tokenCounts.get(token) || 0) + 1);
      }

      for (const [token, count] of tokenCounts) {
        if (count < predictions.length) {
          disagreementTokens.push({
            text: token,
            agreementCount: count,
            models: top1Tokens
              .filter(t => this._normalizeText(t.text) === token)
              .map(t => t.modelIndex)
          });
        }
      }
    }

    return {
      topAgreement,
      averageAgreement,
      agreementCandidate: agreement,
      top1Tokens,
      disagreementTokens
    };
  }
}
