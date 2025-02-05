from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont  # フォント指定
from reportlab.pdfgen import canvas
from reportlab.platypus import Image

from util.text_table_util import async_detect_document, extract_table

pdfmetrics.registerFont(TTFont("NotoSansJP", "NotoSansJP-Regular.ttf"))


def create_pdf(output_path, user_text, image_path):
    # A4のPDFを作成
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    print(f"{width=}, {height=}")

    # 文字の描画
    c.setFont("NotoSansJP", 30)
    c.drawString(20 * mm, (height - 20 * mm), f"ユーザ入力: {user_text}")

    # 画像の描画
    # (x座標, y座標, 幅, 高さ)
    c.drawImage(image_path, 20 * mm, (height - 60 * mm), width=50 * mm, height=30 * mm)

    # PDFを確定
    c.showPage()
    c.save()


def yolov8():
    from ultralytics import SAM, YOLO

    # load model
    print("Loading model...")
    # model = YOLO("api/model/YOLOv10s.pt")
    model = SAM("api/model/mobile_sam.pt")
    print("Model loaded")

    # # set model parameters
    # model.overrides["conf"] = 0.25  # NMS confidence threshold
    # model.overrides["iou"] = 0.45  # NMS IoU threshold
    # model.overrides["agnostic_nms"] = False  # NMS class-agnostic
    # model.overrides["max_det"] = 1000  # maximum number of detections per image

    # set image
    image = "zidane.jpg"

    # perform inference
    # results = model.predict(image, points=[900, 370], labels=[1])
    results = model.predict(
        image,
        save=False,
        project="runs",
        name="test",
        exist_ok=True,
    )
    # # results.verbose()
    for result in results:
        # print(f"{result=}")
        print(result.verbose())
        print(result.save("outputs/test2.jpg", boxes=False, labels=False))
        # result.show()
    # print(f"{results[0]=}")
    # results[0].show()
    # print(f"{type(results)=}")

    # observe results
    # print(f"{results[1]=}")
    # render = render_result(model=model, image=image, result=results[0])
    # render.show()


def table_ex():
    import pdfplumber

    pdf_path = "PDFs/DX白書2023 第2部.pdf"
    extract_table(pdf_path)
    # print(table_data)


if __name__ == "__main__":
    # create_pdf("outputs/custom_output.pdf", user_text="ReportLabによる文字配置サンプルです。", image_path="wakeupcat.jpg")
    # yolov8()
    table_ex()
    # async_detect_document("gs://cloud-samples-data/vision/pdf_tiff/census2010.pdf", "gs://cloud-samples-data/vision/pdf_tiff/census2010.json")
