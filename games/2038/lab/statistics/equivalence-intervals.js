const Z_98 = 2.3263478740408408;

function assertNonEmpty(values, label) {
  if (!Array.isArray(values) || values.length === 0) {
    throw new Error(`${label} requires at least one observation.`);
  }
}

export function mean(values) {
  assertNonEmpty(values, "mean");
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

export function sampleVariance(values) {
  assertNonEmpty(values, "sample variance");
  if (values.length === 1) return 0;
  const center = mean(values);
  return values.reduce((sum, value) => sum + (value - center) ** 2, 0) /
    (values.length - 1);
}

export function normalMeanInterval98(values) {
  const estimate = mean(values);
  const halfWidth = Z_98 * Math.sqrt(sampleVariance(values) / values.length);
  return {
    n: values.length,
    estimate,
    lower: estimate - halfWidth,
    upper: estimate + halfWidth,
    halfWidth,
  };
}

export function subsetMinusGrandMeanInterval98(values, included) {
  assertNonEmpty(values, "subset contrast");
  if (!Array.isArray(included) || included.length !== values.length) {
    throw new Error("subset contrast requires one inclusion flag per observation.");
  }
  const group = values.filter((_, index) => included[index]);
  const rest = values.filter((_, index) => !included[index]);
  assertNonEmpty(group, "subset contrast group");
  assertNonEmpty(rest, "subset contrast complement");

  const total = values.length;
  const complementWeight = rest.length / total;
  const estimate = complementWeight * (mean(group) - mean(rest));
  const standardError = complementWeight * Math.sqrt(
    sampleVariance(group) / group.length + sampleVariance(rest) / rest.length,
  );
  const halfWidth = Z_98 * standardError;
  return {
    n: total,
    groupN: group.length,
    complementN: rest.length,
    estimate,
    lower: estimate - halfWidth,
    upper: estimate + halfWidth,
    halfWidth,
  };
}

export function wilsonInterval98(successes, trials) {
  if (!Number.isInteger(successes) || !Number.isInteger(trials) ||
      successes < 0 || trials <= 0 || successes > trials) {
    throw new Error("Wilson interval requires 0 <= successes <= positive trials.");
  }
  const proportion = successes / trials;
  const zSquared = Z_98 ** 2;
  const denominator = 1 + zSquared / trials;
  const center = (proportion + zSquared / (2 * trials)) / denominator;
  const halfWidth = Z_98 * Math.sqrt(
    (proportion * (1 - proportion) + zSquared / (4 * trials)) / trials,
  ) / denominator;
  return {
    successes,
    trials,
    estimate: proportion,
    lower: center - halfWidth,
    upper: center + halfWidth,
    halfWidth,
  };
}

export function intervalFits(interval, lower, upper) {
  return interval.lower >= lower && interval.upper <= upper;
}

