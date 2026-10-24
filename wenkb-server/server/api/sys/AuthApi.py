from datetime import datetime
import binascii

from fastapi import FastAPI
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError

from server.api.BaseApi import BaseApi
from server.db.DbManager import session_scope
from server.exception.exception import BaseBusiException
from server.model.orm_sys import UserAccount
from server.utils.jwtutils import generate_token
from server.utils.passwordutils import hash_password, verify_password
from server.utils.secretutils import aes_decrypt


class AuthRequest(BaseModel):
  username: str = Field(min_length=1, max_length=128)
  password: str = Field(min_length=1, max_length=512)
  nickname: str | None = Field(None, max_length=80)
  cfimpswd: str | None = Field(None, max_length=512)


class AuthApi(BaseApi):
  def __init__(self, app: FastAPI):
    super().__init__()

    @app.post('/sys/auth/regist')
    def register(form: AuthRequest):
      username = form.username.strip().casefold()
      nickname = (form.nickname or '').strip() or username
      if not username or len(username) > 128:
        raise BaseBusiException('账号不能为空且不能超过 128 个字符', status_code=400)
      if len(nickname) > 80:
        raise BaseBusiException('昵称不能超过 80 个字符', status_code=400)
      if not form.cfimpswd:
        raise BaseBusiException('请确认登录密码', status_code=400)
      password = self.decrypt_password(form.password)
      confirmation = self.decrypt_password(form.cfimpswd)
      if len(password) < 8 or len(password) > 128:
        raise BaseBusiException('密码长度须为 8 到 128 个字符', status_code=400)
      if confirmation is not None and password != confirmation:
        raise BaseBusiException('两次输入的密码不一致', status_code=400)

      account = UserAccount(
        userId=self.getPk(),
        username=username,
        nickname=nickname,
        passwordHash=hash_password(password),
        status='Y',
        crtTm=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
      )
      try:
        with session_scope() as session:
          if session.query(UserAccount).filter_by(username=username).first():
            raise BaseBusiException('该账号已注册', status_code=409)
          session.add(account)
      except IntegrityError:
        raise BaseBusiException('该账号已注册', status_code=409)
      return self.success({'id': account.userId, 'name': account.nickname})

    @app.post('/sys/auth/login')
    def login(form: AuthRequest):
      username = form.username.strip().casefold()
      password = self.decrypt_password(form.password)
      with session_scope(True) as session:
        account = session.query(UserAccount).filter_by(username=username).first()
        if account is None or account.status != 'Y' or not verify_password(password, account.passwordHash):
          raise BaseBusiException('账号或密码错误', status_code=401)
        identity = {'id': account.userId, 'name': account.nickname}
      try:
        token = generate_token(identity)
      except ValueError:
        raise BaseBusiException('服务端尚未正确配置 WENKB_JWT_SECRET', status_code=503)
      return self.success({**identity, 'token': token})

  @staticmethod
  def decrypt_password(ciphertext):
    if not ciphertext or len(ciphertext) > 512:
      raise BaseBusiException('密码格式无效', status_code=400)
    try:
      plaintext = aes_decrypt(ciphertext)
    except (ValueError, TypeError, binascii.Error, UnicodeDecodeError):
      raise BaseBusiException('密码格式无效，请刷新页面后重试', status_code=400)
    if not plaintext:
      raise BaseBusiException('密码不能为空', status_code=400)
    return plaintext
