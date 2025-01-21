from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from transformers import pipeline
from typing import Annotated

app = FastAPI()

# 質問応答モデルのロード
qa_pipeline = pipeline("question-answering", model="deepset/roberta-base-squad2")


@app.get("/", response_class=HTMLResponse)
async def index():
    """トップページを表示"""
    return """
    <html>
        <head>
            <title>QA App</title>
        </head>
        <body>
            <h1>PDFPlumber</h1>
            <form action="/answer" method="post">
                <label for="context">Context:</label><br>
                <textarea id="context" name="context" rows="5" cols="50" required></textarea><br><br>
                <label for="question">Question:</label><br>
                <input id="question" name="question" type="text" required><br><br>
                <button type="submit">Get Answer</button>
            </form>
        </body>
    </html>
    """
# name="context"とname="question"の値をpostで送信することができる．


@app.post("/answer", response_class=HTMLResponse)
async def get_answer(context: Annotated[str, Form(...)], question: Annotated[str, Form(...)]):
    """質問応答を処理"""
    result = qa_pipeline(question=question, context=context)
    answer = result.get("answer", "No answer found.")
    score = result.get("score", 0)

    return f"""
    <html>
        <head>
            <title>QA Result</title>
        </head>
        <body>
            <h1>Answer</h1>
            <p><strong>Question:</strong> {question}</p>
            <p><strong>Answer:</strong> {answer}</p>
            <p><strong>Confidence Score:</strong> {score:.2f}</p>
            <a href="/">Back</a>
        </body>
    </html>
    """
