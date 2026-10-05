/** Keep the deployment directory when resolving every release resource. */
export function releaseBaseUrl(value) {
  const url = new URL(value);
  if (!['http:', 'https:'].includes(url.protocol)) {
    throw new TypeError('Release URL must use HTTP or HTTPS.');
  }
  url.search = '';
  url.hash = '';
  if (!url.pathname.endsWith('/')) url.pathname += '/';
  return url.href;
}

export function releaseResourceUrl(base, path) {
  // These are release-relative paths; a leading slash must not reset the base.
  const url = new URL(path.replace(/^\/+/, ''), releaseBaseUrl(base));
  if (!url.href.startsWith(releaseBaseUrl(base))) {
    throw new TypeError('Release resource escapes its deployment directory.');
  }
  return url.href;
}

/** A static-host fallback is exclusion only when it is exact known public HTML. */
export function excludedResourceOutcome(status, bytes, publicFallbacks = []) {
  if ([403, 404, 410].includes(status)) return 'http-exclusion';
  if (status === 200 && publicFallbacks.some(fallback => bytes.equals(fallback))) {
    return 'public-host-fallback';
  }
  throw new Error(`Internal resource unexpectedly served (HTTP ${status}).`);
}
