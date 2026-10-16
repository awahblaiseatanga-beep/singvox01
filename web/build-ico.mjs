import fs from 'fs';
const pngData = fs.readFileSync('../app/android/app/src/main/res/mipmap-mdpi/ic_launcher.png');
const header = Buffer.alloc(22);
header.writeUInt16LE(0, 0); // Reserved
header.writeUInt16LE(1, 2); // Format: ICO
header.writeUInt16LE(1, 4); // Images: 1
header.writeUInt8(48, 6);   // width 48px
header.writeUInt8(48, 7);   // height 48px
header.writeUInt8(0, 8);    // Colors
header.writeUInt8(0, 9);    // Reserved
header.writeUInt16LE(1, 10);  // Planes
header.writeUInt16LE(32, 12); // BPP
header.writeUInt32LE(pngData.length, 14); // Size of PNG byte array
header.writeUInt32LE(22, 18); // Offset
const icoData = Buffer.concat([header, pngData]);
fs.writeFileSync('./public/favicon.ico', icoData);
