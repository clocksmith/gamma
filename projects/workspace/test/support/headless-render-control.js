// Capability discovery is distinct from controlled-rendering or screenshot qualification.
export async function inspectBeginFrame(send) {
  try {
    const frame = await send('HeadlessExperimental.beginFrame', {
      screenshot: { format: 'png' },
    });
    return {
      status: 'available',
      hasDamage: frame.hasDamage ?? null,
      screenshot: frame.screenshotData ? Buffer.from(frame.screenshotData, 'base64') : null,
    };
  } catch (error) {
    if (/HeadlessExperimental\.beginFrame.*(?:wasn't found|not found)|'HeadlessExperimental\.beginFrame' wasn't found/.test(error.message)) {
      return { status: 'unsupported', reason: 'protocol-method-not-found', screenshot: null };
    }
    throw error;
  }
}
