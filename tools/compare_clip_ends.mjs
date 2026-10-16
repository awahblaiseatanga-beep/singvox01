import fs from 'fs';

const data = fs.readFileSync('web/public/avatar/SignVox_Female_Competition_Prototype.glb');
const jsonChunkLength = data.readUInt32LE(12);
const jsonText = data.toString('utf8', 20, 20 + jsonChunkLength);
const gltf = JSON.parse(jsonText);

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

const keyBones = ['RightArm', 'RightForeArm', 'RightHand', 'LeftArm', 'LeftForeArm', 'LeftHand'];

gltf.animations.forEach((anim) => {
  console.log(`\n========================================`);
  console.log(`CLIP: "${anim.name}"`);
  console.log(`========================================`);

  keyBones.forEach(bName => {
    anim.channels.forEach(ch => {
      const targetNode = gltf.nodes[ch.target.node];
      if (targetNode && targetNode.name.endsWith(bName) && ch.target.path === 'rotation') {
        const sampler = anim.samplers[ch.sampler];
        const timeData = getAccessorData(sampler.input).result;
        const valData = getAccessorData(sampler.output).result;
        
        const firstVal = valData.slice(0, 4);
        const lastIdx = timeData.length - 1;
        const lastVal = valData.slice(lastIdx * 4, (lastIdx + 1) * 4);
        
        console.log(`Bone: ${bName.padEnd(15)} | Start (0.0s): [${firstVal.map(v=>v.toFixed(3)).join(', ')}] | End (${timeData[lastIdx].toFixed(2)}s): [${lastVal.map(v=>v.toFixed(3)).join(', ')}]`);
      }
    });
  });
});
