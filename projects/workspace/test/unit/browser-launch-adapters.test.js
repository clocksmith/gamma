// Actual child-process launch admission; this controlled executable is not a GPU/browser proof.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { chmodSync, mkdtempSync, readFileSync, writeFileSync, rmSync, existsSync, realpathSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { loadServiceConfig } from '../../src/config.js';
import { createPlaywrightAdapter } from '../../src/adapters/playwright-adapter.js';
import { createCdpAdapter } from '../../src/adapters/cdp-adapter.js';

if (process.platform === 'win32') {
  console.log('skip: POSIX controlled executable; Windows requires its native launcher controls');
} else {
  const root = realpathSync(mkdtempSync(join(tmpdir(), 'fawn-adapter-launch-')));
  const hash = bytes => createHash('sha256').update(bytes).digest('hex');
  try {
    for (const [name, factory] of [['playwright', createPlaywrightAdapter], ['cdp', createCdpAdapter]]) {
      const record = join(root, `${name}.json`);
      const path = join(root, `${name} controlled executable`);
      const script = `#!${process.execPath}\nrequire('node:fs').writeFileSync(${JSON.stringify(record)}, JSON.stringify({pid:process.pid,args:process.argv.slice(2)}));\n${name === 'playwright' ? 'process.exit(17);' : 'setInterval(()=>{},1000);'}\n`;
      writeFileSync(path, script);
      chmodSync(path, 0o700);
      const config = structuredClone(loadServiceConfig());
      config.dispatch.actionTimeoutMs = 1500;
      config.browser.channel = 'fawn';
      const library = join(root, `${name} C runtime`);
      const compiler = join(root, `${name} C compiler`);
      writeFileSync(library, 'library');
      writeFileSync(compiler, 'compiler');
      config.browser.fawnBuild = { executable: { path, sha256: hash(script) },
        dependencies: [{ path: compiler, sha256: hash('compiler') }],
        runtime: { mode: 'doe-c', library: { path: library, sha256: hash('library') } } };
      const adapter = factory({ config, profileRoot: join(root, name, 'profiles'), artifactRoot: join(root, name, 'artifacts') });
      try {
        await assert.rejects(adapter.openWorkspace('controlled'));
        assert.equal(existsSync(record), true, `${name} must launch the selected executable`);
        const observed = JSON.parse(readFileSync(record));
        assert.ok(observed.args.includes('--use-webgpu-runtime=doe'));
        assert.ok(observed.args.includes(`--doe-webgpu-library-path=${library}`));
        assert.ok(observed.args.includes('--remote-debugging-pipe'));
        assert.equal(observed.args.some(arg => arg === '--no-sandbox'), false);
        assert.equal(observed.args.includes('--enable-unsafe-swiftshader'), false);
        assert.equal(observed.args.includes('--gpu-sandbox-start-early'), process.platform === 'linux');
        assert.throws(() => process.kill(observed.pid, 0), { code: 'ESRCH' }, `${name} must reap failed launch`);
        // A modified image must be rejected before the next spawn, rather than falling back.
        rmSync(record);
        writeFileSync(path, `${script}// changed\n`);
        await assert.rejects(adapter.openWorkspace('tampered'), /SHA-256 mismatch/);
        assert.equal(existsSync(record), false);
      } finally {
        await adapter.close();
      }
    }
    console.log('ok: both adapters launch the selected image over a private pipe, preserve sandbox and reap failed handshakes');
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
}
