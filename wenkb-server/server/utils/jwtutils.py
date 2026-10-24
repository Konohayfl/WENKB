import jwt
import datetime
import os
import secrets
from pathlib import Path

ALGORITHM = 'HS256'
SECRET_FILE_PATH = Path(__file__).resolve().parents[2] / 'resources' / 'jwt_secret.key'


def ensure_secret_key():
  secret = os.environ.get('WENKB_JWT_SECRET')
  if secret is not None:
    if len(secret.encode('utf-8')) < 32:
      raise ValueError('WENKB_JWT_SECRET must contain at least 32 bytes')
    return secret

  SECRET_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
  try:
    with SECRET_FILE_PATH.open('x', encoding='utf-8') as secret_file:
      secret_file.write(secrets.token_urlsafe(48))
      secret_file.flush()
      os.fsync(secret_file.fileno())
  except FileExistsError:
    pass

  secret = SECRET_FILE_PATH.read_text(encoding='utf-8').strip()
  if len(secret.encode('utf-8')) < 32:
    raise ValueError('Stored WENKB JWT secret must contain at least 32 bytes')
  return secret

def get_secret_key():
  try:
    return ensure_secret_key()
  except (OSError, ValueError):
    return None

# 创建token
def generate_token(inf:dict):
  secret = get_secret_key()
  if secret is None:
    raise ValueError('WENKB_JWT_SECRET must contain at least 32 bytes')
  payload = {
    'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7), # 有效期七天
    'iat': datetime.datetime.utcnow(),
    'inf': inf
  }
  return jwt.encode(
    payload,
    secret,
    algorithm=ALGORITHM
  )
  
# 解析token
def decode_token(token):
  """ 解码Token并处理异常 """
  secret = get_secret_key()
  if secret is None:
    return False
  try:
    payload = jwt.decode(token, secret, algorithms=['HS256'])
    return payload['inf']  # 返回成功标志和内容
  except jwt.ExpiredSignatureError as e:
    return False
  except jwt.InvalidTokenError as e:
    return False
