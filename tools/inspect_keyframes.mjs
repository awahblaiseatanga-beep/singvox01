import fs from 'fs';

const data = fs.readFileSync('web/public/avatar/SignVox_Female_Competition_Prototype.glb');
const jsonChunkLength = data.readUInt32LE(12);
const jsonText = data.toString('utf8', 20, 20 + jsonChunkLength);
const gltf = JSON.parse(jsonText);

// Build accessor reader helper
function getAccessorData(accessorIndex) {
  const acc = gltf.accessors[accessorIndex];
  const bufferView = gltf.bufferViews[acc.bufferView];
  const binOffset = 20 + jsonChunkLength + 8 + (bufferView.byteOffset || 0) + (acc.byteOffset || 0);
  
  let numComponents = 1;
  if (acc.type === 'VEC3') numComponents = 3;
  if (acc.type === 'VEC4') numComponents = 4;
  if (acc.type === 'MAT4') numComponents = 16;

  const count = acc.count;
  const result = [];
  for (let i = 0; i < count * numComponents; i++) {
    result.push(data.readFloatLE(binOffset + i * 4));
  }
  return { count, numComponents, result };
}

gltf.animations.forEach((anim) => {
  console.log(`\n========================================`);
  console.log(`CLIP: "${anim.name}"`);
  console.log(`========================================`);
  
  anim.channels.forEach(ch => {
    const targetNode = gltf.nodes[ch.target.node];
    const nodeName = targetNode ? targetNode.name : `Node_${ch.target.node}`;
    const targetPath = ch.target.path;
    
    if (nodeName.includes('LeftArm') || nodeName.includes('RightArm') || nodeName.includes('LeftHand') || nodeName.includes('RightHand')) {
      const sampler = anim.samplers[ch.sampler];
      const timeData = getAccessorData(sampler.input).result;
      const valData = getAccessorData(sampler.output).result;
      const lastIdx = timeData.length - 1;
      const numComp = valData.length / timeData.length;
      const lastVal = valData.slice(lastIdx * numComp, (lastIdx + 1) * numComp);
      console.log(`  Bone: ${nodeName.padEnd(30)} | Path: ${targetPath.padEnd(8)} | LastTime: ${timeData[lastIdx].toFixed(3)}s | LastVal: [${lastVal.map(v=>v.toFixed(3)).join(', ')}]`);
    }
  });
});
