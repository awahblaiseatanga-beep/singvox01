const http = require('http');

http.get('http://localhost:5173/onnxruntime/ort-wasm-simd-threaded.wasm', (res) => {
  console.log('HTTP Status:', res.statusCode);
  console.log('Content-Type:', res.headers['content-type']);
  res.once('data', (chunk) => {
    const magic = chunk.slice(0, 4).toString('hex');
    console.log('Magic Bytes:', magic.match(/.{1,2}/g).join(' '));
    process.exit(0);
  });
}).on('error', (e) => {
  console.error(e);
  process.exit(1);
});
