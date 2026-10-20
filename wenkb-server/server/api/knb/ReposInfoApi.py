from fastapi import FastAPI, Request, Body
from server.db.DbManager import session_scope
from server.api.BaseApi import BaseApi
from sqlalchemy import select, delete
from datetime import datetime
from server.model.orm_knb import ReposInfo, ChatInfo, ChatMesg, ReposQuest, ReposSetting, Dataset
from server.model.entity_base import PageBase
from server.model.entity_knb import ReposInfo as ReposInfoEntity, ReposQuest as ReposQuestEntity, ReposSetting as ReposSettingEntity
from server.utils.websocketutils import WebsocketManager
from server.core.knb.ReposService import ReposService
from server.exception.exception import BaseBusiException
from config.llm import MAX_CONTEXT, MAX_HISTORY, TEMPERATURE, SIMILARITY_TRVAL, TOP_K

class ReposInfoApi(BaseApi):
  reposService = ReposService()
  def __init__(self, app: FastAPI, manager: WebsocketManager):
    BaseApi.__init__(self)

    def require_repository_access(reposId: str, request: Request, owner: bool = False):
      userId = self.getUserId(request)
      with session_scope(True) as session:
        orm = session.get(ReposInfo, reposId)
        if (orm is None):
          raise BaseBusiException('知识库不存在或已被删除', error_code='4004', status_code=404)
        if (orm.crtUser != userId and orm.authRang != 'pblc'):
          raise BaseBusiException('您没有权限访问该知识库', error_code='4003', status_code=403)
        if (owner and orm.crtUser != userId):
          raise BaseBusiException('您没有权限修改该知识库', error_code='4003', status_code=403)
        repository = ReposInfoEntity().copy_from_dict(orm.to_dict())
        repository.optAuth = 'alter' if orm.crtUser == userId else 'visit'
        return repository

    # 获取单个知识库
    @app.get('/knb/repository/{id}')
    def getRepository(id: str, request: Request):
      return self.success(require_repository_access(id, request))
    
    # 修改名称
    @app.put('/knb/repository/name')
    def editRepositoryName(reposInfo: ReposInfoEntity, request: Request):
      reposId = reposInfo.reposId
      require_repository_access(reposId, request, owner=True)
      with session_scope() as session:
        orm = session.get(ReposInfo, reposId)
        orm.reposNm = reposInfo.reposNm
        session.merge(orm)
      return self.success()
    
    # 修改介绍
    @app.put('/knb/repository/desc')
    def editRepositoryDesc(reposInfo: ReposInfoEntity, request: Request):
      reposId = reposInfo.reposId
      require_repository_access(reposId, request, owner=True)
      with session_scope() as session:
        orm = session.get(ReposInfo, reposId)
        orm.reposDesc = reposInfo.reposDesc
        session.merge(orm)
      return self.success()
    
    # 修改权限
    @app.put('/knb/repository/auth/range')
    def editRepositoryAuthRange(reposInfo: ReposInfoEntity, request: Request):
      reposId = reposInfo.reposId
      authRang = reposInfo.authRang
      require_repository_access(reposId, request, owner=True)
      with session_scope() as session:
        orm = session.get(ReposInfo, reposId)
        if (orm.authRang == authRang):
          return self.success()
        orm.authRang = authRang
        session.merge(orm)
        # if (authRang == 'prvt' or authRang == 'pblc'): # 需要删除团队信息
        #   session.query(ReposTeam).filter(ReposTeam.reposId == reposId).delete()
      return self.success()

    # 查询知识库列表
    @app.post('/knb/repository/list')
    def repositoryList(request: Request):
      return self.success(self.reposService.select_list_by_user_id(self.getUserId(request)))
    
    # 查询知识库列表
    @app.post('/knb/repository/my/list')
    def repositoryList(request:Request):
      return self.success(self.reposService.select_list_by_user_id(self.getUserId(request)))
    
    # 新增知识库
    @app.post('/knb/repository')
    def addRepository(reposInfo: ReposInfoEntity, request: Request):
      # reposId='' reposNm='123456' reposDesc='' reposIcon=None crtUser=None authRang=None
      if reposInfo.reposNm is None or not reposInfo.reposNm.strip():
        raise BaseBusiException('知识库名称不能为空', error_code='4001', status_code=400)
      if reposInfo.vecModlId is None or reposInfo.vecModlId == '':
        raise BaseBusiException('请选择构建索引的模型', error_code='4001', status_code=400)
      userId = self.getUserId(request=request)
      if userId is None:
        raise BaseBusiException('请先登录后再创建知识库', error_code='4001', status_code=401)
      reposInfo.reposNm = reposInfo.reposNm.strip()
      reposInfo.reposId = self.getPk()
      reposInfo.crtTm = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
      reposInfo.crtUser = userId
      if (reposInfo.reposTyp is None):
        reposInfo.reposTyp = 'nml' # 知识库类型：nml 通用知识库，tbl 表格知识库
      if (reposInfo.authRang is None):
        reposInfo.authRang = 'prvt'
      orm = ReposInfo().copy_from_dict(reposInfo.to_dict())
      with session_scope() as session:
        session.add(orm)
        session.add(ReposSetting(
          reposId=reposInfo.reposId,
          maxCtx=MAX_CONTEXT,
          maxHist=MAX_HISTORY,
          llmTptur=TEMPERATURE,
          smlrTrval=SIMILARITY_TRVAL,
          topK=TOP_K
        ))
      return self.success(reposInfo)
    
    # 修改知识库 todo 需要同时删除索引库
    @app.put('/knb/repository')
    def editRepository(reposInfo:ReposInfoEntity, request: Request):
      # reposId='' reposNm='123456' reposDesc='' reposIcon=None crtUser=None authRang=None
      reposId = reposInfo.reposId
      with session_scope() as session:
        orm = session.get(ReposInfo, reposId)
        if (orm is None):
          raise BaseBusiException('知识库不存在或已被删除', error_code='4004', status_code=404)
        if (orm.crtUser != self.getUserId(request)):
          raise BaseBusiException('您没有权限修改该知识库', error_code='4003', status_code=403)
        if reposInfo.vecModlId is None or reposInfo.vecModlId == '':
          raise BaseBusiException('请选择构建索引的模型', error_code='4001', status_code=400)
        if reposInfo.vecModlId != orm.vecModlId:
          ready_count = session.query(Dataset).where(
            Dataset.reposId == reposId,
            Dataset.idxSts == 'ready'
          ).count()
          if ready_count > 0:
            raise BaseBusiException(
              '知识库已有索引，切换 embedding 模型前请先重建索引',
              error_code='4002',
              status_code=409
            )
        orm.reposNm = reposInfo.reposNm
        orm.reposDesc = reposInfo.reposDesc
        orm.reposIcon = reposInfo.reposIcon
        orm.authRang = reposInfo.authRang
        orm.vecModlId = reposInfo.vecModlId # 嵌入模型
        session.merge(orm)
      return self.success()

    # 删除知识库
    @app.delete('/knb/repository/{id}')
    def removeRepository(id:str, request: Request):
      # reposId='' reposNm='123456' reposDesc='' reposIcon=None crtUser=None authRang=None
      repository = self.reposService.select_by_repos_id_and_user_id(
        id, self.getUserId(request)
      )
      if repository is None or repository.optAuth != 'alter':
        raise BaseBusiException('您没有权限删除该知识库', error_code='4003', status_code=403)
      self.reposService.remove_repository_by_id(id)
      return self.success()
    
    # 删除对话
    @app.delete('/knb/repository/chat/clear/{id}')
    def clearRepositoryChat(id, request: Request):
      repository = self.reposService.select_by_repos_id_and_user_id(
        id, self.getUserId(request)
      )
      if repository is None or repository.optAuth != 'alter':
        raise BaseBusiException('您没有权限清空该知识库聊天', error_code='4003', status_code=403)
      with session_scope() as session:
        stmt = delete(ChatInfo).where(ChatInfo.reposId == id)
        session.execute(stmt)
        stmt = delete(ChatMesg).where(ChatMesg.reposId == id)
        session.execute(stmt)
        from server.model.orm_knb import ChatMesgQuote
        session.execute(delete(ChatMesgQuote).where(ChatMesgQuote.reposId == id))
      return self.success()
  
    # 查询知识库QA列表
    @app.post('/knb/repository/quest/list')
    def repositoryQuestList(reposQuest: ReposQuestEntity, request: Request):
      reposId = reposQuest.reposId
      require_repository_access(reposId, request)
      stmt = select(ReposQuest).where(ReposQuest.reposId == reposId)
      list = []
      with session_scope(True) as session:
        for row in session.scalars(stmt):
          list.append(row)
      return self.success(list)
    
    # 新增QA
    @app.post('/knb/repository/quest')
    def addRepositoryQuest(reposQuest: ReposQuestEntity, request: Request):
      require_repository_access(reposQuest.reposId, request, owner=True)
      return self.success(self.reposService.add_repos_quest(reposQuest))

    # 修改QA
    @app.put('/knb/repository/quest')
    def editRepositoryQuest(reposQuest: ReposQuestEntity, request: Request):
      require_repository_access(reposQuest.reposId, request, owner=True)
      self.reposService.edit_repos_quest(reposQuest)
      return self.success()

    # 移除QA
    @app.delete('/knb/repository/quest/{qstId}')
    def repositoryRemoveQuest(qstId: str, request: Request):
      with session_scope(True) as session:
        orm = session.get(ReposQuest, qstId)
        if (orm is None):
          return self.success()
        require_repository_access(orm.reposId, request, owner=True)
      self.reposService.remove_repos_quest(qstId)
      return self.success()
    
    @app.post('/knb/repository/guess/list')
    def repositoryGuessQuestList(reposQuest: ReposQuestEntity, request: Request):
      reposId = reposQuest.reposId
      qstQuest = reposQuest.qstQuest
      if (qstQuest is None):
        qstQuest = ''
      require_repository_access(reposId, request)
      stmt = select(ReposQuest).where(ReposQuest.reposId == reposId, ReposQuest.qstQuest.ilike(f'%{qstQuest}%')).limit(5)
      list = []
      with session_scope(True) as session:
        for row in session.scalars(stmt):
          list.append(row)
      return self.success(list)
    
    @app.post('/knb/repository/quest/page')
    def repositoryGuessQuestPage(reposQuest: ReposQuestEntity, pageBase: PageBase, request: Request):
      reposId = reposQuest.reposId
      dtsetId = reposQuest.dtsetId
      qstQuest = reposQuest.qstQuest
      if (qstQuest is None):
        qstQuest = ''
      require_repository_access(reposId, request)
      list = []
      with session_scope(True) as session:
        query = session.query(ReposQuest).where(ReposQuest.reposId == reposId, ReposQuest.qstQuest.ilike(f'%{qstQuest}%'))
        stmt = select(ReposQuest).where(ReposQuest.reposId == reposId, ReposQuest.qstQuest.ilike(f'%{qstQuest}%'))
        if (dtsetId is not None and len(dtsetId) > 0):
          query = query.filter(ReposQuest.dtsetId == dtsetId)
          stmt = stmt.filter(ReposQuest.dtsetId == dtsetId)
        total = query.count()
        stmt = stmt.offset(pageBase.get_offset()).limit(pageBase.pageSize)
        for row in session.scalars(stmt):
          list.append(row)
      return self.sucess_page(data=list, total=total, size=pageBase.pageSize, page=pageBase.pageNum)
    

    # 查询知识库设置
    @app.get('/knb/repository/setting/{reposId}')
    def getReposSetting(reposId:str, request: Request):
      require_repository_access(reposId, request)
      return self.success(self.reposService.get_repos_setting(reposId))
    
    # 新增或修改知识库设置
    @app.post('/knb/repository/setting')
    def addOrEditRepositorySetting(setting:ReposSettingEntity, request: Request):
      require_repository_access(setting.reposId, request, owner=True)
      with session_scope() as session:
        orm = ReposSetting().copy_from_dict(setting.to_dict())
        session.merge(orm)
      return self.success()
