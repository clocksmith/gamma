// Fawn workspace differentiation — the shared agent policy.
//
// One deterministic decision procedure stands in for an agent on both sides. Each side supplies
// tools with the same shape (navigate, view, act, resolveInterruptedOrder, checkpoint); only how
// those tools reach the browser differs. The policy decides from what it observed, waits its
// think time, then acts, as an agent does.

const MAX_DECISIONS = 4;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const isValid = (item, budget) => item.stock > 0 && item.price <= budget;

function cheapestValid(items, budget) {
  return items.filter((item) => isValid(item, budget))
    .sort((a, b) => a.price - b.price || (a.name < b.name ? -1 : 1))[0] ?? null;
}

const urls = (task) => ({
  catalog: (page) => `${task.origin}/catalog?page=${page}`,
  cart: `${task.origin}/cart`,
  checkout: `${task.origin}/checkout`,
  order: (orderId) => `${task.origin}/orders/${orderId}`,
});

async function survey(agent, task) {
  const items = [];
  for (let page = 1; page <= task.pageCount; page += 1) {
    await agent.navigate(urls(task).catalog(page));
    items.push(...(await agent.view('catalog')).items.map((item) => ({ ...item, page })));
  }
  return items;
}

/** Put exactly one unit of the cheapest valid item in the cart, re-deciding when refused. */
async function fillCart(agent, task, hooks) {
  for (let decision = 1; decision <= MAX_DECISIONS; decision += 1) {
    const choice = cheapestValid(await survey(agent, task), task.budget);
    if (!choice) throw new Error('no item satisfies the task');
    await agent.navigate(urls(task).catalog(choice.page));
    const current = (await agent.view('catalog')).items.find((item) => item.name === choice.name);
    if (!current || !isValid(current, task.budget)) continue;
    await hooks.decision('add', { item: current, decision });
    await sleep(agent.thinkTimeMs);
    try {
      await agent.act('add', current, { decision });
    } catch (error) {
      if (error.redecide) continue;
      throw error;
    }
    await agent.navigate(urls(task).cart);
    const cart = await agent.view('cart');
    const keep = cart.lines.find((line) => line.name === current.name && line.price <= task.budget);
    for (const line of cart.lines.filter((candidate) => candidate !== keep)) await agent.act('remove', line);
    if (keep) return;
  }
  throw new Error('the cart could not be filled within the decision bound');
}

/** Fill the checkout form and place the order once; a human-entered address is kept. */
async function placeOrder(agent, task, hooks) {
  await agent.navigate(urls(task).checkout);
  let form = await agent.view('checkout');
  for (let attempt = 1; attempt <= MAX_DECISIONS; attempt += 1) {
    const address = form.address.value || task.address;
    if (attempt === 1) await hooks.decision('fill-address', { address });
    await sleep(agent.thinkTimeMs);
    try {
      if (form.address.value !== address) await agent.act('fill', form.address, { value: address });
      if (form.reference && form.reference.value !== task.reference) {
        await agent.act('fill', form.reference, { value: task.reference });
      }
      form = await agent.view('checkout');
      agent.checkpoint.update({ order: 'calling', address, reference: form.reference ? task.reference : null });
      const placed = await agent.act('place', form.place, { reference: form.reference ? task.reference : null });
      agent.checkpoint.update({ order: 'done', orderId: placed.orderId });
      return placed.orderId;
    } catch (error) {
      if (!error.redecide) throw error;
      agent.checkpoint.update({ order: null });
      form = await agent.view('checkout');
    }
  }
  throw new Error('the order could not be placed within the decision bound');
}

async function downloadInvoice(agent, task, orderId) {
  await agent.navigate(urls(task).order(orderId));
  const confirmation = await agent.view('confirmation');
  if (!confirmation.invoice) throw new Error(`order ${orderId} shows no invoice link`);
  return agent.act('download', confirmation.invoice);
}

/**
 * Run the task, resuming from the checkpoint after an interruption.
 * @returns {Promise<{status: string, orderId?: number, invoiceSha256?: string, reason?: string}>}
 */
async function runProcurement(agent, task, hooks) {
  const progress = agent.checkpoint.get();
  let orderId = progress.orderId ?? null;
  if (!orderId && progress.order === 'calling') {
    const resolved = await agent.resolveInterrupted(task, progress);
    if (resolved.humanReview) return { status: 'human-review', reason: resolved.reason };
    if (resolved.id) {
      orderId = resolved.id;
      agent.checkpoint.update({ order: 'done', orderId });
    } else {
      agent.checkpoint.update({ order: null });
    }
  }
  if (!orderId) {
    if (!agent.checkpoint.get().cartFilled) {
      await fillCart(agent, task, hooks);
      agent.checkpoint.update({ cartFilled: true });
    }
    orderId = await placeOrder(agent, task, hooks);
  }
  const invoice = await downloadInvoice(agent, task, orderId);
  return { status: 'completed', orderId, invoiceSha256: invoice.sha256 };
}

export { cheapestValid, runProcurement };
