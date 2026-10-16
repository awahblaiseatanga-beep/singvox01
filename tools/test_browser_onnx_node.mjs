import ort from 'onnxruntime-node';

async function testPilotModel() {
  console.log('Loading web/public/spoter_pilot.onnx with ONNX Runtime Node...');
  const session = await ort.InferenceSession.create('web/public/spoter_pilot.onnx');
  
  const dummy = new Float32Array(60 * 366).fill(0.1);
  const tensor = new ort.Tensor('float32', dummy, [1, 60, 366]);
  
  const feeds = { input: tensor };
  const results = await session.run(feeds);
  const logits = results.output.data;
  
  console.log('Logits array:', Array.from(logits));
  console.log('Logits shape:', results.output.dims);
  
  let nanCount = 0;
  let infCount = 0;
  for (const val of logits) {
    if (Number.isNaN(val)) nanCount++;
    if (!Number.isFinite(val)) infCount++;
  }
  
  console.log(`NaN count: ${nanCount}, Inf count: ${infCount}`);
  if (logits.length === 3 && nanCount === 0 && infCount === 0) {
    console.log('SUCCESS: 3-Class Pilot ONNX model executes correctly and produces valid 3-class logits!');
  } else {
    console.error('FAILURE: Unexpected ONNX output');
    process.exit(1);
  }
}

testPilotModel().catch(err => {
  console.error('Error during node ONNX test:', err);
  process.exit(1);
});
