// The raw OS result of Node's forced process termination, without inventing
// POSIX signals on Windows. Recovery expectations are shared across platforms.
function abruptExitMatches(exit, platform = process.platform, source) {
  switch (platform) {
    case 'win32':
      // child.kill reports its requested signal in Node's close event, while
      // process.kill(self) terminates with code1. Keep both raw tuples intact
      // and require the matching independently observed request source.
      if (source === 'controller') return exit?.code === null && exit.signal === 'SIGKILL';
      if (source === 'host-hook') return exit?.code === 1 && exit.signal === null;
      return false;
    case 'linux':
    case 'darwin': return exit?.code === null && exit.signal === 'SIGKILL';
    default: return false;
  }
}

function observedKillRequest(request) {
  return request?.signal === 'SIGKILL' && Number.isInteger(request.pid) && request.pid > 0
    && ['controller', 'host-hook'].includes(request.source);
}

function terminationEvidence(exit, request) {
  if (!observedKillRequest(request) || !abruptExitMatches(exit, process.platform, request.source)) {
    throw new Error(`forced termination lacks an observed request/OS exit: ${JSON.stringify({ exit, request })}`);
  }
  return { requestedSignal: request.signal, abrupt: true, hostPid: request.pid, request, rawExit: exit };
}

function terminationMatches(evidence, platform) {
  return evidence?.abrupt === true && observedKillRequest(evidence.request)
    && evidence.requestedSignal === evidence.request.signal && evidence.hostPid === evidence.request.pid
    && abruptExitMatches(evidence.rawExit, platform, evidence.request.source);
}

export { abruptExitMatches, terminationEvidence, terminationMatches };
