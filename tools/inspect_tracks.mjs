import fs from 'fs';

const data = fs.readFileSync('web/public/avatar/SignVox_Female_Competition_Prototype.glb');
const jsonChunkLength = data.readUInt32LE(12);
const jsonText = data.toString('utf8', 20, 20 + jsonChunkLength);
const gltf = JSON.parse(jsonText);

console.log('=== DETAILED GLB ANIMATION ANALYSIS ===');
gltf.animations.forEach((anim, i) => {
  console.log(`\nAnim ${i}: "${anim.name}"`);
  // Inspect input accessors (timestamps) for samplers
  const inputAccessors = anim.samplers.map(s => gltf.accessors[s.input]);
  const minTimes = inputAccessors.map(a => a.min ? a.min[0] : 0);
  const maxTimes = inputAccessors.map(a => a.max ? a.max[0] : 0);
  const minT = Math.min(...minTimes);
  const maxT = Math.max(...maxTimes);
  console.log(`  Duration: ${minT.toFixed(3)}s to ${maxT.toFixed(3)}s (Length: ${(maxT - minT).toFixed(3)}s)`);
});
