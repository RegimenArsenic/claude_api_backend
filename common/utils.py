import io
import os
import jwt
import hashlib
from dotenv import load_dotenv
from PIL import Image


def md5_hash(input_string):
  md5 = hashlib.md5()
  md5.update(input_string.encode('utf-8'))
  hashed_string = md5.hexdigest()
  return hashed_string


# 签名函数
def sign(data={}):
  return jwt.encode(data, os.getenv('secret_key'), algorithm='HS256')


@staticmethod
def decode_auth_token(auth_token):
  try:
    payload = jwt.decode(auth_token, os.getenv('secret_key'), algorithms='HS256')
    if ('data' in payload and 'id' in payload['data']):
      return payload
    else:
      raise jwt.InvalidTokenError
  except jwt.ExpiredSignatureError:
    return 'Token过期'
  except jwt.InvalidTokenError:
    return '无效Token'


# 用户鉴权
def authorize(req):
  try:
    data = req.get_json()
    authPassword = os.getenv('login_password')
    if (not authPassword):
      return True
    if (req is None):
      return False
    authorization = req.cookies.get('Authorization')
    if (authorization):
      payload = decode_auth_token(authorization)
      if not isinstance(payload, str):
        authPassword = hashlib.md5(authPassword).hexdigest()
        password = data.get('password')
        if (password != authPassword):
          return False
        else:
          return True
    return False

  except jwt.ExpiredSignatureError:
    #result = 'Token已更改，请重新登录获取'
    return False

  except jwt.InvalidTokenError:
    #result = '没有提供认证token'
    return False


# 定义白名单
white_list = ['/login']


# 授权处理函数
async def authorize_handler(req):
  if req.url not in white_list:
    # 判断请求头是否携带正确的token
    try:
      return authorize(req)
    except Exception as e:
      print(e)
      return False
  else:
    return True


def fsize(file):
  if isinstance(file, io.BytesIO):
    return file.getbuffer().nbytes
  elif isinstance(file, str):
    return os.path.getsize(file)
  elif hasattr(file, "seek") and hasattr(file, "tell"):
    pos = file.tell()
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(pos)
    return size
  else:
    raise TypeError("Unsupported type")


def compress_imgfile(file, max_size):
  if fsize(file) <= max_size:
    return file
  file.seek(0)
  img = Image.open(file)
  rgb_image = img.convert("RGB")
  quality = 95
  while True:
    out_buf = io.BytesIO()
    rgb_image.save(out_buf, "JPEG", quality=quality)
    if fsize(out_buf) <= max_size:
      return out_buf
    quality -= 5


def split_string_by_utf8_length(string, max_length, max_split=0):
  encoded = string.encode("utf-8")
  start, end = 0, 0
  result = []
  while end < len(encoded):
    if max_split > 0 and len(result) >= max_split:
      result.append(encoded[start:].decode("utf-8"))
      break
    end = min(start + max_length, len(encoded))
    # 如果当前字节不是 UTF-8 编码的开始字节，则向前查找直到找到开始字节为止
    while end < len(encoded) and (encoded[end] & 0b11000000) == 0b10000000:
      end -= 1
    result.append(encoded[start:end].decode("utf-8"))
    start = end
  return result


load_dotenv()


def get_cookie():
  #cookie = os.environ.get('cookie')
  cookie = os.getenv('cookie')
  print(cookie)
  if not cookie:
    raise ValueError("Please set the 'cookie' environment variable.")
  return cookie


def set_cookie(cookie):
  if not cookie:
    raise ValueError("Invaild 'cookie' environment variable.")
  os.environ["cookie"] = cookie
  print(os.getenv('cookie'))
  return cookie
