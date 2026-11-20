// Real POSIX pipe peer for adapter lifetime controls. It is not a browser or GPU.
const fs = require('node:fs');
const { scenario, record, timeoutMs } = global.CONTROL;
const observed = { pid: process.pid, commands: [] };
const save = () => fs.writeFileSync(record, JSON.stringify(observed));
save();
let buffer = '';
let downloadPath;
let location = 'about:blank';
const send = messages => fs.writeSync(4, messages.map(message => JSON.stringify(message) + '\0').join(''));
const input = fs.createReadStream(null, { fd: 3, autoClose: false });
input.on('data', chunk => {
  buffer += chunk.toString('utf8');
  let end;
  while ((end = buffer.indexOf('\0')) !== -1) {
    const command = JSON.parse(buffer.slice(0, end));
    buffer = buffer.slice(end + 1);
    observed.commands.push(command.method + (command.params.type ? ':' + command.params.type : ''));
    save();
    const reply = result => ({ id: command.id, result });
    const reject = () => send([{ id: command.id, error: { code: -32000, message: 'controlled command rejection' } }]);
    // A browser that acknowledges the close and then never exits, as stock Chrome can for minutes.
    if (command.method === 'Browser.close' && scenario === 'close-stalls') { send([reply({})]); continue; }
    if (command.method === 'Browser.close') { send([reply({})]); process.exit(0); }
    if (command.method === 'Target.getTargets') { send([reply({ targetInfos: [{ type: 'page', targetId: 'page' }] })]); continue; }
    if (command.method === 'Target.attachToTarget') { send([reply({ sessionId: 'session' })]); continue; }
    if (command.method === 'Browser.setDownloadBehavior') downloadPath = command.params.downloadPath;
    if (command.method === 'Page.navigate') {
      location = command.params.url;
      if (scenario === 'command-rejection') { reject(); continue; }
      if (scenario === 'navigation-error') { send([reply({ errorText: 'controlled navigation rejection' })]); continue; }
      if (scenario === 'transport-close') { fs.closeSync(4); continue; }
      if (scenario === 'event-timeout') continue;
      send([{ method: 'Page.loadEventFired', params: {}, sessionId: 'session' }, reply({ frameId: 'frame' })]);
      continue;
    }
    if (command.method === 'Runtime.evaluate') {
      const point = command.params.expression.includes('getBoundingClientRect');
      if (point && scenario === 'click-timeout') {
        setTimeout(() => send([reply({ result: { value: { count: 1, x: 4, y: 8 } } })]), timeoutMs * 2);
        continue;
      }
      send([reply({ result: { value: point ? { count: 1, x: 4, y: 8 } : location } })]);
      continue;
    }
    if (command.method === 'Input.dispatchMouseEvent') {
      if (scenario === 'click-rejection') { reject(); continue; }
      if (command.params.type === 'mouseReleased') {
        fs.writeFileSync(require('node:path').join(downloadPath, 'controlled-guid'), 'download proof');
        send([
          { method: 'Browser.downloadWillBegin', params: { guid: 'controlled-guid', suggestedFilename: 'proof.txt' } },
          { method: 'Browser.downloadProgress', params: { guid: 'unrelated-guid', state: 'completed' } },
          { method: 'Browser.downloadProgress', params: { guid: 'controlled-guid', state: 'completed' } },
          reply({}),
        ]);
        continue;
      }
    }
    send([reply({})]);
  }
});
