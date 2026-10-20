import jwt
import datetime
import os

ALGORITHM = 'HS256'

def get_secret_key():
  secret = os.environ.get('WENKB_JWT_SECRET')
  if secret is None or len(secret.encode('utf-8')) < 32:
    return None
  return secret

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
