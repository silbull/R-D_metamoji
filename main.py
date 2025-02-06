import base64
import os
import subprocess
import sys
import time

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import api.routers.routers as routers
from util.redis_util import redis_box_get, redis_image_get, redis_image_put, redis_text_get, redis_text_put
from util.text_table_util import run_ocr
from util.util import getNoteId
from util.yolo_util import yolo_detect_objects


def start_redis_with_docker():
    # Docker コマンドで Redis コンテナを起動
    command = ["docker", "run", "--rm", "-d", "--name", "redis-server", "-p", "6379:6379", "redis:latest"]
    subprocess.run(command, check=False)
    print("Redis server started with Docker")


# .envファイルの内容を読み込見込む
load_dotenv()

# ローカルフォルダー
local_folder = os.environ.get("LOCAL_FOLDER")
if local_folder is None:
    print("環境変数LOCAL_FOLDERが設定されていません")
    sys.exit()

# YOLOモデルファイル
yolo_model_file = os.environ.get("YOLO_MODEL_FILE")
if yolo_model_file is None:
    print("環境変数YOLO_MODEL_FILEが設定されていません")
    sys.exit()
else:
    print("[MODEL FILE]", yolo_model_file)

app = FastAPI()
app.include_router(routers.text_router)
app.include_router(routers.object_detection_router)
app.mount(path="/static", app=StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
start_redis_with_docker()


@app.get("/", response_class=HTMLResponse)
async def top_page(request: Request):
    """トップページを開く

    Args:
        request (Request): リクエスト

    Returns:
        _type_: テンプレートレスポンスを返す
    """

    return templates.TemplateResponse("top.html", {"request": request, "title": "YOLO REST Server"})
