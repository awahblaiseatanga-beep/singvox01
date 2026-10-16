// Deterministic synthetic fixture generator for SignVox test fixtures.
// Nothing here is recorded signer data or a trained model: every byte is
// computed, so the output is identical on every machine and in every checkout.
// Produces (in this folder, or argv[2] if given):
//   signvox_synth_rig.glb  - valid GLB: 44 canonical Mixamo-named bones in a real
//                            hierarchy, a skinned triangle mesh, an ASL_GOOD clip
//                            (rotation channels on RightArm/RightForeArm/RightHand)
//                            and an ASL_NEUTRAL clip.
//   synth_79.onnx          - 274 B graph: input [1,60,366] -> logits [1,79]
//   synth_79.onnx.data     - empty sidecar (ORT opens `${modelUrl}.data` unconditionally)
//   synth_3.onnx / .data   - same for 3 classes
// No randomness: byte-for-byte reproducible on every run.
import * as fs from 'node:fs';
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';

// Writes beside this script by default: `node generate_fixtures.mjs [outDir]`
const outDir = process.argv[2] || path.dirname(fileURLToPath(import.meta.url));
fs.mkdirSync(outDir, { recursive: true });

/* ------------------------------- GLB rig -------------------------------- */

// Mixamo canonical bone tree: parent -> [children], with local offsets (metres).
const BONES = [
  ['mixamorig4:Hips', null, [0, 1, 0]],
  ['mixamorig4:Spine', 'mixamorig4:Hips', [0, 0.1, 0]],
  ['mixamorig4:Spine1', 'mixamorig4:Spine', [0, 0.1, 0]],
  ['mixamorig4:Spine2', 'mixamorig4:Spine1', [0, 0.1, 0]],
  ['mixamorig4:Neck', 'mixamorig4:Spine2', [0, 0.1, 0]],
  ['mixamorig4:Head', 'mixamorig4:Neck', [0, 0.1, 0]],
  ['mixamorig4:LeftShoulder', 'mixamorig4:Spine2', [0.05, 0.08, 0]],
  ['mixamorig4:LeftArm', 'mixamorig4:LeftShoulder', [0.17, 0, 0]],
  ['mixamorig4:LeftForeArm', 'mixamorig4:LeftArm', [0.28, 0, 0]],
  ['mixamorig4:LeftHand', 'mixamorig4:LeftForeArm', [0.26, 0, 0]],
  ['mixamorig4:RightShoulder', 'mixamorig4:Spine2', [-0.05, 0.08, 0]],
  ['mixamorig4:RightArm', 'mixamorig4:RightShoulder', [-0.17, 0, 0]],
  ['mixamorig4:RightForeArm', 'mixamorig4:RightArm', [-0.28, 0, 0]],
  ['mixamorig4:RightHand', 'mixamorig4:RightForeArm', [-0.26, 0, 0]],
];
const FINGERS = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky'];
for (const side of ['Left', 'Right']) {
  const s = side === 'Left' ? 1 : -1;
  for (const f of FINGERS) {
    const segs = f === 'Index' ? 4 : 3;
    for (let i = 1; i <= segs; i++) {
      const name = `mixamorig4:${side}Hand${f}${i}`;
      const parent = i === 1 ? `mixamorig4:${side}Hand` : `mixamorig4:${side}Hand${f}${i - 1}`;
      const off = i === 1 ? [s * 0.02, 0, f === 'Thumb' ? 0.03 : 0.01] : [s * 0.03, 0, 0];
      BONES.push([name, parent, off]);
    }
  }
}
// CanonicalBones in avatar/controller/boneMap.ts has exactly 46 entries:
// 6 core + 8 arm + (3 thumb + 4 index + 3 middle + 3 ring + 3 pinky) x 2 hands.
if (BONES.length !== 46) throw new Error(`expected 46 canonical bones, got ${BONES.length}`);

const idx = new Map(BONES.map(([n], i) => [n, i]));
const nodes = BONES.map(([name, parent, off]) => ({ name, translation: off, children: [] }));
BONES.forEach(([name, parent], i) => {
  if (parent) nodes[idx.get(parent)].children.push(i);
});
for (const n of nodes) if (n.children.length === 0) delete n.children;

// Packed binary buffer -----------------------------------------------------
const parts = [];
let len = 0;
const push = (buf, align) => {
  const pad = (align - (len % align)) % align;
  if (pad) { parts.push(Buffer.alloc(pad)); len += pad; }
  const off = len;
  parts.push(buf);
  len += buf.length;
  return off;
};
const f32 = (arr) => { const b = Buffer.alloc(arr.length * 4); arr.forEach((v, i) => b.writeFloatLE(v, i * 4)); return b; };

const posOff = push(f32([-0.1, 1, 0, 0.1, 1, 0, 0, 1.1, 0]), 4);
const jointsOff = push(Buffer.from([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]), 4); // all verts -> joint 0 (Hips)
const weightsOff = push(f32([1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]), 4);
const ibmOff = push(f32(new Array(46 * 16).fill(0).map((_, i) => (i % 5 === 0 ? 1 : 0))), 4); // identity mat4 x46
const timesOff = push(f32([0, 1]), 4);
const idQuat = [0, 0, 0, 1];
const turnedQuat = [0, 0.38268343, 0, 0.92387953]; // 45 deg about Y for key 1
const goodOff = push(f32([...idQuat, ...turnedQuat]), 4); // track 0 (RightArm)
const push2 = (arr) => { const o = len; parts.push(f32(arr)); len += arr.length * 4; return o; };
const goodOff1 = push2([...idQuat, ...turnedQuat]); // track 1 (RightForeArm)
const goodOff2 = push2([...idQuat, ...turnedQuat]); // track 2 (RightHand)
const neutralOff = push2([...idQuat, ...idQuat]);

const bufferBin = Buffer.concat(parts, len);

const gltf = {
  asset: { version: '2.0', generator: 'signvox-synth-fixture-gen' },
  scene: 0,
  scenes: [{ nodes: [0, BONES.length] }], // Hips + Body(mesh) 
  nodes: [...nodes, { name: 'Body', mesh: 0, skin: 0 }],
  skins: [{ inverseBindMatrices: 3, skeleton: 0, joints: BONES.map((_, i) => i) }],
  meshes: [{ primitives: [{ attributes: { POSITION: 0, JOINTS_0: 1, WEIGHTS_0: 2 } }] }],
  accessors: [
    { bufferView: 0, componentType: 5126, count: 3, type: 'VEC3', min: [-0.1, 1, 0], max: [0.1, 1.1, 0.1] },
    { bufferView: 1, componentType: 5121, count: 3, type: 'VEC4' },
    { bufferView: 2, componentType: 5126, count: 3, type: 'VEC4' },
    { bufferView: 3, componentType: 5126, count: 46, type: 'MAT4' },
    { bufferView: 4, componentType: 5126, count: 2, type: 'SCALAR', min: [0], max: [1] },
    { bufferView: 5, componentType: 5126, count: 2, type: 'VEC4' },
    { bufferView: 6, componentType: 5126, count: 2, type: 'VEC4' },
    { bufferView: 7, componentType: 5126, count: 2, type: 'VEC4' },
    { bufferView: 8, componentType: 5126, count: 2, type: 'VEC4' },
  ],
  bufferViews: [
    { buffer: 0, byteOffset: posOff, byteLength: 36, target: 34962 },
    { buffer: 0, byteOffset: jointsOff, byteLength: 12, target: 34962 },
    { buffer: 0, byteOffset: weightsOff, byteLength: 48, target: 34962 },
    { buffer: 0, byteOffset: ibmOff, byteLength: 46 * 64 },
    { buffer: 0, byteOffset: timesOff, byteLength: 8 },
    { buffer: 0, byteOffset: goodOff, byteLength: 32 },
    { buffer: 0, byteOffset: goodOff1, byteLength: 32 },
    { buffer: 0, byteOffset: goodOff2, byteLength: 32 },
    { buffer: 0, byteOffset: neutralOff, byteLength: 32 },
  ],
  buffers: [{ byteLength: len }],
  animations: [
    {
      name: 'ASL_GOOD',
      samplers: [
        { input: 4, output: 5, interpolation: 'LINEAR' },
        { input: 4, output: 6, interpolation: 'LINEAR' },
        { input: 4, output: 7, interpolation: 'LINEAR' },
      ],
      channels: [
        { sampler: 0, target: { node: idx.get('mixamorig4:RightArm'), path: 'rotation' } },
        { sampler: 1, target: { node: idx.get('mixamorig4:RightForeArm'), path: 'rotation' } },
        { sampler: 2, target: { node: idx.get('mixamorig4:RightHand'), path: 'rotation' } },
      ],
    },
    {
      name: 'ASL_NEUTRAL',
      samplers: [{ input: 4, output: 8, interpolation: 'LINEAR' }],
      channels: [{ sampler: 0, target: { node: idx.get('mixamorig4:Head'), path: 'rotation' } }],
    },
  ],
};

const jsonBuf = Buffer.from(JSON.stringify(gltf), 'utf8');
const jsonPad = (4 - (jsonBuf.length % 4)) % 4;
const jsonChunk = Buffer.concat([jsonBuf, Buffer.alloc(jsonPad, 0x20)]);
const binPad = (4 - (bufferBin.length % 4)) % 4;
const binChunk = Buffer.concat([bufferBin, Buffer.alloc(binPad, 0)]);
const header = Buffer.alloc(12);
header.write('glTF', 0, 'ascii');
header.writeUInt32LE(2, 4);
header.writeUInt32LE(12 + 8 + jsonChunk.length + 8 + binChunk.length, 8);
const jc = Buffer.alloc(8); jc.writeUInt32LE(jsonChunk.length, 0); jc.write('JSON', 4, 'ascii');
const bc = Buffer.alloc(8); bc.writeUInt32LE(binChunk.length, 0); bc.write('BIN\0', 4, 'ascii');
const glb = Buffer.concat([header, jc, jsonChunk, bc, binChunk]);
fs.writeFileSync(path.join(outDir, 'signvox_synth_rig.glb'), glb);

/* -------------------------------- ONNX ---------------------------------- */
// Proven encoder (verified against the real onnxruntime-web runtime: a 274-byte
// graph loaded with inference.ts's exact session options and returned [1,79] /
// [1,3] logits from a [1,60,366] input). Graph: Reshape(flat) -> Slice(first N).
const varint = (n) => {
  let v = BigInt(n);
  if (v < 0n) v += 1n << 64n;
  const out = [];
  do {
    let b = Number(v & 0x7fn);
    v >>= 7n;
    if (v > 0n) b |= 0x80;
    out.push(b);
  } while (v > 0n);
  return Buffer.from(out);
};
const tag = (f, w) => varint((f << 3) | w);
const lenDelim = (f, p) => Buffer.concat([tag(f, 2), varint(p.length), p]);
const str = (f, s) => lenDelim(f, Buffer.from(s, 'utf8'));
const vi = (f, n) => Buffer.concat([tag(f, 0), varint(n)]);
const packedInt64 = (f, vs) => lenDelim(f, Buffer.concat(vs.map(varint)));
const FLOAT = 1, INT64 = 7;

const int64Tensor = (name, dims, values) =>
  Buffer.concat([...dims.map((d) => vi(1, d)), vi(2, INT64), str(8, name), packedInt64(7, values)]);
const node = (inputs, outputs, name, opType) =>
  Buffer.concat([...inputs.map((i) => str(1, i)), ...outputs.map((o) => str(2, o)), str(3, name), str(4, opType)]);
const valueInfo = (name, elemType, dims) => {
  const dimsEnc = Buffer.concat(dims.map((d) => lenDelim(1, vi(1, d))));
  return Buffer.concat([str(1, name), lenDelim(2, lenDelim(1, Buffer.concat([vi(1, elemType), lenDelim(2, dimsEnc)])))]);
};

function makeOnnx(classes) {
  const elements = 60 * 366;
  const graph = Buffer.concat([
    lenDelim(1, node(['input', 'flat_shape'], ['flat'], 'flatten', 'Reshape')),
    lenDelim(1, node(['flat', 'starts', 'ends', 'axes'], ['logits'], 'take_first', 'Slice')),
    str(2, 'signvox_synthetic'),
    lenDelim(5, int64Tensor('flat_shape', [2], [1, elements])),
    lenDelim(5, int64Tensor('starts', [1], [0])),
    lenDelim(5, int64Tensor('ends', [1], [classes])),
    lenDelim(5, int64Tensor('axes', [1], [1])),
    lenDelim(11, valueInfo('input', FLOAT, [1, 60, 366])),
    lenDelim(12, valueInfo('logits', FLOAT, [1, classes])),
  ]);
  const opset = vi(2, 13);
  return Buffer.concat([vi(1, 8), str(2, 'signvox-synthetic'), lenDelim(7, graph), lenDelim(8, opset)]);
}
for (const classes of [79, 3]) {
  fs.writeFileSync(path.join(outDir, `synth_${classes}.onnx`), makeOnnx(classes));
  fs.writeFileSync(path.join(outDir, `synth_${classes}.onnx.data`), Buffer.alloc(0));
}

console.log(JSON.stringify(
  Object.fromEntries(fs.readdirSync(outDir).map((f) => [f, fs.statSync(path.join(outDir, f)).size])),
  null, 2,
));
