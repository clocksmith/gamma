import { sha256Hex } from '../../src/utils/sha256.js';

const DEFAULT_BROWSER_ARGS = Object.freeze([
  '--enable-unsafe-webgpu',
  '--enable-dawn-features=allow_unsafe_apis',
  '--enable-features=Vulkan,DefaultANGLEVulkan,VulkanFromANGLE',
  '--use-angle=vulkan',
  '--disable-vulkan-surface',
]);

function normalizeMessages(messages) {
  return messages.map((message) => ({
    type: message.type,
    message: message.message,
    lineNum: message.lineNum,
    linePos: message.linePos,
    offset: message.offset,
    length: message.length,
  }));
}

function requirePositiveInteger(value, fallback, label) {
  const parsed = value == null ? fallback : Number(value);
  if (!Number.isInteger(parsed) || parsed < 1) {
    throw new Error(`${label} must be an integer >= 1.`);
  }
  return parsed;
}

export async function settleWithTimeout(operation, timeoutMs) {
  let timeoutId;
  const operationResult = Promise.resolve()
    .then(operation)
    .then(
      (value) => ({ status: 'fulfilled', value }),
      (error) => ({ status: 'rejected', error })
    );
  const timeoutResult = new Promise((resolve) => {
    timeoutId = setTimeout(() => resolve({ status: 'timed_out' }), timeoutMs);
  });
  const result = await Promise.race([operationResult, timeoutResult]);
  clearTimeout(timeoutId);
  return result;
}

export async function createWgslBrowserVerifier(options = {}) {
  const { chromium } = await import('playwright');
  const browserArgs = Array.isArray(options.browserArgs)
    ? options.browserArgs.map(String)
    : [...DEFAULT_BROWSER_ARGS];
  const compilationTimeoutMs = requirePositiveInteger(
    options.compilationTimeoutMs,
    10000,
    'compilationTimeoutMs'
  );
  const progressEvery = requirePositiveInteger(options.progressEvery, 100, 'progressEvery');
  const dispatchTimeoutMs = requirePositiveInteger(
    options.dispatchTimeoutMs,
    20000,
    'dispatchTimeoutMs'
  );
  const deviceRequest = {
    powerPreference: options.powerPreference || 'high-performance',
    requiredFeatures: Array.isArray(options.requiredFeatures)
      ? options.requiredFeatures.map(String)
      : ['shader-f16', 'subgroups'],
  };
  const requiredVendor = String(options.requiredVendor || '').trim().toLowerCase();

  let browser = null;
  let page = null;
  async function openSession() {
    browser = await chromium.launch({
      headless: options.headless !== false,
      args: browserArgs,
    });
    page = await browser.newPage();
    await page.route('https://wgsl-verifier.invalid/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'text/html',
        body: '<!doctype html><meta charset="utf-8"><title>WGSL verifier</title>',
      });
    });
    await page.goto('https://wgsl-verifier.invalid/');
    const info = await page.evaluate(async (request) => {
      if (!navigator.gpu) {
        throw new Error('webgpu_unavailable');
      }
      const adapter = await navigator.gpu.requestAdapter({
        powerPreference: request.powerPreference,
      });
      if (!adapter) {
        throw new Error('webgpu_adapter_unavailable');
      }
      const availableFeatures = [...adapter.features].sort();
      const missingFeatures = request.requiredFeatures.filter((feature) => (
        !adapter.features.has(feature)
      ));
      if (missingFeatures.length > 0) {
        throw new Error(`webgpu_required_features_missing:${missingFeatures.join(',')}`);
      }
      const device = await adapter.requestDevice({
        requiredFeatures: request.requiredFeatures,
      });
      globalThis.__wgslVerifierDevice = device;
      const adapterInfo = adapter.info || {};
      return {
        vendor: adapterInfo.vendor || null,
        architecture: adapterInfo.architecture || null,
        device: adapterInfo.device || null,
        description: adapterInfo.description || null,
        availableFeatures,
        requiredFeatures: request.requiredFeatures,
      };
    }, deviceRequest);
    if (requiredVendor && String(info.vendor || '').toLowerCase() !== requiredVendor) {
      await browser.close();
      browser = null;
      page = null;
      throw new Error(
        `webgpu_adapter_vendor_mismatch: expected ${requiredVendor}, got ${info.vendor || 'unknown'}`
      );
    }
    return info;
  }

  const deviceInfo = await openSession();
  async function resetSession() {
    if (browser) await browser.close().catch(() => {});
    browser = null;
    page = null;
    const replacementInfo = await openSession();
    if (JSON.stringify(replacementInfo) !== JSON.stringify(deviceInfo)) {
      throw new Error('webgpu_verifier_device_changed_after_reset');
    }
  }

  return {
    deviceInfo,
    browserArgs,
    compilationTimeoutMs,
    async compile(entries) {
      const normalizedEntries = entries.map((entry, index) => ({
        id: String(entry.id || `shader-${index + 1}`),
        code: String(entry.code || ''),
      }));
      const compiled = [];
      for (const [index, shader] of normalizedEntries.entries()) {
        const outcome = await settleWithTimeout(
          () => page.evaluate(async (input) => {
            const device = globalThis.__wgslVerifierDevice;
            if (!device) throw new Error('webgpu_verifier_device_missing');
            const module = device.createShaderModule({
              code: input.code,
              label: input.id,
            });
            const info = await module.getCompilationInfo();
            return {
              id: input.id,
              messages: [...info.messages].map((message) => ({
                type: message.type,
                message: message.message,
                lineNum: message.lineNum,
                linePos: message.linePos,
                offset: message.offset,
                length: message.length,
              })),
            };
          }, shader),
          compilationTimeoutMs
        );
        if (outcome.status === 'fulfilled') {
          compiled.push(outcome.value);
        } else {
          const reason = outcome.status === 'timed_out'
            ? `WGSL compilation timed out after ${compilationTimeoutMs}ms.`
            : `WGSL verifier exception: ${outcome.error?.message || String(outcome.error)}`;
          compiled.push({
            id: shader.id,
            messages: [{
              type: 'error',
              message: reason,
              lineNum: 0,
              linePos: 0,
              offset: 0,
              length: 0,
            }],
          });
          await resetSession();
        }
        if ((index + 1) % progressEvery === 0 || index + 1 === normalizedEntries.length) {
          console.error(`[wgsl-verifier] compiled ${index + 1}/${normalizedEntries.length}`);
        }
      }
      return compiled.map((result, index) => {
        const messages = normalizeMessages(result.messages);
        const errors = messages.filter((message) => message.type === 'error');
        return {
          id: result.id,
          sourceSha256: sha256Hex(normalizedEntries[index].code),
          passed: errors.length === 0,
          messages,
          errorCount: errors.length,
        };
      });
    },
    async dispatch(entries) {
      const normalizedEntries = entries.map((entry, index) => ({
        id: String(entry.id || `dispatch-${index + 1}`),
        code: String(entry.code || ''),
        entryPoint: String(entry.entryPoint || 'main'),
        constants: entry.constants || {},
        dispatch: Array.isArray(entry.dispatch) ? entry.dispatch.map(Number) : [1, 1, 1],
        buffers: Array.isArray(entry.buffers) ? entry.buffers.map((buffer) => ({
          binding: Number(buffer.binding),
          kind: String(buffer.kind || ''),
          bytes: Array.from(buffer.bytes || [], Number),
          readback: buffer.readback === true,
        })) : [],
      }));
      const dispatched = [];
      for (const [index, input] of normalizedEntries.entries()) {
        const outcome = await settleWithTimeout(
          () => page.evaluate(async (request) => {
            const device = globalThis.__wgslVerifierDevice;
            if (!device) throw new Error('webgpu_verifier_device_missing');
            const compilationMessages = [];
            const runtimeErrors = [];
            const readbacks = {};
            const gpuBuffers = [];
            const stagingBuffers = [];
            const uncaptured = (event) => {
              runtimeErrors.push(event.error?.message || String(event.error || event));
            };
            device.addEventListener('uncapturederror', uncaptured);
            device.pushErrorScope('out-of-memory');
            device.pushErrorScope('validation');
            try {
              const module = device.createShaderModule({ code: request.code, label: request.id });
              const compilationInfo = await module.getCompilationInfo();
              compilationMessages.push(...[...compilationInfo.messages].map((message) => ({
                type: message.type,
                message: message.message,
                lineNum: message.lineNum,
                linePos: message.linePos,
                offset: message.offset,
                length: message.length,
              })));
              if (compilationMessages.some((message) => message.type === 'error')) {
                return { compilationMessages, runtimeErrors, readbacks };
              }
              const pipeline = await device.createComputePipelineAsync({
                label: request.id,
                layout: 'auto',
                compute: {
                  module,
                  entryPoint: request.entryPoint,
                  constants: request.constants,
                },
              });
              const bindGroupEntries = request.buffers.map((buffer) => {
                if (!Number.isInteger(buffer.binding) || buffer.binding < 0) {
                  throw new Error(`invalid_binding:${buffer.binding}`);
                }
                if (buffer.bytes.length === 0 || buffer.bytes.length % 4 !== 0) {
                  throw new Error(`invalid_buffer_byte_length:${buffer.binding}`);
                }
                let usage = GPUBufferUsage.COPY_DST;
                if (buffer.kind === 'uniform') usage |= GPUBufferUsage.UNIFORM;
                else if (buffer.kind === 'storage' || buffer.kind === 'read-only-storage') {
                  usage |= GPUBufferUsage.STORAGE;
                } else {
                  throw new Error(`unsupported_buffer_kind:${buffer.kind}`);
                }
                if (buffer.readback) usage |= GPUBufferUsage.COPY_SRC;
                const gpuBuffer = device.createBuffer({
                  label: `${request.id}-binding-${buffer.binding}`,
                  size: buffer.bytes.length,
                  usage,
                });
                gpuBuffers.push({ binding: buffer.binding, buffer: gpuBuffer, size: buffer.bytes.length });
                device.queue.writeBuffer(gpuBuffer, 0, new Uint8Array(buffer.bytes));
                return { binding: buffer.binding, resource: { buffer: gpuBuffer } };
              });
              const bindGroup = device.createBindGroup({
                label: `${request.id}-bind-group`,
                layout: pipeline.getBindGroupLayout(0),
                entries: bindGroupEntries,
              });
              const encoder = device.createCommandEncoder({ label: `${request.id}-encoder` });
              const pass = encoder.beginComputePass({ label: `${request.id}-compute` });
              pass.setPipeline(pipeline);
              pass.setBindGroup(0, bindGroup);
              pass.dispatchWorkgroups(...request.dispatch);
              pass.end();
              for (const descriptor of request.buffers.filter((buffer) => buffer.readback)) {
                const source = gpuBuffers.find((entry) => entry.binding === descriptor.binding);
                const staging = device.createBuffer({
                  label: `${request.id}-readback-${descriptor.binding}`,
                  size: descriptor.bytes.length,
                  usage: GPUBufferUsage.COPY_DST | GPUBufferUsage.MAP_READ,
                });
                stagingBuffers.push({
                  binding: descriptor.binding,
                  buffer: staging,
                  size: descriptor.bytes.length,
                });
                encoder.copyBufferToBuffer(source.buffer, 0, staging, 0, descriptor.bytes.length);
              }
              device.queue.submit([encoder.finish()]);
              await device.queue.onSubmittedWorkDone();
              for (const staging of stagingBuffers) {
                await staging.buffer.mapAsync(GPUMapMode.READ);
                readbacks[String(staging.binding)] = {
                  bytes: [...new Uint8Array(staging.buffer.getMappedRange()).slice()],
                };
                staging.buffer.unmap();
              }
            } catch (error) {
              runtimeErrors.push(error?.message || String(error));
            } finally {
              const validationError = await device.popErrorScope();
              const outOfMemoryError = await device.popErrorScope();
              if (validationError) runtimeErrors.push(validationError.message);
              if (outOfMemoryError) runtimeErrors.push(outOfMemoryError.message);
              device.removeEventListener('uncapturederror', uncaptured);
              for (const entry of gpuBuffers) entry.buffer.destroy();
              for (const entry of stagingBuffers) entry.buffer.destroy();
            }
            return { compilationMessages, runtimeErrors, readbacks };
          }, input),
          dispatchTimeoutMs
        );
        if (outcome.status === 'fulfilled') {
          const messages = normalizeMessages(outcome.value.compilationMessages);
          const compilationErrors = messages.filter((message) => message.type === 'error');
          const runtimeErrors = outcome.value.runtimeErrors.map(String);
          dispatched.push({
            id: input.id,
            sourceSha256: sha256Hex(input.code),
            passed: compilationErrors.length === 0 && runtimeErrors.length === 0,
            compilation: {
              passed: compilationErrors.length === 0,
              messages,
              errorCount: compilationErrors.length,
            },
            validationErrorsAbsent: runtimeErrors.length === 0,
            runtimeErrors,
            readbacks: outcome.value.readbacks,
          });
        } else {
          const reason = outcome.status === 'timed_out'
            ? `WGSL dispatch timed out after ${dispatchTimeoutMs}ms.`
            : `WGSL dispatch exception: ${outcome.error?.message || String(outcome.error)}`;
          dispatched.push({
            id: input.id,
            sourceSha256: sha256Hex(input.code),
            passed: false,
            compilation: { passed: false, messages: [], errorCount: 0 },
            validationErrorsAbsent: false,
            runtimeErrors: [reason],
            readbacks: {},
          });
          await resetSession();
        }
        if ((index + 1) % progressEvery === 0 || index + 1 === normalizedEntries.length) {
          console.error(`[wgsl-verifier] dispatched ${index + 1}/${normalizedEntries.length}`);
        }
      }
      return dispatched;
    },
    async close() {
      if (browser) await browser.close();
      browser = null;
      page = null;
    },
  };
}

export async function verifyWgslCompilation(entries, options = {}) {
  const verifier = await createWgslBrowserVerifier(options);
  try {
    return {
      deviceInfo: verifier.deviceInfo,
      browserArgs: verifier.browserArgs,
      results: await verifier.compile(entries),
    };
  } finally {
    await verifier.close();
  }
}
