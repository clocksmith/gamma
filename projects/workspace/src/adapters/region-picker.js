// Human-only selection UI. The selected click is consumed; it never activates the page control.
export function pickRegion(timeoutMs) {
  return new Promise((resolve, reject) => {
    const frame = document.createElement('div');
    Object.assign(frame.style, { position: 'fixed', pointerEvents: 'none', zIndex: '2147483647', border: '2px solid #13856a',
      background: '#13856a18', boxSizing: 'border-box', color: '#fff', font: '13px system-ui' });
    const label = document.createElement('span'); label.textContent = 'Click a region to share · Esc cancels';
    Object.assign(label.style, { position: 'absolute', left: '0', top: '0', background: '#145346', padding: '6px 10px' });
    frame.append(label); document.documentElement.append(frame);
    let timer;
    const finish = (error, value) => {
      clearTimeout(timer); frame.remove();
      document.removeEventListener('mousemove', move, true); document.removeEventListener('click', click, true);
      document.removeEventListener('keydown', key, true);
      if (error) reject(error); else resolve(value);
    };
    const move = event => {
      const rect = event.target.getBoundingClientRect();
      Object.assign(frame.style, { left: `${rect.left}px`, top: `${rect.top}px`, width: `${rect.width}px`, height: `${rect.height}px` });
    };
    const selectorFor = node => {
      if (node.id && document.querySelectorAll(`#${CSS.escape(node.id)}`).length === 1) return `#${CSS.escape(node.id)}`;
      const parts = [];
      for (let current = node; current && current !== document.documentElement; current = current.parentElement) {
        const tag = current.tagName.toLowerCase();
        const siblings = [...current.parentElement.children].filter(value => value.tagName === current.tagName);
        parts.unshift(`${tag}:nth-of-type(${siblings.indexOf(current) + 1})`);
      }
      return `html > ${parts.join(' > ')}`;
    };
    const click = event => {
      event.preventDefault(); event.stopImmediatePropagation();
      finish(null, { selector: selectorFor(event.target), preview: (event.target.innerText ?? '').slice(0, 200) });
    };
    const key = event => { if (event.key === 'Escape') { event.preventDefault(); finish(Error('Selection cancelled')); } };
    document.addEventListener('mousemove', move, true); document.addEventListener('click', click, true); document.addEventListener('keydown', key, true);
    timer = setTimeout(() => finish(Error('Selection expired; try again')), timeoutMs);
  });
}
