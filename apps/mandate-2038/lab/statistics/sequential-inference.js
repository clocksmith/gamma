const PI_SQUARED = Math.PI ** 2;

function clamp(value, minimum = 0, maximum = 1) {
  return Math.min(maximum, Math.max(minimum, value));
}

function mean(values) {
  return values.length
    ? values.reduce((sum, value) => sum + value, 0) / values.length
    : 0;
}

function variance(values, center = mean(values)) {
  return mean(values.map((value) => (value - center) ** 2));
}

export function alphaSpentAtLook({
  alpha = 0.05,
  familySize = 1,
  look = 1
} = {}) {
  if (!(alpha > 0 && alpha < 1)) throw new RangeError("alpha must be between zero and one.");
  if (!Number.isInteger(familySize) || familySize < 1) {
    throw new RangeError("familySize must be a positive integer.");
  }
  if (!Number.isInteger(look) || look < 1) {
    throw new RangeError("look must be a positive integer.");
  }
  return alpha / familySize * 6 / (PI_SQUARED * look ** 2);
}

export function boundedConfidenceSequence({
  success,
  exposure,
  alpha = 0.05,
  familySize = 1,
  look = 1
}) {
  if (!(exposure > 0) || success < 0 || success > exposure) {
    return {
      estimate: null,
      lower: 0,
      upper: 1,
      halfWidth: 0.5,
      exposure,
      alphaSpent: alphaSpentAtLook({ alpha, familySize, look })
    };
  }
  const estimate = success / exposure;
  const alphaSpent = alphaSpentAtLook({ alpha, familySize, look });
  const radius = Math.sqrt(Math.log(2 / alphaSpent) / (2 * exposure));
  const lower = clamp(estimate - radius);
  const upper = clamp(estimate + radius);
  return {
    estimate,
    lower,
    upper,
    halfWidth: (upper - lower) / 2,
    exposure,
    alphaSpent
  };
}

export function empiricalBayesRates(cells, {
  alpha = 0.05,
  familySize = Math.max(1, cells.length),
  look = 1,
  minimumExposure = 1
} = {}) {
  const observed = cells.filter((cell) => cell.exposure >= minimumExposure);
  const totalExposure = observed.reduce((sum, cell) => sum + cell.exposure, 0);
  const totalSuccess = observed.reduce((sum, cell) => sum + cell.success, 0);
  const grandMean = totalExposure ? totalSuccess / totalExposure : 0.5;
  const rawRates = observed.map((cell) => cell.success / cell.exposure);
  const observedVariance = variance(rawRates);
  const expectedSamplingVariance = mean(observed.map((cell) =>
    grandMean * (1 - grandMean) / Math.max(1, cell.exposure)
  ));
  const betweenVariance = Math.max(0, observedVariance - expectedSamplingVariance);
  const rawPrecision = betweenVariance > 0
    ? grandMean * (1 - grandMean) / betweenVariance - 1
    : 10000;
  const priorPrecision = clamp(rawPrecision, 2, 10000);
  const priorAlpha = Math.max(0.001, grandMean * priorPrecision);
  const priorBeta = Math.max(0.001, (1 - grandMean) * priorPrecision);
  return {
    grandMean,
    prior: {
      alpha: priorAlpha,
      beta: priorBeta,
      precision: priorPrecision,
      betweenVariance
    },
    cells: cells.map((cell) => {
      const posteriorAlpha = priorAlpha + cell.success;
      const posteriorBeta = priorBeta + cell.exposure - cell.success;
      const total = posteriorAlpha + posteriorBeta;
      const posteriorMean = posteriorAlpha / total;
      const posteriorVariance =
        posteriorAlpha * posteriorBeta / (total ** 2 * (total + 1));
      const posteriorRadius = 1.96 * Math.sqrt(posteriorVariance);
      return {
        ...cell,
        rawRate: cell.exposure ? cell.success / cell.exposure : null,
        posteriorMean,
        posteriorInterval: {
          lower: clamp(posteriorMean - posteriorRadius),
          upper: clamp(posteriorMean + posteriorRadius)
        },
        confidenceSequence: boundedConfidenceSequence({
          success: cell.success,
          exposure: cell.exposure,
          alpha,
          familySize,
          look
        })
      };
    })
  };
}

export function intervalCrossesThreshold(cell, {
  operator,
  threshold,
  minimumExposure
}) {
  if (cell.exposure < minimumExposure) return false;
  if (operator === "max") {
    return cell.posteriorInterval.lower > threshold &&
      cell.confidenceSequence.lower > threshold;
  }
  if (operator === "min") {
    return cell.posteriorInterval.upper < threshold &&
      cell.confidenceSequence.upper < threshold;
  }
  throw new TypeError(`Unknown threshold operator: ${operator}.`);
}

export function precisionReached(groups, {
  targetHalfWidth,
  minimumExposure
}) {
  return groups.length > 0 && groups.every((group) =>
    group.exposure >= minimumExposure &&
    group.confidenceSequence.halfWidth <= targetHalfWidth
  );
}
