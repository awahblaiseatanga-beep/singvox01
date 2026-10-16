import * as ort from 'onnxruntime-node';

async function run() {
    const session = await ort.InferenceSession.create('d:/Singvox/Singvox/web/public/spoter_v2_model.onnx');
    console.log('Output names:', session.outputNames);
    
    // Test shape output tensor size
    const dummy = new Float32Array(60 * 366).fill(0.1);
    const tensor = new ort.Tensor('float32', dummy, [1, 60, 366]);
    
    const feeds: any = {};
    feeds[session.inputNames[0]] = tensor;
    
    const res = await session.run(feeds);
    console.log('Logits Array Dims:', res[session.outputNames[0]].dims);
    console.log('Total Output Classes Span:', res[session.outputNames[0]].data.length);
}
run().catch(console.error);
