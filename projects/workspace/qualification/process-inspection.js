// Operating-system process and socket evidence, independent of adapter claims.
import { execFileSync, spawnSync } from 'node:child_process';
import { closeSync, existsSync, openSync, readFileSync, readdirSync, readlinkSync, readSync, realpathSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const COMMAND_OPTIONS = Object.freeze({ encoding: 'utf8', timeout: 15000, maxBuffer: 16 * 1024 * 1024, windowsHide: true });

function powershell(script) {
  const prelude = "$ErrorActionPreference='Stop'; [Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false); ";
  return execFileSync('powershell.exe', ['-NoProfile', '-NonInteractive', '-EncodedCommand',
    Buffer.from(prelude + script, 'utf16le').toString('base64')], COMMAND_OPTIONS).trim();
}

function linuxProcesses() {
  return readdirSync('/proc').filter((name) => /^\d+$/.test(name)).flatMap((name) => {
    try {
      const stat = readFileSync(`/proc/${name}/stat`, 'utf8');
      const fields = stat.slice(stat.lastIndexOf(')') + 2).split(' ');
      return [{ pid: Number(name), parentPid: Number(fields[1]), startedAt: fields[19],
        executable: realpathSync.native(`/proc/${name}/exe`),
        commandLine: readFileSync(`/proc/${name}/cmdline`, 'utf8').replaceAll('\0', ' ') }];
    } catch {
      // Unrelated protected processes and processes exiting during the snapshot.
      return [];
    }
  });
}

function macProcesses() {
  const rows = execFileSync('/bin/ps', ['-ww', '-axo', 'pid=,ppid=,stat=,lstart=,comm='],
    { ...COMMAND_OPTIONS, env: { ...process.env, LC_ALL: 'C' } });
  return rows.trim().split('\n').flatMap((line) => {
    const match = /^\s*(\d+)\s+(\d+)\s+(\S+)\s+(\S+\s+\S+\s+\d+\s+\S+\s+\d{4})\s+(.+)$/.exec(line);
    if (!match) throw new Error(`unrecognized process row: ${line}`);
    // A zombie has no live executable or sockets; ps renders its old comm in
    // parentheses, which must never be interpreted as a relative image path.
    if (/[ZE]/.test(match[3])) return [];
    return [{ pid: Number(match[1]), parentPid: Number(match[2]), startedAt: match[4], executable: match[5] }];
  });
}

function windowsProcesses() {
  const text = powershell('$rows=@(Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,ExecutablePath,CommandLine,CreationDate); '
    + 'ConvertTo-Json -InputObject $rows -Compress -Depth 3');
  return JSON.parse(text).map((row) => ({ pid: row.ProcessId, parentPid: row.ParentProcessId,
    executable: row.ExecutablePath, commandLine: row.CommandLine ?? '', startedAt: row.CreationDate }));
}

function processSnapshot() {
  switch (process.platform) {
    case 'linux': return linuxProcesses();
    case 'darwin': return macProcesses();
    case 'win32': return windowsProcesses();
    default: throw new Error(`process inspection is unsupported on ${process.platform}`);
  }
}

function descendantRows(rootPid, snapshot) {
  const found = [];
  const seen = new Set([rootPid]);
  const pending = [rootPid];
  while (pending.length) {
    const parentPid = pending.shift();
    for (const row of snapshot) {
      if (row.parentPid !== parentPid || seen.has(row.pid)) continue;
      seen.add(row.pid);
      found.push(row);
      pending.push(row.pid);
    }
  }
  return found;
}

function descendants(rootPid) {
  return descendantRows(rootPid, processSnapshot()).map((row) => row.pid);
}

function lsof(args) {
  const result = spawnSync('/usr/sbin/lsof', ['-nP', ...args], COMMAND_OPTIONS);
  if (result.error) throw result.error;
  // lsof returns1 if any requested PID/file selection has no match, including
  // a helper that exited during inspection. Retain partial matches; diagnostics
  // still fail closed, and live browser roots must have text mappings below.
  if (result.status !== 0 && !(result.status === 1 && !result.stderr.trim())) {
    throw new Error(`lsof ${args.join(' ')} failed: ${result.stderr.trim() || result.status}`);
  }
  return result.stdout;
}

function linuxListeners(pids) {
  const tables = ['/proc/net/tcp', '/proc/net/tcp6'].filter(existsSync);
  if (!tables.length) throw new Error('TCP listener tables are unavailable');
  const listening = new Set();
  for (const table of tables) {
    for (const line of readFileSync(table, 'utf8').trim().split('\n').slice(1)) {
      const fields = line.trim().split(/\s+/);
      if (fields[3] === '0A') listening.add(fields[9]);
    }
  }
  let count = 0;
  for (const pid of pids) {
    try {
      for (const fd of readdirSync(`/proc/${pid}/fd`)) {
        try {
          const match = /^socket:\[(\d+)\]$/.exec(readlinkSync(`/proc/${pid}/fd/${fd}`));
          if (match && listening.has(match[1])) count++;
        } catch (error) {
          if (error.code !== 'ENOENT') throw error;
        }
      }
    } catch (error) {
      if (error.code !== 'ENOENT') throw error;
    }
  }
  return count;
}

function listenerCount(pids) {
  if (!pids.length) return 0;
  switch (process.platform) {
    case 'linux': return linuxListeners(pids);
    case 'darwin': return lsof(['-a', '-p', pids.join(','), '-iTCP', '-sTCP:LISTEN', '-Fpn'])
      .split('\n').filter((line) => line.startsWith('n')).length;
    case 'win32': {
      const ids = pids.map((pid) => {
        if (!Number.isInteger(pid) || pid <= 0) throw new Error('invalid process id');
        return pid;
      });
      return Number(powershell(`$ids=@(${ids.join(',')}); `
        + '@(Get-NetTCPConnection -ErrorAction Stop | Where-Object { $_.State -eq "Listen" -and $ids -contains $_.OwningProcess }).Count'));
    }
    default: throw new Error(`socket inspection is unsupported on ${process.platform}`);
  }
}

/** Loaded text vnodes establish the actual macOS executable and framework bytes. */
function macTextImages(pids) {
  return parseMacTextImages(lsof(['-a', '-p', pids.join(','), '-d', 'txt', '-Fpn']), pids);
}

function parseMacTextImages(text, pids) {
  const images = new Map();
  let pid;
  for (const line of text.split('\n')) {
    if (line.startsWith('p')) {
      pid = Number(line.slice(1));
      if (!pids.includes(pid)) throw new Error(`unrequested module process ${pid}`);
      images.set(pid, []);
    } else if (line.startsWith('n')) {
      if (!images.has(pid)) throw new Error('module path without an owned process');
      images.get(pid).push(line.slice(1));
    }
  }
  return images;
}

function parseWindowsModuleImages(text, pids) {
  const images = new Map();
  const entries = JSON.parse(text);
  if (!Array.isArray(entries)) throw new Error('expected module process array');
  for (const entry of entries) {
    if (!Number.isInteger(entry.pid) || !pids.includes(entry.pid) || images.has(entry.pid)
        || !Array.isArray(entry.paths) || entry.paths.some(path => typeof path !== 'string' || !path)) {
      throw new Error('invalid or unrequested module process');
    }
    images.set(entry.pid, entry.paths);
  }
  return images;
}

function windowsModuleImages(pids) {
  const text = powershell(`$rows=@(foreach($id in @(${pids.join(',')})) { `
    + '$process=Get-Process -Id $id -ErrorAction SilentlyContinue; if($null -ne $process) { '
    + '[pscustomobject]@{pid=$id;paths=@($process.Modules | ForEach-Object {$_.FileName})} } }); '
    + 'ConvertTo-Json -InputObject $rows -Compress -Depth 4');
  return parseWindowsModuleImages(text, pids);
}

function parseLinuxExecutableMappings(text) {
  const paths = new Set();
  const unavailable = [];
  for (const line of text.trim().split('\n').filter(Boolean)) {
    const match = /^[a-f\d]+-[a-f\d]+\s+([rwxps-]{4})\s+\S+\s+\S+\s+\d+(?:\s+(.*))?$/i.exec(line);
    if (!match) throw new Error(`unrecognized executable mapping: ${line}`);
    if (!match[1].includes('x') || !match[2]?.startsWith('/')) continue;
    const path = match[2].replace(/\\([0-7]{3})/g, (_whole, digits) => String.fromCharCode(parseInt(digits, 8)));
    if (path.endsWith(' (deleted)')) unavailable.push({ path, reason: 'deleted executable mapping' });
    else paths.add(path);
  }
  return { paths: [...paths], unavailable };
}

function linuxModuleImages(pids, unavailable) {
  const images = new Map();
  for (const pid of pids) {
    try {
      const parsed = parseLinuxExecutableMappings(readFileSync(`/proc/${pid}/maps`, 'utf8'));
      images.set(pid, parsed.paths);
      unavailable.push(...parsed.unavailable.map(entry => ({ pid, ...entry })));
    } catch (error) {
      if (error.code !== 'ENOENT') throw error;
    }
  }
  return images;
}

function isCodeImage(path) {
  const descriptor = openSync(path, 'r');
  try {
    const bytes = Buffer.alloc(4);
    if (readSync(descriptor, bytes, 0, 4, 0) !== 4) return false;
    // ELF, PE and both byte orders of thin/fat Mach-O. lsof txt also lists
    // resources and dyld caches, which are not separately readable code images.
    return ['7f454c46', 'feedface', 'cefaedfe', 'feedfacf', 'cffaedfe', 'cafebabe', 'bebafeca',
      'cafebabf', 'bfbafeca'].includes(bytes.toString('hex')) || bytes.subarray(0, 2).toString() === 'MZ';
  } finally { closeSync(descriptor); }
}

function canonicalOwnedRows(hostPid) {
  let rows = descendantRows(hostPid, processSnapshot());
  if (process.platform === 'darwin') {
    const helper = fileURLToPath(new URL('./process-paths-macos.py', import.meta.url));
    const paths = JSON.parse(execFileSync('python3', [helper, JSON.stringify(rows.map(row => row.pid))], COMMAND_OPTIONS));
    rows = rows.filter(row => paths[row.pid]).map(row => ({ ...row, executable: paths[row.pid] }));
    if (rows.length) {
      const commands = spawnSync('/bin/ps', ['-ww', '-p', rows.map(row => row.pid).join(','), '-o', 'pid=,args='], COMMAND_OPTIONS);
      if (commands.error) throw commands.error;
      if (commands.status !== 0 && !(commands.status === 1 && !commands.stderr.trim())) {
        throw new Error(`owned process arguments unavailable: ${commands.stderr.trim()}`);
      }
      const byPid = new Map(commands.stdout.split('\n').flatMap(line => {
        const match = /^\s*(\d+)\s+(.*)$/.exec(line);
        return match ? [[Number(match[1]), match[2]]] : [];
      }));
      rows = rows.filter(row => byPid.has(row.pid)).map(row => ({ ...row, commandLine: byPid.get(row.pid) }));
    }
  }
  return rows.map(row => {
    if (!row.executable || !row.startedAt) throw new Error(`process identity unavailable for ${row.pid}`);
    return { ...row, executable: realpathSync.native(row.executable) };
  });
}

function inspectProcesses(hostPid) {
  let rows = canonicalOwnedRows(hostPid);
  const roots = rows.filter((row) => row.parentPid === hostPid);
  if (!roots.length) throw new Error(`no live browser process belongs to host ${hostPid}`);
  const pids = rows.map(row => row.pid);
  const unavailableModuleMappings = [];
  const images = process.platform === 'darwin' ? macTextImages(pids)
    : process.platform === 'win32' ? windowsModuleImages(pids) : linuxModuleImages(pids, unavailableModuleMappings);
  // Reject PID reuse, reparenting and image replacement across the kernel
  // observation. Exited helpers may be omitted; every root must remain proven.
  const current = canonicalOwnedRows(hostPid);
  rows = rows.filter(row => current.some(live => live.pid === row.pid && live.parentPid === row.parentPid
    && live.startedAt === row.startedAt && live.executable === row.executable));
  if (roots.some(root => !rows.includes(root))) throw new Error('browser root changed during module observation');
  for (const row of rows) {
    const paths = images.get(row.pid) ?? [];
    const observed = paths.some(path => {
      try { return realpathSync.native(path) === row.executable; } catch { return false; }
    });
    if (!observed) {
      // A short-lived helper may have exited during inspection. A root must
      // retain independently observed kernel text identity to qualify.
      if (roots.includes(row)) throw new Error(`browser executable not observed in kernel text mappings: ${row.executable}`);
    }
  }
  const modules = new Set();
  const mapped = new Set();
  const mappedCodeModuleObservations = [];
  for (const row of rows) {
    const observedPaths = new Set();
    for (const path of images.get(row.pid) ?? []) {
      try {
        const real = realpathSync.native(path);
        if (observedPaths.has(real)) continue;
        observedPaths.add(real);
        if (!isCodeImage(real)) continue;
        mapped.add(real);
        mappedCodeModuleObservations.push({ path: real, pid: row.pid, parentPid: row.parentPid,
          executable: row.executable, startedAt: row.startedAt,
          source: process.platform === 'darwin' ? 'lsof-txt' : process.platform === 'win32' ? 'process-modules' : 'proc-executable-map' });
      } catch (error) {
        if (!['ENOENT', 'EACCES', 'EPERM'].includes(error.code)) throw error;
        unavailableModuleMappings.push({ pid: row.pid, path, reason: error.code });
      }
    }
  }
  // Preserve the existing main-browser image/framework digest. Descendant
  // provider ownership is a separate observation and must not alter that key.
  if (process.platform === 'darwin') {
    for (const root of roots) {
      const bundle = root.executable.split('.app/')[0] + '.app/';
      for (const path of images.get(root.pid) ?? []) {
        if (!path.startsWith(bundle)) continue;
        const real = realpathSync.native(path);
        const framework = /\/([^/]+)\.framework\/(?:Versions\/[^/]+\/)?([^/]+)$/.exec(real);
        // Chromium's main framework is executable code; txt also contains
        // lazily mapped resources/libraries, recorded separately below.
        if (real === root.executable || (framework && framework[1] === framework[2])) modules.add(real);
      }
    }
  } else if (process.platform === 'win32') {
    for (const root of roots) {
      for (const path of images.get(root.pid) ?? []) {
        const real = realpathSync.native(path);
        if (real === root.executable || /[\\/]chrome\.dll$/i.test(real)) modules.add(real);
      }
    }
  }
  const listeningTcpSockets = listenerCount(rows.map((row) => row.pid));
  if (!Number.isInteger(listeningTcpSockets) || listeningTcpSockets < 0) throw new Error('invalid socket inspection result');
  return { rows, roots, codeModules: [...modules], mappedCodeModules: [...mapped], mappedCodeModuleObservations,
    unavailableModuleMappings, listeningTcpSockets };
}

function processesUsing(path) {
  let rows;
  if (process.platform === 'darwin') {
    const commands = execFileSync('/bin/ps', ['-ww', '-axo', 'pid=,ppid=,args='], COMMAND_OPTIONS);
    rows = commands.split('\n').flatMap((line) => {
      const match = /^\s*(\d+)\s+(\d+)\s+(.*)$/.exec(line);
      return match ? [{ pid: Number(match[1]), parentPid: Number(match[2]), commandLine: match[3] }] : [];
    });
  } else rows = processSnapshot();
  // A node -e verifier (and its shell ancestors) may name the profile in its
  // own command. They are observers, not a surviving browser/profile claimant.
  const parents = new Map(rows.map(row => [row.pid, row.parentPid]));
  const observers = new Set();
  for (let pid = process.pid; pid && !observers.has(pid); pid = parents.get(pid)) observers.add(pid);
  return rows.filter(row => !observers.has(row.pid) && row.commandLine.includes(path)).map(row => row.pid);
}

function windowsFileVersion(path) {
  return powershell(`(Get-Item -LiteralPath '${path.replaceAll("'", "''")}').VersionInfo.ProductVersion`);
}

export { descendants, inspectProcesses, processesUsing, windowsFileVersion,
  parseLinuxExecutableMappings, parseMacTextImages, parseWindowsModuleImages };
