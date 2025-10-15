/**
 * Statistical Analysis for Benchmark Results
 * Provides rigorous statistical methods for analyzing benchmark data
 */

export class StatisticalAnalyzer {
  /**
   * Calculate comprehensive statistics for a set of values
   */
  static calculateStats(values) {
    if (!values || values.length === 0) {
      return null;
    }

    const sorted = [...values].sort((a, b) => a - b);
    const n = sorted.length;
    const mean = values.reduce((a, b) => a + b, 0) / n;

    // Variance and standard deviation
    const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / n;
    const stdDev = Math.sqrt(variance);

    // Standard error
    const stderr = stdDev / Math.sqrt(n);

    // Percentiles
    const p25 = this.percentile(sorted, 25);
    const p50 = this.percentile(sorted, 50); // median
    const p75 = this.percentile(sorted, 75);
    const p95 = this.percentile(sorted, 95);
    const p99 = this.percentile(sorted, 99);

    // Interquartile range
    const iqr = p75 - p25;

    // Min and max
    const min = sorted[0];
    const max = sorted[n - 1];

    // Range
    const range = max - min;

    // Coefficient of variation (CV)
    const cv = mean !== 0 ? (stdDev / mean) * 100 : 0;

    return {
      count: n,
      mean,
      median: p50,
      stdDev,
      stderr,
      variance,
      min,
      max,
      range,
      percentiles: { p25, p50, p75, p95, p99 },
      iqr,
      cv,
      outliers: this.detectOutliers(values, mean, stdDev)
    };
  }

  /**
   * Calculate percentile value
   */
  static percentile(sortedArray, p) {
    if (sortedArray.length === 0) return 0;
    if (p <= 0) return sortedArray[0];
    if (p >= 100) return sortedArray[sortedArray.length - 1];

    const index = (p / 100) * (sortedArray.length - 1);
    const lower = Math.floor(index);
    const upper = Math.ceil(index);
    const weight = index - lower;

    return sortedArray[lower] * (1 - weight) + sortedArray[upper] * weight;
  }

  /**
   * Detect outliers using IQR method and z-score
   */
  static detectOutliers(values, mean, stdDev, threshold = 3) {
    const sorted = [...values].sort((a, b) => a - b);
    const p25 = this.percentile(sorted, 25);
    const p75 = this.percentile(sorted, 75);
    const iqr = p75 - p25;

    const lowerBoundIQR = p25 - 1.5 * iqr;
    const upperBoundIQR = p75 + 1.5 * iqr;

    return values.map((val, idx) => {
      const zScore = stdDev !== 0 ? Math.abs((val - mean) / stdDev) : 0;
      const isOutlierIQR = val < lowerBoundIQR || val > upperBoundIQR;
      const isOutlierZScore = zScore > threshold;

      return {
        index: idx,
        value: val,
        isOutlier: isOutlierIQR || isOutlierZScore,
        method: isOutlierIQR ? 'IQR' : (isOutlierZScore ? 'Z-Score' : null),
        zScore
      };
    }).filter(o => o.isOutlier);
  }

  /**
   * Calculate confidence interval for mean
   */
  static confidenceInterval(values, confidenceLevel = 0.95) {
    const stats = this.calculateStats(values);
    if (!stats) return null;

    // Use t-distribution for small samples (n < 30)
    const df = stats.count - 1;
    const tValue = this.tValue(confidenceLevel, df);
    const marginOfError = tValue * stats.stderr;

    return {
      mean: stats.mean,
      lower: stats.mean - marginOfError,
      upper: stats.mean + marginOfError,
      marginOfError,
      confidenceLevel
    };
  }

  /**
   * Approximate t-value for confidence intervals
   * Uses approximation for common confidence levels
   */
  static tValue(confidenceLevel, df) {
    // Simplified t-values for common confidence levels
    // For more accuracy, use a proper t-distribution library
    const alpha = 1 - confidenceLevel;

    if (df >= 30) {
      // Use z-values for large samples
      if (confidenceLevel === 0.90) return 1.645;
      if (confidenceLevel === 0.95) return 1.96;
      if (confidenceLevel === 0.99) return 2.576;
    }

    // Approximate t-values for small samples (df < 30)
    const tTable = {
      0.95: [12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228,
             2.201, 2.179, 2.160, 2.145, 2.131, 2.120, 2.110, 2.101, 2.093, 2.086,
             2.080, 2.074, 2.069, 2.064, 2.060, 2.056, 2.052, 2.048, 2.045],
      0.99: [63.657, 9.925, 5.841, 4.604, 4.032, 3.707, 3.499, 3.355, 3.250, 3.169,
             3.106, 3.055, 3.012, 2.977, 2.947, 2.921, 2.898, 2.878, 2.861, 2.845,
             2.831, 2.819, 2.807, 2.797, 2.787, 2.779, 2.771, 2.763, 2.756]
    };

    const table = tTable[confidenceLevel] || tTable[0.95];
    return df < table.length ? table[df - 1] : 1.96;
  }

  /**
   * Perform t-test to compare two sets of values
   * Returns whether the difference is statistically significant
   */
  static tTest(values1, values2, alpha = 0.05) {
    const stats1 = this.calculateStats(values1);
    const stats2 = this.calculateStats(values2);

    if (!stats1 || !stats2) return null;

    // Welch's t-test (doesn't assume equal variances)
    const meanDiff = stats1.mean - stats2.mean;
    const se = Math.sqrt(
      (stats1.variance / stats1.count) +
      (stats2.variance / stats2.count)
    );

    const tStat = se !== 0 ? meanDiff / se : 0;

    // Welch-Satterthwaite degrees of freedom
    const df = Math.pow(
      (stats1.variance / stats1.count) + (stats2.variance / stats2.count),
      2
    ) / (
      Math.pow(stats1.variance / stats1.count, 2) / (stats1.count - 1) +
      Math.pow(stats2.variance / stats2.count, 2) / (stats2.count - 1)
    );

    // Critical value (two-tailed)
    const criticalValue = this.tValue(1 - alpha, Math.floor(df));
    const isSignificant = Math.abs(tStat) > criticalValue;

    // Calculate effect size (Cohen's d)
    const pooledStdDev = Math.sqrt(
      ((stats1.count - 1) * stats1.variance + (stats2.count - 1) * stats2.variance) /
      (stats1.count + stats2.count - 2)
    );
    const cohensD = pooledStdDev !== 0 ? meanDiff / pooledStdDev : 0;

    return {
      meanDiff,
      tStatistic: tStat,
      degreesOfFreedom: df,
      isSignificant,
      pValue: this.approximatePValue(Math.abs(tStat), df),
      alpha,
      cohensD,
      effectSize: this.interpretEffectSize(cohensD)
    };
  }

  /**
   * Approximate p-value from t-statistic
   */
  static approximatePValue(t, df) {
    // Very rough approximation
    if (df >= 30) {
      // Use standard normal approximation
      const z = t;
      return 2 * (1 - this.normalCDF(z));
    }

    // For small samples, use conservative estimate
    if (t < 1.5) return 0.2;
    if (t < 2.0) return 0.05;
    if (t < 2.5) return 0.02;
    if (t < 3.0) return 0.01;
    return 0.001;
  }

  /**
   * Standard normal CDF approximation
   */
  static normalCDF(x) {
    const t = 1 / (1 + 0.2316419 * Math.abs(x));
    const d = 0.3989423 * Math.exp(-x * x / 2);
    const prob = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))));
    return x > 0 ? 1 - prob : prob;
  }

  /**
   * Interpret Cohen's d effect size
   */
  static interpretEffectSize(d) {
    const absD = Math.abs(d);
    if (absD < 0.2) return 'negligible';
    if (absD < 0.5) return 'small';
    if (absD < 0.8) return 'medium';
    return 'large';
  }

  /**
   * Calculate correlation between two variables
   */
  static correlation(values1, values2) {
    if (values1.length !== values2.length || values1.length === 0) {
      return null;
    }

    const n = values1.length;
    const mean1 = values1.reduce((a, b) => a + b, 0) / n;
    const mean2 = values2.reduce((a, b) => a + b, 0) / n;

    let numerator = 0;
    let sum1Sq = 0;
    let sum2Sq = 0;

    for (let i = 0; i < n; i++) {
      const diff1 = values1[i] - mean1;
      const diff2 = values2[i] - mean2;
      numerator += diff1 * diff2;
      sum1Sq += diff1 * diff1;
      sum2Sq += diff2 * diff2;
    }

    const denominator = Math.sqrt(sum1Sq * sum2Sq);
    const r = denominator !== 0 ? numerator / denominator : 0;

    return {
      coefficient: r,
      strength: this.interpretCorrelation(r),
      rSquared: r * r
    };
  }

  /**
   * Interpret correlation coefficient
   */
  static interpretCorrelation(r) {
    const absR = Math.abs(r);
    if (absR < 0.1) return 'negligible';
    if (absR < 0.3) return 'weak';
    if (absR < 0.5) return 'moderate';
    if (absR < 0.7) return 'strong';
    return 'very strong';
  }

  /**
   * Analyze trends over time
   */
  static analyzeTrend(values) {
    const n = values.length;
    if (n < 2) return null;

    // Simple linear regression
    const x = Array.from({ length: n }, (_, i) => i);
    const y = values;

    const meanX = x.reduce((a, b) => a + b, 0) / n;
    const meanY = y.reduce((a, b) => a + b, 0) / n;

    let numerator = 0;
    let denominator = 0;

    for (let i = 0; i < n; i++) {
      numerator += (x[i] - meanX) * (y[i] - meanY);
      denominator += Math.pow(x[i] - meanX, 2);
    }

    const slope = denominator !== 0 ? numerator / denominator : 0;
    const intercept = meanY - slope * meanX;

    // Calculate R²
    const predictions = x.map(xi => slope * xi + intercept);
    const ssRes = y.reduce((sum, yi, i) => sum + Math.pow(yi - predictions[i], 2), 0);
    const ssTot = y.reduce((sum, yi) => sum + Math.pow(yi - meanY, 2), 0);
    const rSquared = ssTot !== 0 ? 1 - (ssRes / ssTot) : 0;

    return {
      slope,
      intercept,
      rSquared,
      trend: slope > 0.01 ? 'increasing' : (slope < -0.01 ? 'decreasing' : 'stable'),
      percentChange: meanY !== 0 ? ((values[n - 1] - values[0]) / values[0]) * 100 : 0
    };
  }

  /**
   * Perform ANOVA (Analysis of Variance) for multiple groups
   */
  static anova(groups) {
    if (groups.length < 2) return null;

    // Calculate grand mean
    const allValues = groups.flat();
    const grandMean = allValues.reduce((a, b) => a + b, 0) / allValues.length;

    // Calculate between-group variance (SSB)
    let ssb = 0;
    for (const group of groups) {
      const groupMean = group.reduce((a, b) => a + b, 0) / group.length;
      ssb += group.length * Math.pow(groupMean - grandMean, 2);
    }

    // Calculate within-group variance (SSW)
    let ssw = 0;
    for (const group of groups) {
      const groupMean = group.reduce((a, b) => a + b, 0) / group.length;
      for (const value of group) {
        ssw += Math.pow(value - groupMean, 2);
      }
    }

    // Degrees of freedom
    const dfBetween = groups.length - 1;
    const dfWithin = allValues.length - groups.length;

    // Mean squares
    const msb = ssb / dfBetween;
    const msw = dfWithin > 0 ? ssw / dfWithin : 0;

    // F-statistic
    const fStatistic = msw !== 0 ? msb / msw : 0;

    return {
      fStatistic,
      dfBetween,
      dfWithin,
      isSignificant: fStatistic > 3.0, // Rough approximation
      ssb,
      ssw,
      msb,
      msw
    };
  }
}
