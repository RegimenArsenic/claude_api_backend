from common.utils import *
import sys

sys.path.append("./Claude-API/claude-api")
import os
import json
from flask import Flask, request, jsonify, stream_with_context, Response
from claude_api import Client

app = Flask(__name__)


@app.route('/chat', methods=['POST'])
def create_chat():
    data = request.get_json()
    prompt = data['prompt']

    cookie = get_cookie()
    client = Client(cookie)
    conversation = client.create_new_chat()
    conversation_id = conversation['uuid']

    response = client.send_message(prompt, conversation_id)
    return jsonify({'conversation_id': conversation_id, 'response': response})


@app.route('/chat/<conversation_id>')
def get_chat_history(conversation_id):
    cookie = get_cookie()
    client = Client(cookie)
    history = client.chat_conversation_history(conversation_id)
    return jsonify(history)


@app.route('/send', methods=['POST'])
def send_message():
    file = None
    if (len(request.files)):
        file = request.files['file']
        data = json.loads(request.form.get("json"))
    else:
        data = request.get_json()
    conversation_id = data['conversation_id']
    prompt = data['prompt']
    file_path = None
    if file:
        file_path = save_upload_file(file)
    cookie = get_cookie()
    client = Client(cookie)
    response = client.send_message(prompt, conversation_id, file_path)
    return jsonify({'response': response})


@app.route('/stream', methods=['POST'])
def query_stream():
    file = None
    if (len(request.files)):
        file = request.files['file']
        data = json.loads(request.form.get("json"))
    else:
        data = request.get_json()
    conversation_id = data['conversation_id']
    prompt = data['prompt']
    file_path = None
    if file:
        file_path = save_upload_file(file)
    cookie = get_cookie()
    client = Client(cookie)
    return Response(stream_with_context(client._query_stream(prompt, conversation_id, file_path)), content_type='text/event-stream')


@app.route('/reset', methods=['POST'])
def reset_conversations():
    cookie = get_cookie()
    client = Client(cookie)
    result = client.reset_all()
    return jsonify({'result': result})


@app.route('/rename', methods=['POST'])
def rename_conversation():
    data = request.get_json()
    conversation_id = data['conversation_id']
    title = data['title']

    cookie = get_cookie()
    client = Client(cookie)
    result = client.rename_chat(title, conversation_id)
    return jsonify({'result': result})


@app.route('/upload', methods=['POST'])
def upload_attachment():
    file = request.files['file']
    if file:
        file_path = save_upload_file(file)
        cookie = get_cookie()
        client = Client(cookie)
        response = client.upload_attachment(file_path)
        return jsonify({'result': response})
    else:
        return jsonify({'error': 'No file uploaded'}), 400


def save_upload_file(file):
    uploads_dir = os.getenv('uploads')
    file_path = os.path.join(uploads_dir, file.filename)
    file.save(file_path)
    return file_path


@app.route('/conversations')
def list_all_conversations():
    cookie = get_cookie()
    client = Client(cookie)
    conversations = client.list_all_conversations()
    return jsonify(conversations)


@app.route('/history/<conversation_id>')
def chat_conversation_history(conversation_id):
    cookie = get_cookie()
    client = Client(cookie)
    history = client.chat_conversation_history(conversation_id)
    return jsonify(history)


@app.route('/setcookie', methods=['POST'])
def setcookie():
    data = request.get_json()
    cookie = data['cookie']
    if cookie:
        return jsonify({'result': set_cookie(cookie)})
    else:
        return jsonify({'error': 'Invaild cookie environment variable'}), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4149, debug=True, use_reloader=True)
    app.default_encoding = 'utf-8'
