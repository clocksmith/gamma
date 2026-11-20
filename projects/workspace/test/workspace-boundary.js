import { realpathSync } from 'node:fs';
import { isBuiltin, registerHooks } from 'node:module';
import { isAbsolute, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = realpathSync(fileURLToPath(new URL('..', import.meta.url)));
function contained(base, path) {
  const rel = relative(base, path);
  return rel === '' || (rel !== '..' && !rel.startsWith(`..${sep}`) && !isAbsolute(rel));
}

// Test-only gate on the real, transitive Node resolution of production
// entrypoints. An operator-supplied workflow module is intentionally not tested.
registerHooks({
  resolve(specifier, context, nextResolve) {
    if (isBuiltin(specifier)) return nextResolve(specifier, context);
    const result = nextResolve(specifier, context);
    if (!result.url.startsWith('file:') || !contained(root, realpathSync(fileURLToPath(result.url)))) {
      throw Error(`Workspace import escapes production package: ${specifier}`);
    }
    return result;
  }
});
