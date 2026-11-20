import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { crc32, inflateSync } from 'node:zlib';

const PNG_SIGNATURE = Buffer.from('89504e470d0a1a0a', 'hex');
const sha256 = value => createHash('sha256').update(value).digest('hex');

function extractRenderShaders(html) {
  const sources = [...html.matchAll(/createShaderModule\(\{\s*code:\s*`([^`]*)`/g)].map(match => match[1]);
  const result = {};
  for (const stage of ['vertex', 'fragment']) {
    const matches = sources.filter(source => source.includes(`@${stage}`));
    assert.equal(matches.length, 1, `one unchanged ${stage} shader required`);
    assert.ok(!matches[0].includes('\\') && !matches[0].includes('${'), 'shader literal must require no JavaScript interpretation');
    result[stage] = matches[0];
  }
  return result;
}

function paeth(left, above, upperLeft) {
  const prediction = left + above - upperLeft;
  const distances = [Math.abs(prediction - left), Math.abs(prediction - above), Math.abs(prediction - upperLeft)];
  return distances[0] <= distances[1] && distances[0] <= distances[2] ? left
    : distances[1] <= distances[2] ? above : upperLeft;
}

function decodePng(png) {
  assert.ok(png.subarray(0, 8).equals(PNG_SIGNATURE), 'PNG signature');
  let offset = 8;
  let header;
  let ended = false;
  const compressed = [];
  while (offset < png.length) {
    assert.ok(offset + 12 <= png.length, 'truncated PNG chunk');
    const length = png.readUInt32BE(offset);
    const end = offset + 12 + length;
    assert.ok(end <= png.length, 'truncated PNG data');
    const type = png.toString('ascii', offset + 4, offset + 8);
    assert.equal(crc32(png.subarray(offset + 4, end - 4)), png.readUInt32BE(end - 4), 'PNG CRC');
    const data = png.subarray(offset + 8, end - 4);
    if (type === 'IHDR') {
      assert.ok(!header && length === 13 && offset === 8, 'one initial PNG header');
      header = { width: data.readUInt32BE(0), height: data.readUInt32BE(4), depth: data[8], type: data[9] };
      assert.ok(header.width > 0 && header.height > 0 && header.width * header.height <= 16777216);
      assert.ok(header.depth === 8 && [2, 6].includes(header.type), '8-bit RGB/RGBA PNG required');
      assert.ok(data.subarray(10).every(byte => byte === 0), 'standard noninterlaced PNG required');
    } else if (type === 'IDAT') compressed.push(data);
    else if (type === 'IEND') {
      assert.equal(length, 0);
      assert.equal(end, png.length, 'PNG trailing bytes');
      ended = true;
    } else assert.ok(type[0] === type[0].toLowerCase(), `unsupported critical PNG chunk ${type}`);
    offset = end;
  }
  assert.ok(header && ended && compressed.length, 'complete PNG required');
  const channels = header.type === 6 ? 4 : 3;
  const stride = channels * header.width;
  const bytes = inflateSync(Buffer.concat(compressed), { maxOutputLength: (stride + 1) * header.height });
  assert.equal(bytes.length, (stride + 1) * header.height, 'PNG decoded length');
  const pixels = Buffer.alloc(header.width * header.height * 4);
  let previous = Buffer.alloc(stride);
  for (let y = 0; y < header.height; y++) {
    const filter = bytes[y * (stride + 1)];
    assert.ok(filter <= 4, 'PNG filter');
    const row = Buffer.from(bytes.subarray(y * (stride + 1) + 1, (y + 1) * (stride + 1)));
    for (let x = 0; x < stride; x++) {
      const left = x >= channels ? row[x - channels] : 0;
      const above = previous[x];
      const upperLeft = x >= channels ? previous[x - channels] : 0;
      const prediction = [0, left, above, Math.floor((left + above) / 2), paeth(left, above, upperLeft)][filter];
      row[x] = (row[x] + prediction) & 255;
    }
    for (let x = 0; x < header.width; x++) {
      const target = (y * header.width + x) * 4;
      row.copy(pixels, target, x * channels, x * channels + 3);
      pixels[target + 3] = channels === 4 ? row[x * channels + 3] : 255;
    }
    previous = row;
  }
  return { ...header, pixels };
}

function assertSolidPixels(png, rgba) {
  const image = decodePng(png);
  assert.equal(image.width, 8);
  assert.equal(image.height, 8);
  for (let pixel = 0; pixel < 64; pixel++) {
    assert.deepEqual([...image.pixels.subarray(pixel * 4, pixel * 4 + 4)], rgba, `compositor pixel ${pixel}`);
  }
  return { width: 8, height: 8, pixelCount: 64, expectedRgba: rgba, pngSha256: sha256(png) };
}

function presentationReceipt(png, rgba, submission = null) {
  if (submission !== null) {
    assert.equal(submission.queueCompleted, true, 'queue completion requires an independent receipt');
    assert.ok(Number.isSafeInteger(submission.sequence) && submission.sequence > 0, 'submission sequence');
  }
  return { status: 'image-verified', submissionSequence: submission?.sequence ?? null,
    queueCompleted: submission?.queueCompleted ?? null, ...assertSolidPixels(png, rgba) };
}

export { assertSolidPixels, decodePng, extractRenderShaders, presentationReceipt };
