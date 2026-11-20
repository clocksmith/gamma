// Local workspace surface ABI. This describes the existing Chromium port only:
// it grants no authority and adds no operations to the workspace wire protocol.
export const CHROMIUM_SURFACE_V1 = 'gamma.workspace.chromium/v1';

const REQUIRED = Object.freeze([
  'openWorkspace', 'snapshot', 'probeUrl', 'probeElement', 'execute', 'close',
]);
const OPTIONAL = Object.freeze(['listPages', 'openPage', 'selectRegion', 'focusPage']);

/**
 * Validate a service-owned adapter before restoring or opening a workspace.
 *
 * openWorkspace/close own surface lifecycle; snapshot/probeUrl/probeElement
 * observe live state. execute applies a request the service already admitted
 * and journaled; the service alone decides outcome and reconciliation.
 * Page-management operations are optional on existing single-page ports.
 *
 * Existing fixture and wrapper adapters that do not declare a version use
 * the v1 shape. An explicit unknown version is rejected without fallback.
 * No adapter is selected from client input.
 */
export function requireChromiumSurfaceV1(adapter) {
  if (adapter === null || typeof adapter !== 'object') {
    throw new TypeError('Workspace adapter must implement the Chromium surface contract');
  }
  const version = adapter.surfaceVersion;
  if (version !== undefined && version !== CHROMIUM_SURFACE_V1) {
    throw new TypeError('Unsupported workspace surface contract version');
  }
  for (const method of REQUIRED) {
    if (typeof adapter[method] !== 'function') {
      throw new TypeError(`Workspace surface is missing required operation: ${method}`);
    }
  }
  for (const method of OPTIONAL) {
    if (adapter[method] != null && typeof adapter[method] !== 'function') {
      throw new TypeError(`Workspace surface operation must be callable: ${method}`);
    }
  }
  return adapter;
}
