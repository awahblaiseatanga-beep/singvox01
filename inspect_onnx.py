import onnx

def inspect_external_data():
    model_path = r"d:\Singvox\Singvox\ai\sign-recognition\checkpoints\spoter_v2_model.onnx"
    try:
        model = onnx.load(model_path, load_external_data=False)
        for initializer in model.graph.initializer:
            if initializer.data_location == onnx.TensorProto.EXTERNAL:
                for entry in initializer.external_data:
                    if entry.key == 'location':
                        print("EXTERNAL_PATH:" + entry.value)
                        return
        print("NO_EXTERNAL_DATA")
    except Exception as e:
        print("ERROR:", str(e))

if __name__ == '__main__':
    inspect_external_data()
