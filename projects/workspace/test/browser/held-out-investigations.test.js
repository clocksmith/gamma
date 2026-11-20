// Browser check for the offline held-out workspace investigations: multi-page origin rejection,
// mid-run human takeover generation handoff, and interrupted failover audit reconciliation.
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { runHeldOutAndLiveSuite } from '../../qualification/held-out-and-live-investigations.js';

const outDir = mkdtempSync(join(tmpdir(), 'fawn-heldout-browser-test-'));
try {
  const { report } = await runHeldOutAndLiveSuite({ outDir, offline: true });
  assert.equal(report.summary.allPassed, true);
  assert.equal(report.summary.heldOutCount, 3);
  assert.equal(report.summary.heldOutPassed, 3);
  assert.equal(report.summary.liveSiteCount, 0);
  assert.equal(report.summary.productReleaseQualified, false);
  const [cacheRow, takeoverRow, failoverRow] = report.heldOutInvestigations;
  assert.equal(cacheRow.arms.fawn.ungrantedOriginRejected, true);
  assert.equal(takeoverRow.staleGenerationRejected, true);
  assert.equal(failoverRow.fawnDuplicateSubmissions, 0);
  assert.equal(failoverRow.unguardedRetryDuplicateSubmissions, 1);
  console.log('ok: held-out workspace investigations pass offline on stock Chrome');
} finally {
  rmSync(outDir, { recursive: true, force: true });
}
