from flask import Flask, render_template, stream_with_context, Response
import time

app = Flask(__name__)

def generate():
    # 这是一个简单的例子，实际中可能是一个不断更新的数据流
    for i in range(5):
        time.sleep(1)  # 模拟一些耗时操作
        yield f"data: {i}\n\n"

@app.route('/events')
def events():
    # 使用 stream_with_context 函数来创建一个流式响应
    return Response(stream_with_context(generate()), content_type='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)