// Explicit Fawn build selection. Artifact identity is launch admission, not GPU
// ownership proof; that additionally requires the composed browser qualification.
import { createHash } from 'node:crypto';
import { readFileSync, realpathSync, statSync } from 'node:fs';
import { posix, win32 } from 'node:path';
// Optional Fawn launch flag ABI only. Stock Chrome has no Fawn/Doe dependency.
function forcedRuntimeArgs(mode, libraryPath) {
  if (mode === 'dawn') return ['--use-webgpu-runtime=dawn'];
  if (mode !== 'doe' || typeof libraryPath !== 'string' || !libraryPath) {
    throw new Error('forced runtime requires dawn, or doe with an explicit library path');
  }
  return ['--use-webgpu-runtime=doe', `--doe-webgpu-library-path=${libraryPath}`,
    ...(process.platform === 'linux' ? ['--gpu-sandbox-start-early'] : [])];
}

const SHA256 = /^[a-f0-9]{64}$/;
const STOCK_CHANNELS = Object.freeze({ 'chromium-headless-shell': undefined, chromium: 'chromium', chrome: 'chrome' });
const BROWSER_CHANNELS = Object.freeze([...Object.keys(STOCK_CHANNELS), 'fawn']);

function artifactShape(artifact, name, platform) {
  const grammar = platform === 'win32' ? win32 : posix;
  if (!artifact || typeof artifact.path !== 'string' || !grammar.isAbsolute(artifact.path)
      || artifact.path.includes('\0')
      || !SHA256.test(artifact.sha256 ?? '')
      || Object.keys(artifact).some(key => !['path', 'sha256'].includes(key))) {
    throw new Error(`${name} requires an absolute path and lowercase SHA-256`);
  }
}

function validateFawnBuild(browser, { platform = process.platform } = {}) {
  if (browser.channel !== 'fawn') {
    if (browser.fawnBuild !== undefined) throw new Error('fawnBuild requires browser.channel=fawn');
    return;
  }
  const build = browser.fawnBuild;
  if (Object.keys(browser).some(key => !['engine', 'transport', 'channel', 'headless', 'persistentProfiles', 'fawnBuild'].includes(key))) {
    throw new Error('Fawn launch accepts only the declared browser configuration');
  }
  if (!build || Object.keys(build).some(key => !['executable', 'dependencies', 'runtime'].includes(key))) {
    throw new Error('browser.channel=fawn requires an explicit fawnBuild');
  }
  artifactShape(build.executable, 'Fawn executable', platform);
  if (!Array.isArray(build.dependencies)) throw new Error('Fawn dependencies must be an explicit array');
  for (const artifact of build.dependencies) artifactShape(artifact, 'Fawn dependency', platform);
  if (!build.runtime || !['doe-c', 'dawn'].includes(build.runtime.mode)) {
    throw new Error('Fawn runtime mode must be doe-c or explicit dawn');
  }
  const keys = build.runtime.mode === 'doe-c' ? ['mode', 'library'] : ['mode'];
  if (Object.keys(build.runtime).some(key => !keys.includes(key))) throw new Error('unexpected Fawn runtime option');
  if (build.runtime.mode === 'doe-c') artifactShape(build.runtime.library, 'Doe C library', platform);
  if (build.runtime.mode === 'doe-c' && build.dependencies.length === 0) {
    throw new Error('Doe C requires an explicit compiler/dependency closure');
  }
}

function verifiedArtifact(artifact) {
  const path = realpathSync.native(artifact.path);
  if (!statSync(path).isFile()) throw new Error(`Fawn artifact is not a file: ${path}`);
  const sha256 = createHash('sha256').update(readFileSync(path)).digest('hex');
  if (sha256 !== artifact.sha256) throw new Error(`Fawn artifact SHA-256 mismatch: ${path}`);
  return Object.freeze({ path, sha256 });
}

function prepareFawnLaunch(browser) {
  validateFawnBuild(browser);
  if (browser.channel !== 'fawn') return null;
  const build = browser.fawnBuild;
  const executable = verifiedArtifact(build.executable);
  const dependencies = build.dependencies.map(verifiedArtifact);
  const library = build.runtime.mode === 'doe-c' ? verifiedArtifact(build.runtime.library) : null;
  const paths = [executable, ...dependencies, ...(library ? [library] : [])].map(value => value.path);
  if (new Set(paths).size !== paths.length) throw new Error('Fawn artifacts must name distinct files');
  const mode = library ? 'doe' : 'dawn';
  const args = forcedRuntimeArgs(mode, library?.path);
  if (process.platform === 'win32') args.push('--do-not-de-elevate');
  return Object.freeze({ executablePath: executable.path, args,
    identity: Object.freeze({ executable, dependencies, library, runtime: build.runtime.mode,
      fallbackAllowed: false }) });
}

function playwrightLaunchOptions(browser) {
  const launch = prepareFawnLaunch(browser);
  if (launch) return { executablePath: launch.executablePath, args: launch.args, chromiumSandbox: true,
    ignoreDefaultArgs: ['--enable-unsafe-swiftshader'] };
  if (!Object.hasOwn(STOCK_CHANNELS, browser.channel)) throw new Error(`unsupported browser channel: ${browser.channel}`);
  return { channel: STOCK_CHANNELS[browser.channel] };
}

export { BROWSER_CHANNELS, validateFawnBuild, prepareFawnLaunch, playwrightLaunchOptions };
