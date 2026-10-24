from fastapi import Request
from fastapi.responses import JSONResponse

from server.utils.jwtutils import decode_token


def identity_from_token(token):
  identity = decode_token(token) if token else False
  user_id = identity.get('id') if isinstance(identity, dict) else None
  if not isinstance(user_id, str) or not user_id.strip():
    return None
  return identity


async def request_identity_middleware(request: Request, call_next):
  public_routes = {
    ('POST', '/sys/auth/login'),
    ('POST', '/sys/auth/regist'),
  }
  if (
    request.url.path in {'/', '/health'}
    or request.url.path.startswith('/static/')
    or (request.method, request.url.path) in public_routes
  ):
    request.state.user = None
    return await call_next(request)

  token = request.headers.get('token')
  identity = identity_from_token(token)
  if identity is None:
    return JSONResponse(
      status_code=401,
      content={
        'code': '4001',
        'success': False,
        'data': None,
        'msg': '登录凭证无效或已过期'
      }
    )

  request.state.user = identity
  return await call_next(request)
