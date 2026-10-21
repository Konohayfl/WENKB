from fastapi import FastAPI, Request
from server.db.DbManager import session_scope
from server.api.BaseApi import BaseApi
from sqlalchemy import select, delete
from server.model.orm_knb import SrchHist, ReposSetting, Dataset
from server.model.entity_knb import SrchInfo as SrchInfoEntity, SrchHist as SrchHistEntity, ReposSetting as ReposSettingEntity
from datetime import datetime
from server.core.tools.ask_to_llm import get_related_docs_by_repos_id
from server.utils.websocketutils import WebsocketManager
from server.exception.exception import BaseBusiException
from server.core.knb.ReposService import ReposService
from config.llm import SIMILARITY_TRVAL, TOP_K

class SearchApi(BaseApi):
  reposService = ReposService()
  def __init__(self, app: FastAPI, manager: WebsocketManager):
    BaseApi.__init__(self)

    def require_repository_access(reposId: str, request: Request, owner: bool = False):
      repository = self.reposService.select_by_repos_id_and_user_id(
        reposId, self.getUserId(request)
      )
      if repository is None:
        raise BaseBusiException('知识库不存在或已被删除', status_code=404)
      if owner and repository.optAuth != 'alter':
        raise BaseBusiException('您没有权限修改该知识库', status_code=403)
      return repository
  
    # 搜索
    @app.post('/knb/search')
    def search(srchInfo: SrchInfoEntity, request: Request):
      reposId = srchInfo.reposId
      require_repository_access(reposId, request)
      if (not srchInfo.noHist):
        srchHist = SrchHistEntity(
          srchId = self.getPk(),
          reposId = reposId,
          srchText = srchInfo.searchTxt,
          srchTm = datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
          crtUser = self.getUserId(request)
        )
        orm = SrchHist().copy_from_dict(vars(srchHist))
        with session_scope() as session:
          session.add(orm)
      
      with session_scope(True) as session:
        setting_orm = session.get(ReposSetting, reposId)
        active_dataset_ids = set(session.scalars(
          select(Dataset.dtsetId).where(
            Dataset.reposId == reposId,
            Dataset.enbSts == 'enb',
            Dataset.idxSts == 'ready',
          )
        ).all())
      setting = ReposSettingEntity(
        reposId=reposId,
        topK=(setting_orm.topK if setting_orm and setting_orm.topK and setting_orm.topK > 0 else TOP_K),
        smlrTrval=(setting_orm.smlrTrval if setting_orm and setting_orm.smlrTrval is not None else SIMILARITY_TRVAL),
      )
      related_docs_with_score = get_related_docs_by_repos_id(
        reposId=reposId,
        question=srchInfo.searchTxt,
        setting=setting,
        dataset_ids=active_dataset_ids,
      )
      data = []
      if (not related_docs_with_score):
        return self.success(data)
      for doc, score in related_docs_with_score:
        metadata = doc.metadata
        dtsetId = metadata.get('dtsetId')
        if (dtsetId is None and 'source' in metadata):
          source = metadata['source']
          dtsetId = (source.split('/')[-1]).split('.')[0]
        if (dtsetId is None):
          continue
        if dtsetId not in active_dataset_ids or float(score) >= setting.smlrTrval:
          continue
        data.append({
          'srcId': dtsetId, # 来源文件ID
          'score': float(score),
          'content': doc.page_content,
          'srcNm': metadata.get('dtsetNm', ''),
          'srcTyp': metadata.get('fileTyp', '')
        })
      return self.success(data)
    
    # 搜索历史查询
    @app.post('/knb/search/hist/list')
    def searchHistList(srchHist: SrchHistEntity, request: Request):
      reposId = srchHist.reposId
      require_repository_access(reposId, request)
      stmt = select(SrchHist).where(SrchHist.reposId == reposId).order_by(SrchHist.srchTm.desc()).limit(10)
      list = []
      with session_scope(True) as session:
        for row in session.scalars(stmt):
          list.append(row)
      return self.success(list)
    
    # 搜索我的历史查询
    @app.post('/knb/search/hist/my/list')
    def searchHistList(srchHist: SrchHistEntity, request: Request):
      reposId = srchHist.reposId
      require_repository_access(reposId, request)
      stmt = select(SrchHist).where(SrchHist.reposId == reposId, SrchHist.crtUser == self.getUserId(request)).order_by(SrchHist.srchTm.desc()).limit(10)
      list = []
      with session_scope(True) as session:
        for row in session.scalars(stmt):
          list.append(row)
      return self.success(list)
    
    # 移除搜索历史
    @app.delete('/knb/search/hist/{srchId}')
    def searchHistRemove(srchId: str, request: Request):
      with session_scope() as session:
        orm = session.get(SrchHist, srchId)
        if (orm is None):
          return self.success()
        repository = require_repository_access(orm.reposId, request)
        if orm.crtUser != self.getUserId(request) and repository.optAuth != 'alter':
          raise BaseBusiException('您没有权限删除该搜索历史', status_code=403)
        stmt = delete(SrchHist).where(SrchHist.srchId == srchId)
        session.execute(stmt)
      return self.success()
