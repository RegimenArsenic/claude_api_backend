from common.utils import *
import sys

sys.path.append("./Claude-API/claude-api")
import os
import json
from flask import Flask, request, jsonify, Response
from claude_api import Client
import datetime

app = Flask(__name__)


# 注册中间件，使其对所有请求生效
@app.before_request
def before_request():
  result = authorize_handler(request)
  if not result:
    return {'message': 'Unauthorized'}, 401


@app.route('/login', methods=['POST'])
def login_handler():
  # try:
  data = request.get_json()
  if data:
    if data.get('password') == md5_hash(os.getenv('login_password')):
      iat = datetime.datetime.utcnow()
      payload = {
          'iss': 'momo',
          'iat': iat.timestamp(),  # 开始时间
          'exp': (iat + datetime.timedelta(days=0, hours=int(os.getenv('expires_in')))).timestamp(),  # 过期时间
          'data': {
              'id': data.get('id'),
              'login_time': iat.timestamp()
          },
      }
      return jsonify({
          'error': 0,
          'data': '登录成功',
          'id': data.get('id'),
          'token': sign(payload),
      })
    else:
      return {'message': '密码错误'}, 401
  return {'message': '发生内部错误'}, 401


# except Exception as err:
#   print(str(err))
#   return {'message': '发生内部错误'}, 500


@app.route('/api/chat', methods=['POST'])
def create_chat():
  data = request.get_json()
  prompt = data['prompt']

  cookie = get_cookie()
  client = Client(cookie)
  conversation = client.create_new_chat()
  conversation_id = conversation['uuid']

  response = client.send_message(prompt, conversation_id)
  return jsonify({'conversation_id': conversation_id, 'response': response})


@app.route('/api/chat/<conversation_id>')
def get_chat_history(conversation_id):
  cookie = get_cookie()
  client = Client(cookie)
  history = client.chat_conversation_history(conversation_id)
  return jsonify(history)


@app.route('/api/send', methods=['POST'])
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


@app.route('/api/stream', methods=['POST'])
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

  def handle_result(prompt, conversation_id, file_path):
    for data in client._query_stream(prompt, conversation_id, file_path):
      yield f"event:update\n\ndata: '{data}'\n\n"
    yield f"event:finish\n\ndata: ''\n\n"

  return Response(handle_result(prompt, conversation_id, file_path), content_type='text/event-stream')


@app.route('/api/reset', methods=['POST'])
def reset_conversations():
  cookie = get_cookie()
  client = Client(cookie)
  result = client.reset_all()
  return jsonify({'result': result})


@app.route('/api/rename', methods=['POST'])
def rename_conversation():
  data = request.get_json()
  conversation_id = data['conversation_id']
  title = data['title']

  cookie = get_cookie()
  client = Client(cookie)
  result = client.rename_chat(title, conversation_id)
  return jsonify({'result': result})


@app.route('/api/upload', methods=['POST'])
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


@app.route('/api/conversations')
def list_all_conversations():
  cookie = get_cookie()
  client = Client(cookie)
  conversations = client.list_all_conversations()
  return jsonify(conversations)


@app.route('/api/history/<conversation_id>')
def chat_conversation_history(conversation_id):
  cookie = get_cookie()
  client = Client(cookie)
  history = client.chat_conversation_history(conversation_id)
  return jsonify(history)


@app.route('/api/delete/<conversation_id>')
def chat_delete_conversation(conversation_id):
  cookie = get_cookie()
  client = Client(cookie)
  result = client.delete_conversation(conversation_id)
  return jsonify({result: result})


@app.route('/api/setcookie', methods=['POST'])
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
