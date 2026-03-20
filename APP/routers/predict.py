import time

from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel

from APP.services import inference_service


router = APIRouter()


class PredictRequest(BaseModel):
    ct_path: str


@router.post("/predict")
def predict(file: UploadFile = File(...)):
    upload_path, original_filename = inference_service.save_upload_file(file)

    start = time.time()
    try:
        output_name = inference_service.build_result_filename(original_filename)
        result_path = inference_service.run_predict(upload_path, output_name=output_name)
        elapsed_ms = int((time.time() - start) * 1000)
        return {
            "filename": original_filename,
            "result_path": result_path,
            "elapsed_ms": elapsed_ms,
        }
    finally:
        inference_service.safe_remove(upload_path)


@router.post("/predict_by_path")
def predict_by_path(req: PredictRequest):
    start = time.time()
    result_path = inference_service.run_predict(req.ct_path)
    elapsed_ms = int((time.time() - start) * 1000)
    return {"result_path": result_path, "elapsed_ms": elapsed_ms}

