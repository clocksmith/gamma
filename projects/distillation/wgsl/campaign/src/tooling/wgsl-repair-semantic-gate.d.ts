export declare const WGSL_REPAIR_SEMANTIC_READINESS_SCHEMA_ID:
  'doppler.wgsl-repair-semantic-readiness/v1';
export declare const WGSL_REPAIR_SEMANTIC_READINESS_V2_SCHEMA_ID:
  'doppler.wgsl-repair-semantic-readiness/v2';

export interface WgslSemanticTolerance {
  mode: 'exact' | 'numeric';
  absTolerance: number;
  relTolerance: number;
}

export interface WgslNumericAgreementResult {
  pass: boolean;
  expectedElements: number;
  actualElements: number;
  mismatchCount: number;
  maxAbsError: number | null;
  maxRelError: number | null;
  mismatches: Array<Record<string, unknown>>;
}

export interface WgslSemanticTaskEvidence {
  taskId?: string | null;
  responseContractPass?: boolean;
  compilation?: { status?: string };
  variants?: Array<Record<string, unknown>>;
  historicalRegressionsPass?: boolean;
}

export interface WgslSemanticEvidenceState {
  experimentId: 'doppler-wgsl-repair-v13';
  policy: Record<string, unknown>;
  adapterPortability: Record<string, unknown>;
  candidate: Record<string, unknown>;
  populations: Record<string, unknown>;
  implementation: Record<string, unknown>;
  claimBoundary: string;
}

export interface WgslSemanticReadinessV2Options {
  policy: Record<string, unknown>;
  evidenceState: WgslSemanticEvidenceState;
  policyVerified?: boolean;
  predecessorVerified?: boolean;
  preservationReceipt?: Record<string, unknown> | null;
  adapterPortabilityReceipt?: Record<string, unknown> | null;
  adapterPortabilityReceiptVerified?: boolean;
  populationVerification?: Record<string, boolean>;
  selectionReceipt?: Record<string, unknown> | null;
  selectionReceiptVerified?: boolean;
  seedConfirmationReceipt?: Record<string, unknown> | null;
  seedConfirmationReceiptVerified?: boolean;
  implementationVerification?: Record<string, boolean>;
  taskEvidence?: WgslSemanticTaskEvidence[];
}

export declare function evaluateNumericAgreement(
  expectedValues: Iterable<number> | ArrayLike<number> | null | undefined,
  actualValues: Iterable<number> | ArrayLike<number> | null | undefined,
  tolerance: WgslSemanticTolerance
): WgslNumericAgreementResult;

export declare function normalizeWgslSemanticEvidenceValue(value: unknown): unknown;

export declare function hashWgslSemanticEvidenceValue(value: unknown): string;

export declare function evaluateWgslSemanticTaskEvidence(
  policy: Record<string, unknown>,
  evidence: WgslSemanticTaskEvidence
): Record<string, unknown> & { pass: boolean; blockers: string[]; resultHash: string };

export declare function evaluateWgslSemanticReadiness(
  options?: Record<string, unknown>
): Record<string, unknown> & { decision: string; blockers: string[]; receiptHash: string };

export declare function evaluateWgslSemanticReadinessV2(
  options: WgslSemanticReadinessV2Options
): Record<string, unknown> & { decision: string; blockers: string[]; receiptHash: string };
