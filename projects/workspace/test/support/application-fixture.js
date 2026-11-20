// Synthetic ATS-style application. The oracle reads rendered review fields, not planner output.
import { createServer } from 'node:http';
import { randomUUID } from 'node:crypto';

export async function applicationFixture() {
  const cases = new Map();
  const server = createServer((req, res) => {
    const parts = req.url.split('/');
    const entry = cases.get(parts[2]);
    if (!entry) { res.writeHead(404); res.end(); return; }
    if (parts[1] === 'submit') { entry.submissions++; res.end('Unexpected submission'); return; }
    if (parts[1] !== 'application') { res.writeHead(404); res.end(); return; }
    const key = randomUUID();
    res.setHeader('content-type', 'text/html');
    res.end(`<!doctype html><html><head><title>Synthetic application</title></head><body>
      <h1>Example Company ${entry.company}: Engineer application</h1>
      <p id="revision">Review the supplied applicant details. This is a test application.</p>
      <main data-stage="contact"></main><script>
      const key = ${JSON.stringify(key)}, changed = ${entry.changed}, applicant = {};
      document.documentElement.dataset.account = ${JSON.stringify(entry.account)};
      const labels = {fullName:'Full name',email:'Email address',location:'Current city',workMode:'Work arrangement',phone:'Phone number'};
      const main = document.querySelector('main');
      const field = (slot, type='text') => '<label for="'+slot+'-'+key+'">'+labels[slot]+'</label><input required id="'+slot+'-'+key+'" data-slot="'+slot+'" type="'+type+'">';
      const save = () => document.querySelectorAll('[data-slot]').forEach(el => applicant[el.dataset.slot] = el.value);
      const valid = slots => slots.every(slot => applicant[slot] && applicant[slot] !== 'Choose');
      function render(stage) {
        main.dataset.stage=stage;
        if(stage==='contact') main.innerHTML = field('fullName')+field('email','email')+'<button type="button">Continue</button>';
        if(stage==='questions') main.innerHTML = field('location')+'<label for="mode-'+key+'">Work arrangement</label><select id="mode-'+key+'" data-slot="workMode"><option>Choose</option><option>Remote</option><option>Hybrid</option><option>Office</option></select>'
          +(changed ? field('phone','tel') : '')+'<button type="button">Review application</button>';
        if(stage==='review') {
          main.innerHTML='<h2>Review application</h2><dl></dl><form method="post" action="/submit/${entry.name}"><button type="submit" disabled>Submit application</button></form>';
          for(const slot of ['fullName','email','location','workMode',...(changed?['phone']:[])]) {
            const div=document.createElement('div'),dt=document.createElement('dt'),dd=document.createElement('dd');
            dt.textContent=labels[slot];dd.textContent=applicant[slot];div.append(dt,dd);main.querySelector('dl').append(div);
          }
          return;
        }
        main.querySelector('button').onclick=()=>{
          save();const required=stage==='contact'?['fullName','email']:['location','workMode',...(changed?['phone']:[])];
          if(!valid(required)) { document.querySelector('#revision').textContent='Complete all required fields before continuing.';return; }
          render(stage==='contact'?'questions':'review');
        };
      }
      render('contact');
      </script></body></html>`);
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const origin = `http://127.0.0.1:${server.address().port}`;
  return {
    origin,
    add(name, changed = false, company = name, account = 'fixture-account') { cases.set(name, { name, company, changed, account, submissions: 0 }); return `${origin}/application/${name}`; },
    async verify(name, page, inputs) {
      const entry = cases.get(name);
      const expected = { 'Full name': inputs.fullName, 'Email address': inputs.email,
        'Current city': inputs.location, 'Work arrangement': inputs.workMode,
        ...(entry.changed ? { 'Phone number': inputs.phone } : {}) };
      const rendered = await page.evaluate(() => ({ stage: document.querySelector('main')?.dataset.stage,
        fields: Object.fromEntries([...document.querySelectorAll('dl > div')].map(row =>
          [row.querySelector('dt').textContent, row.querySelector('dd').textContent])) }));
      const correct = Object.keys(expected).length === Object.keys(rendered.fields).length
        && Object.entries(expected).every(([key, value]) => rendered.fields[key] === value);
      return { completed: rendered.stage === 'review' && correct && entry.submissions === 0,
        rendered, expected, submissions: entry.submissions };
    },
    close: () => new Promise(resolve => server.close(resolve)),
  };
}
