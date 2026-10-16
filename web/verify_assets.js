import http from 'http';

function checkUrl(url) {
  return new Promise((resolve) => {
    http.get(url, (res) => {
      console.log(`URL: ${url}`);
      console.log(`HTTP Status: ${res.statusCode}`);
      console.log(`Content-Type: ${res.headers['content-type']}`);
      res.destroy();
      resolve();
    }).on('error', (e) => {
      console.error(e);
      resolve();
    });
  });
}

async function main() {
  await checkUrl('http://localhost:5174/onnxruntime/ort-wasm-simd-threaded.jsep.mjs');
  await checkUrl('http://localhost:5174/onnxruntime/ort-wasm-simd-threaded.jsep.wasm');
}

main();
