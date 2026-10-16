import fs from 'fs';

const data = fs.readFileSync('web/public/avatar/SignVox_Female_Competition_Prototype.glb');
const jsonChunkLength = data.readUInt32LE(12);
const jsonChunkType = data.readUInt32LE(16);

if (jsonChunkType === 0x4E4F534A) { // 'JSON'
  const jsonText = data.toString('utf8', 20, 20 + jsonChunkLength);
  const gltf = JSON.parse(jsonText);
  console.log('=== GLB ANIMATIONS INSIDE SignVox_Female_Competition_Prototype.glb ===');
  if (gltf.animations) {
    gltf.animations.forEach((anim, i) => {
      console.log(`\nAnim ${i}: "${anim.name}"`);
      console.log(`  Channels: ${anim.channels ? anim.channels.length : 0}`);
      console.log(`  Samplers: ${anim.samplers ? anim.samplers.length : 0}`);
    });
  } else {
    console.log('No animations property found in JSON header.');
  }
} else {
  console.error('Invalid GLB JSON chunk header');
}
