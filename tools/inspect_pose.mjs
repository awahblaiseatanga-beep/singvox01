import fs from 'fs';

const data = fs.readFileSync('web/public/avatar/SignVox_Female_Competition_Prototype.glb');
const jsonChunkLength = data.readUInt32LE(12);
const jsonText = data.toString('utf8', 20, 20 + jsonChunkLength);
const gltf = JSON.parse(jsonText);

console.log('=== GLB NODES & BONES SUMMARY ===');
gltf.nodes.forEach((node, i) => {
  if (node.name && (node.name.includes('Arm') || node.name.includes('Hand') || node.name.includes('Shoulder'))) {
    console.log(`Node ${i}: ${node.name}`);
  }
});

console.log('\n=== CHECKING MIXAMO.COM vs ASL_NEUTRAL ===');
gltf.animations.forEach((anim, i) => {
  console.log(`Anim ${i}: name="${anim.name}", tracks=${anim.channels.length}`);
});
