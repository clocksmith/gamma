export class ABEEnsemble {
  findAgreement(predictions) {
    const topTokensByModel = predictions.map(pred => pred.topTokens.slice(0, 10));
    const candidates = [];

    for (const token of topTokensByModel[0]) {
      const text = token.text.toLowerCase().trim();
      const matches = topTokensByModel.slice(1).map(tokens =>
        tokens.find(t => t.text.toLowerCase().trim() === text)
      );

      if (matches.every(m => m)) {
        const combinedProb = [token, ...matches].reduce((sum, t) => sum + t.prob, 0) / predictions.length;
        candidates.push({ text, combinedProb, agreement: 1.0 });
      }
    }

    if (candidates.length === 0) return null;
    candidates.sort((a, b) => b.combinedProb - a.combinedProb);
    return candidates[0];
  }
}