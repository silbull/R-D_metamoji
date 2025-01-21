# Imports the Google Cloud client library
import os

from google.cloud import storage, vision

"""
https://nikkie-ftnext.hatenablog.com/entry/ocr-with-google-vision-api-python-first-step
gcloud auth application-default loginをやるとApplication Default Credentialsが設定されるから，使えるようになった？っぽい
"""


# Google Cloud Storageのパスを解析
def download_gcs_file(gcs_uri, local_path):
    # gs://bucket-name/path/to/file.jpg の形式から必要な情報を抽出
    bucket_name = gcs_uri.split("/")[2]
    blob_name = "/".join(gcs_uri.split("/")[3:])

    # Storageクライアントを初期化
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    # ローカルにダウンロード
    blob.download_to_filename(local_path)
    return


def run_quickstart() -> vision.EntityAnnotation:
    """Provides a quick start example for Cloud Vision."""

    # Instantiates a client
    client = vision.ImageAnnotatorClient()

    # The URI of the image file to annotate
    file_uri = "gs://cloud-samples-data/vision/label/wakeupcat.jpg"

    # ローカルに画像を保存する
    download_gcs_file(file_uri, "wakeupcat.jpg")

    image = vision.Image()
    image.source.image_uri = file_uri

    # Performs label detection on the image file
    response = client.label_detection(image=image)
    labels = response.label_annotations

    print("Labels:")
    for label in labels:
        print(label.description)

    return labels


def detect_text(path):
    """Detects text in the file.
    https://cloud.google.com/vision/docs/ocr?hl=ja
    """
    from google.cloud import vision

    client = vision.ImageAnnotatorClient()

    with open(path, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations
    print("Texts:")

    for text in texts:
        print(f'\n"{text.description}"')

        vertices = [f"({vertex.x},{vertex.y})" for vertex in text.bounding_poly.vertices]

        print("bounds: {}".format(",".join(vertices)))

    if response.error.message:
        raise Exception(
            f"{response.error.message}\nFor more info on error messages, check: https://cloud.google.com/apis/design/errors"
        )


if __name__ == "__main__":
    print(run_quickstart())
    # detect_text("uploads/1736234045_9D0CBF02-F663-4C48-A0FA-8E23EEBE58E6.JPEG")
