const fs = require('fs');

const inFile = 'public/avatar/SignVox_Female_v2.glb';
const outFile = 'public/avatar/SignVox_Female_v3.glb';

const buf = fs.readFileSync(inFile);

// parse GLB header
const magic = buf.readUInt32LE(0);
const version = buf.readUInt32LE(4);
const length = buf.readUInt32LE(8);

const jsonChunkLength = buf.readUInt32LE(12);
const jsonChunkType = buf.readUInt32LE(16);

// read JSON
let jsonStr = buf.subarray(20, 20 + jsonChunkLength).toString('utf-8');
// remove trailing spaces padding
jsonStr = jsonStr.replace(/\0/g, '').trim();

const gltf = JSON.parse(jsonStr);

// Junk names
const junk = ["Icosphere", "Cube", "Chest_Target_+Y", "Chest_Target_-Y", "LeftHip_Target", "RightHip_Target", "RightHand_Target", "MP_Trace_Left_Shoulder", "MP_Trace_Right_Shoulder", "MP_Trace_Left_Elbow", "MP_Trace_Right_Elbow", "MP_Trace_Left_Wrist", "MP_Trace_Right_Wrist"];

// Search through nodes and hide them completely from the graph
if (gltf.nodes) {
    let removedCounts = 0;
    gltf.nodes.forEach((node, i) => {
        if (node.name && junk.some(j => node.name.includes(j))) {
            // Unlink it structurally by just clearing the mesh index and children
            delete node.mesh;
            delete node.children;
            delete node.skin;
            node.name = "REMOVED_JUNK_" + i;
            removedCounts++;
        }
    });
    console.log("Purged " + removedCounts + " geometry nodes explicitly");
}

let newJsonStr = JSON.stringify(gltf);

// Padding for 4-byte alignment
while (newJsonStr.length % 4 !== 0) {
    newJsonStr += ' ';
}

const newJsonBuffer = Buffer.from(newJsonStr, 'utf-8');
const newJsonChunkLength = newJsonBuffer.length;

// calculate new total length
const diff = newJsonChunkLength - jsonChunkLength;
const newLength = length + diff;

const newBuf = Buffer.alloc(newLength);

// write header
newBuf.writeUInt32LE(magic, 0);
newBuf.writeUInt32LE(version, 4);
newBuf.writeUInt32LE(newLength, 8);

// write JSON chunk header
newBuf.writeUInt32LE(newJsonChunkLength, 12);
newBuf.writeUInt32LE(jsonChunkType, 16);

// write JSON body
newJsonBuffer.copy(newBuf, 20);

// copy BIN chunk
const binChunkOffset = 20 + jsonChunkLength;
const newBinChunkOffset = 20 + newJsonChunkLength;
buf.copy(newBuf, newBinChunkOffset, binChunkOffset);

fs.writeFileSync(outFile, newBuf);
console.log("Saved safely to " + outFile);
