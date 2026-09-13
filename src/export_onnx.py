import argparse

import torch

from src.dataset import REGIONES_A_IDX
from src.model import build_model_etapa0


def exportar_onnx(model_path, output_path="models/etapa0_region.onnx", opset=17):
    model = build_model_etapa0(num_classes=len(REGIONES_A_IDX))
    model.load_state_dict(torch.load(model_path, map_location="cpu"))
    model.eval()

    dummy_input = torch.randn(1, 3, 512, 512)
    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}},
        opset_version=opset,
    )
    print(f"modelo exportado a {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", default="models/etapa0_region.pt")
    parser.add_argument("--output-path", default="models/etapa0_region.onnx")
    args = parser.parse_args()
    exportar_onnx(args.model_path, args.output_path)
