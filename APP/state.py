import os
from concurrent.futures import ThreadPoolExecutor

import torch
from fastapi.security import HTTPBasic


MODEL_PATH = os.getenv("MODEL_PATH", "./Model/model/best_model.pth")
RESULT_DIR = os.getenv("RESULT_DIR", "./Docs/result")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./Docs/uploads")
DB_PATH = os.getenv("DB_PATH", "./Docs/jobs.db")
DB_URL = os.getenv("DB_URL", "").strip()

N_LABEL = 3
DROP_RATE = 0.3
UPPER = 300
LOWER = -100
XY_DOWN_SCALE = 0.5
Z_DOWN_SCALE = 1.0
TC_SIZE = 80
TC_STRIDE = 20

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = None
executor = ThreadPoolExecutor(max_workers=1)
security = HTTPBasic()
