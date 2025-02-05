import base64
import os
import sys
import time
from typing import Annotated

import aiofiles
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from util.yolo_util import yolo_detect_objects  # YOLOの物体検出関数をインポート

# .envファイルの内容を読み込見込む
load_dotenv()

# YOLOモデルファイル
yolo_model_file = os.environ.get("YOLO_MODEL_FILE")
if yolo_model_file is None:
    print("環境変数YOLO_MODEL_FILEが設定されていません")
    sys.exit()
else:
    print("[MODEL FILE]", yolo_model_file)

app = FastAPI()

# 静的ファイルとテンプレートディレクトリの設定
app.mount("/assets", StaticFiles(directory="test/static"), name="static")
templates = Jinja2Templates(directory="templates")

# ローカルに保存するディレクトリ
UPLOAD_FOLDER = "./uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def upload_page():
    """
    アップロードページを表示
    """
    return templates.TemplateResponse("upload.html", {"request": {}, "title": "YOLO Object Detection"})


@app.post("/detect")
async def detect_objects(request: Request, file: Annotated[UploadFile, File(...)]):
    """
    アップロードされた画像で物体検出を実行

    <form action="/detect" method="post" >
    の中にあるname="file"の値を取得する．

    """
    # アップロードされた画像をローカルに保存
    file_path = os.path.join(UPLOAD_FOLDER, f"{int(time.time())}_{file.filename}")
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(await file.read())

    # YOLOによる物体検出
    annotated_image_path = os.path.join(UPLOAD_FOLDER, f"detected_{file.filename}")
    detection_results = yolo_detect_objects(file_path, annotated_image_path, yolo_model_file)

    if not detection_results["records"]:  # これが検出結果のリスト，詳細はyolo_detect.pyを参照
        return templates.TemplateResponse(
            "detection_result.html", {"request": request, "detected_objects": [], "annotated_image": None}
        )

    # 結果をHTMLまたはJSONで返す
    with open(annotated_image_path, "rb") as img_file:
        encoded_image = base64.b64encode(img_file.read()).decode("utf-8")

    # 検出結果をテンプレートに渡してHTMLを生成
    return templates.TemplateResponse(
        "detection_results.html",
        {
            "request": request,
            "detected_objects": detection_results["records"],
            "annotated_image": f"data:image/jpeg;base64,{encoded_image}",
        },
    )

    # return {"detected_objects": detection_results["records"], "annotated_image": f"data:image/jpeg;base64,{encoded_image}"}
