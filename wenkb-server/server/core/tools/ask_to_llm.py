import json
import uuid
from logger import logger
from config.llm import TOP_K
from config.prompt import REPOSCHAT_PROMPT_TEMPLATE
from server.core.tools.repos_vector_db import get_or_build_vector_db
from server.utils.websocketutils import WebsocketManager
from server.model.entity_knb import ChatMesg as ChatMesgEntity, ChatMesgQuote as ChatMesgQuoteEntity, ReposSetting as ReposSettingEntity
from server.model.orm_knb import ChatMesg, ChatMesgQuote
from sqlalchemy import delete
from server.db.DbManager import session_scope
from datetime import datetime
from server.core.tools.llm_client_tools import get_user_llm_client
from server.core.tools.message_tools import message_chunk_to_json, message_quote_to_json, message_error_to_json
def prob_related_documents_and_score(related_docs_with_score):
  sources = []
  for doc, score in related_docs_with_score:
    metadata = doc.metadata
    if 'chkId' in metadata:
      source_type = 'chunk'
      source_id = metadata['chkId']
    elif 'prcsId' in metadata:
      source_type = 'summary'
      source_id = metadata['prcsId']
    elif 'qstId' in metadata:
      source_type = 'qa'
      source_id = metadata['qstId']
    elif 'tpltId' in metadata:
      source_type = 'triplet'
      source_id = metadata['tpltId']
    else:
      source_type = 'unknown'
      source_id = None
    sources.append({
      'dtsetId': metadata['dtsetId'],
      'dtsetNm': metadata['dtsetNm'],
      'fileNm': metadata['fileNm'],
      'fileTyp': metadata['fileTyp'],
      'score': score,
      'content': doc.page_content,
      'sourceObjectType': source_type,
      'sourceObjectId': source_id,
      'chkId': metadata.get('chkId')
    })
    # print('%s [%s]: %s' % (doc.metadata['source'], score, doc.page_content))
  return sources

def save_message_quotes(chatMesg: ChatMesgEntity, sources: list):
  sources = sources or []
  now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  with session_scope() as session:
    session.execute(delete(ChatMesgQuote).where(ChatMesgQuote.mesgId == chatMesg.mesgId))
    session.add_all([
      ChatMesgQuote(
        quoteId=str(uuid.uuid4()).replace('-', ''),
        mesgId=chatMesg.mesgId,
        reposId=chatMesg.reposId,
        dtsetId=source.get('dtsetId'),
        chkId=source.get('chkId'),
        srcObjTyp=source.get('sourceObjectType', 'unknown'),
        srcObjId=source.get('sourceObjectId'),
        dtsetNm=source.get('dtsetNm'),
        fileNm=source.get('fileNm'),
        fileTyp=source.get('fileTyp'),
        score=float(source['score']) if source.get('score') is not None else None,
        content=source.get('content') or '',
        quoteOrder=index,
        crtTm=now
      )
      for index, source in enumerate(sources)
    ])

def get_related_docs_by_repos_id(
  reposId: str,
  question: str,
  setting: ReposSettingEntity = ReposSettingEntity(),
  dataset_ids: set[str] = None,
):
  vector_store = get_or_build_vector_db(reposId)
  if (vector_store is None):
    return None
  if dataset_ids is not None and len(dataset_ids) == 0:
    return []
  document_filter = None
  if dataset_ids is not None:
    document_filter = {'dtsetId': {'$in': sorted(dataset_ids)}}
  return get_related_docs_with_score(
    vector_store=vector_store,
    question=question,
    k=setting.topK,
    filter=document_filter,
  )

def get_related_docs_with_score(vector_store, question:str, k:int = TOP_K, filter: dict = None):
  if filter is None:
    return vector_store.similarity_search_with_score(question, k)
  return vector_store.similarity_search_with_score(question, k, filter=filter)

def format_chat_history(chat_history: list[ChatMesgEntity] = None) -> str:
  history = []
  for message in chat_history or []:
    role = '用户' if message.crtRole == 'usr' else '助手'
    history.append(f'{role}: {message.mesgCntnt}')
  return '\n'.join(history)

def generate_llm_prompts(question: str, related_docs_with_score, chat_history: list[ChatMesgEntity] = None) -> str:
  context = '\n'.join([doc.page_content for doc, score in related_docs_with_score])
  history = format_chat_history(chat_history)
  if history:
    question = f'对话历史（仅用于理解当前问题，不作为事实依据）：\n{history}\n\n当前问题：{question}'
  return REPOSCHAT_PROMPT_TEMPLATE.replace('{question}', question).replace('{context}', context)

def get_question_prompts_and_sources(reposId: str, question: str, setting: ReposSettingEntity, chat_history: list[ChatMesgEntity] = None):
  if (question is None or question == ''):
    return None, None
  related_docs_with_score_ = get_related_docs_by_repos_id(reposId, question, setting)
  if (related_docs_with_score_ is None):
    return None, None
  related_docs_with_score = [[doc, score] for doc, score in related_docs_with_score_ if score < setting.smlrTrval ] # 越小越相似
  # 将related_docs_with_score截取setting.maxCtx条
  related_docs_with_score = related_docs_with_score[:setting.maxCtx]
  sources = prob_related_documents_and_score(related_docs_with_score)
  prompts = generate_llm_prompts(question, related_docs_with_score, chat_history)
  return prompts, sources

def persist_chat_message(chatMesg: ChatMesgEntity, content: str):
  with session_scope() as session:
    orm = session.get(ChatMesg, chatMesg.mesgId)
    if orm is None:
      orm = ChatMesg().copy_from_dict(vars(chatMesg))
      orm.crtTm = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    orm.mesgCntnt = content
    session.merge(orm)

# 发送引用数据
async def send_ws_quote_message(chatMesg:ChatMesgEntity, sources:list, manager: WebsocketManager, token: str = None):
  sources = sources or []
  save_message_quotes(chatMesg=chatMesg, sources=sources)
  mesgId = chatMesg.mesgId
  reposId = chatMesg.reposId
  chatId = chatMesg.chatId
  quotes = []
  for source in sources:
    quote = ChatMesgQuoteEntity(mesgId=mesgId).copy_from_dict(source, convert=lambda key,value: value if key != 'score' else float(value))
    quotes.append(vars(quote))
  message = {
    'type': 'chat_message_quote', 'data': {
      'mesgId': mesgId, 'chatId': chatId, 'reposId': reposId, 'quotes': quotes
    }
  }
  message = json.dumps(message, ensure_ascii=False)
  if (token is None):
    await manager.broadcast(message=message)
  else:
    await manager.send_message_to_client_id(message=message, client_id=token)
  return message
# 发送分段消息
async def send_ws_chunk_message(chatMesg: ChatMesgEntity, chunk: str, manager: WebsocketManager, token: str = None):
  chatMesg.mesgCntnt = chunk
  message = {
    'type': 'chat_message_chunk', 'data': vars(chatMesg)
  }
  message = json.dumps(message, ensure_ascii=False)
  if (token is None):
    await manager.broadcast(message=message)
  else:
    await manager.send_message_to_client_id(message=message, client_id=token)
  return message

def ask_to_llm_stream(setting: ReposSettingEntity, chatMesg: ChatMesgEntity, question: str, userId: str, chatHistory: list[ChatMesgEntity] = None):
  chatHistory = chatHistory or []
  fallback_message = '很抱歉，似乎发生了错误'
  client = None
  try:
    client = get_user_llm_client(userId=userId, temperature=setting.llmTptur)
  except Exception as e:
    logger.error(e)
    yield message_error_to_json(str(e))
    yield message_chunk_to_json(fallback_message)
    persist_chat_message(chatMesg, fallback_message)
    return fallback_message
  if (len(chatHistory) > 0):
    chatHistory = chatHistory[:setting.maxHist]
  prompts, sources = None, None
  try:
    prompts, sources = get_question_prompts_and_sources(chatMesg.reposId, question, setting, chatHistory)
  except Exception as e:
    logger.error(e)
    yield message_error_to_json(str(e))
    yield message_chunk_to_json(fallback_message)
    persist_chat_message(chatMesg, fallback_message)
    return fallback_message
  message = ''
  if (prompts is None):
    message = '很抱歉，无法回答该问题'
    yield message_chunk_to_json(message)
  else:
    try:
      for chunk in client.stream(prompts):
        if (type(chunk) != str):
          chunk = chunk.content
        yield message_chunk_to_json(chunk)
        message = message + chunk
    except Exception as e:
      logger.error(e)
      yield message_error_to_json(str(e))
      message = fallback_message
      yield message_chunk_to_json(message)
  sources = sources or []
  save_message_quotes(chatMesg=chatMesg, sources=sources)
  yield message_quote_to_json(mesgId=chatMesg.mesgId, chatId=chatMesg.chatId, reposId=chatMesg.reposId, quotes=sources)
  persist_chat_message(chatMesg, message)
  return message
