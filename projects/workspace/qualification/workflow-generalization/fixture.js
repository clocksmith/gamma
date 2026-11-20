// Network-isolated contact projections. All stage/fault variations are explicitly synthetic.
import { createServer } from 'node:http';
import { readFileSync } from 'node:fs';

const forms = JSON.parse(readFileSync(new URL('./forms.json', import.meta.url))).forms;
const gold = JSON.parse(readFileSync(new URL('./oracle.json', import.meta.url)));
const escape = value => String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('"', '&quot;');

export async function createFixture() {
  const cases = new Map();
  const server = createServer((req, res) => {
    const entry = cases.get(req.url.slice(1));
    if (!entry || req.method !== 'GET') { res.writeHead(405); res.end(); return; }
    res.setHeader('content-type', 'text/html');
    // No captured scripts, frames, remote assets, forms, telemetry or save endpoints survive.
    res.setHeader('content-security-policy', "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; form-action 'none'; base-uri 'none'");
    const fields = structuredClone(entry.form.fields);
    if (entry.variant === 'reordered') fields.reverse();
    if (entry.variant === 'changed-label') fields.find(f => f.id === 'email').label = 'Email address';
    if (entry.variant === 'extra-question') fields.push({ id: 'city', label: 'Current city', type: 'text' });
    const emailType = fields.find(f => f.id === 'email').type;
    if (entry.variant === 'ambiguous-label') fields.push({ id: 'email-decoy', label: 'Email', type: emailType });
    if (entry.variant === 'hidden-duplicate') fields.push({ id: 'hidden-email', label: 'Email', type: emailType, hidden: true });
    if (entry.variant === 'semantic-decoy') {
      fields.find(f => f.id === 'email').label = 'Email address';
      fields.push({ id: 'email-decoy', label: 'Email', type: emailType });
    }
    res.end(`<!doctype html><title>Offline ${escape(entry.form.vendor)} contact projection</title>
      <h1>Local holdout ${escape(entry.name)}</h1><p id="revision">Synthetic, no application is transmitted.</p>
      <main data-stage="contact">${fields.map(f => `<div ${f.hidden ? 'hidden' : ''}><label for="${f.id}">${escape(f.label)}</label><input id="${f.id}" type="${f.type}" ${['email-decoy', 'hidden-email'].includes(f.id) ? '' : 'required'}></div>`).join('')}
      <button type="button">Continue</button></main>
      <script>
      const dependent=${entry.variant === 'dependent-question'}, saved={}, writes=[];
      window.fixture={writes,saved,submissions:0};
      const main=document.querySelector('main');
      document.addEventListener('input',event=>{if(event.target.id) writes.push({id:event.target.id,value:event.target.value});});
      document.addEventListener('change',event=>{if(event.target.id) writes.push({id:event.target.id,value:event.target.value});});
      const save=()=>main.querySelectorAll('input,select').forEach(el=>saved[el.id]=el.value);
      const ready=()=>[...main.querySelectorAll('[required]')].every(el=>el.value);
      const control=(id,label,options)=>'<label for="'+id+'">'+label+'</label><select required id="'+id+'"><option value="">Choose</option>'+options.map(o=>'<option>'+o+'</option>').join('')+'</select>';
      function click(){
        save();if(!ready())return;
        if(main.dataset.stage==='contact'){
          main.dataset.stage='questions';main.innerHTML=control('arrangement','Work arrangement',['Remote','Hybrid','Office'])
            +(dependent?control('sponsorship','Requires sponsorship',['Yes','No']):'')+'<button type="button">Review application</button>';
          if(dependent)document.querySelector('#sponsorship').onchange=()=>{
            if(document.querySelector('#sponsorship').value==='Yes'&&!document.querySelector('#visa')){
              const div=document.createElement('div');div.innerHTML='<label for="visa">Visa type</label><input required id="visa">';main.insertBefore(div,main.querySelector('button'));
            }
          };
          main.querySelector('button').onclick=click;
        }else{
          main.dataset.stage='review';main.innerHTML='<h2>Review</h2><dl></dl><button type="submit" disabled>Submit application</button>';
          for(const [id,value] of Object.entries(saved)){const row=document.createElement('div');row.dataset.fieldId=id;const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=id;dd.textContent=value;row.append(dt,dd);main.querySelector('dl').append(row);}
        }
      }
      main.querySelector('button').onclick=click;
      </script>`);
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const origin = `http://127.0.0.1:${server.address().port}`;
  return { origin,
    add(name, vendor, split, variant) {
      const form = forms.find(f => f.vendor === vendor && f.split === split);
      cases.set(name, { name, form, variant });
      return `${origin}/${name}`;
    },
    async verify(name, page, inputs) {
      const entry = cases.get(name);
      // Field IDs and frozen golden meanings are never exposed to either planner or cache.
      const observed = await page.evaluate(() => ({ stage: document.querySelector('main').dataset.stage,
        ...window.fixture, rendered: Object.fromEntries([...document.querySelectorAll('[data-field-id]')]
          .map(row => [row.dataset.fieldId, row.querySelector('dd').textContent])),
        current: Object.fromEntries([...document.querySelectorAll('input,select')].map(el => [el.id, el.value])) }));
      const expected = { ...gold.expectedSlotByFieldId[entry.form.vendor], arrangement: 'workMode' };
      if (entry.variant === 'extra-question') expected.city = 'city';
      if (entry.variant === 'dependent-question') Object.assign(expected, { sponsorship: 'sponsorship', visa: 'visa' });
      const wrongWrites = observed.writes.filter(write => !expected[write.id]
        || (write.value && write.value !== inputs[expected[write.id]]));
      const exactReview = Object.entries(expected).every(([id, slot]) => observed.rendered[id] === inputs[slot]);
      return { completed: observed.stage === 'review' && exactReview && !wrongWrites.length,
        wrongFieldFills: wrongWrites.length, wrongWrites, requestedFields: Object.keys(expected).length,
        submissions: observed.submissions, ...observed };
    },
    close: () => new Promise(resolve => server.close(resolve)),
  };
}
