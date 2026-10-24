import asyncio
import os
import sys

SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
if os.getcwd() != SERVER_DIR:
  os.chdir(SERVER_DIR)
if SERVER_DIR not in sys.path:
  sys.path.insert(0, SERVER_DIR)

import uvicorn
from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from logger import logger
from server.api.sys.FileApi import FileApi
from server.api.sys.AuthApi import AuthApi
from server.api.sys.SettingApi import SettingApi
from server.api.sys.HealthApi import HealthApi
from server.api.knb.ReposInfoApi import ReposInfoApi
from server.api.knb.DatasetApi import DatasetApi
from server.api.knb.ChatApi import ChatApi
from server.api.knb.SearchApi import SearchApi
from server.api.doc.DocsetInfoApi import DocsetInfoApi
from contextlib import asynccontextmanager
from server.core.scheduler.Scheduler import datasetToVectorQueueJob, datasetEnhanceQueueJob
from server.utils.websocketutils import WebsocketManager
from server.exception.exception import golbal_exception_handlers, global_exceptions_middleware
from server.utils.authmiddleware import identity_from_token, request_identity_middleware
from server.utils.jwtutils import ensure_secret_key
from config.common import DEFAULT_STATIC_DIR_NAME, DEFAULT_DOCUMENT_DIR_NAME

from server.db.DbUpgrade import upgrade_db
upgrade_db()

@asynccontextmanager
async def lifespan(app: FastAPI):
  logger.error('----app startup----')
  ensure_secret_key()
  asyncio.create_task(datasetToVectorQueueJob())
  asyncio.create_task(datasetEnhanceQueueJob())
  yield
  logger.error('----app shutdown----')

app = FastAPI(lifespan=lifespan, debug=True, exception_handlers=golbal_exception_handlers)
# 全局未处理的错误处理
app.middleware('http')(global_exceptions_middleware)
# 将'static'目录设置为静态文件目录
app.mount(f'/{DEFAULT_STATIC_DIR_NAME}/{DEFAULT_DOCUMENT_DIR_NAME}', StaticFiles(directory=f'./resources/{DEFAULT_DOCUMENT_DIR_NAME}'), name=DEFAULT_DOCUMENT_DIR_NAME)
app.mount(f'/{DEFAULT_STATIC_DIR_NAME}', StaticFiles(directory=f'./resources/{DEFAULT_STATIC_DIR_NAME}'), name=DEFAULT_STATIC_DIR_NAME)

router = APIRouter()
manager = WebsocketManager()

FileApi(app)
AuthApi(app)
SettingApi(app)
HealthApi(app)
ReposInfoApi(app, manager)
DatasetApi(app, manager)
ChatApi(app, manager)
SearchApi(app, manager)
DocsetInfoApi(app)

@router.websocket('/ws/knb/{client_id}')
async def websocket_serve(client_id: str, websocket: WebSocket):
  identity = identity_from_token(client_id)
  if identity is None:
    await websocket.close(code=1008)
    return
  websocket.state.user = identity
  # 1、客户端、服务端建立 ws 连接
  await websocket.accept()
  manager.connect(client_id, websocket)
  # # 2、广播某个客户端进入聊天室
  # await manager.broadcast(f"{client_id} 进入了聊天室")
  try:
    while True:
      # 3、服务端接收客户端发送的内容
      data = await websocket.receive_text()
      # 4、广播某个客户端发送的消息
      # await manager.broadcast(f"{client_id} 发送消息：{data}")
      # 5、服务端回复客户端
      # await manager.send_message_to_client(f"服务端回复{client_id}：你发送的信息是：{data}", websocket)
  except WebSocketDisconnect:
    # 6、若有客户端断开连接，广播某个客户端离开了
    manager.disconnect(client_id)
    # await manager.broadcast(f"{client_id} 离开了聊天室")

app.include_router(router)

app.middleware('http')(request_identity_middleware)

@app.get('/')
def repositoryList():
  return 'hello world'

if __name__ == '__main__':
  uvicorn.run(app, host='0.0.0.0', port=16088, log_level='debug')
