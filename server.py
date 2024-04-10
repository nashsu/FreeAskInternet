# -*- coding: utf-8 -*-

import time
import uvicorn
import sys
import getopt
import json
import os 
from pprint import pprint
import requests
import trafilatura
from trafilatura import bare_extraction
from concurrent.futures import ThreadPoolExecutor
import concurrent
import requests
import openai
import time 
from datetime import datetime
from urllib.parse import urlparse
import platform
import urllib.parse
import free_ask_internet
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Literal, Optional, Union
from sse_starlette.sse import ServerSentEvent, EventSourceResponse
from fastapi.responses import StreamingResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ModelCard(BaseModel):
    id: str
    object: str = "model"
    created: int = Field(default_factory=lambda: int(time.time()))
    owned_by: str = "owner"
    root: Optional[str] = None
    parent: Optional[str] = None
    permission: Optional[list] = None


class ModelList(BaseModel):
    object: str = "list"
    data: List[ModelCard] = []


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class DeltaMessage(BaseModel):
    role: Optional[Literal["user", "assistant", "system"]] = None
    content: Optional[str] = None


class QueryRequest(BaseModel):
    query:str
    model: str
    ask_type:  Literal["search", "llm"]
    llm_auth_token: Optional[str] = "CUSTOM"
    llm_base_url: Optional[str] = ""
    using_custom_llm:Optional[bool] = False
    lang:Optional[str] = "zh-CN"

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_length: Optional[int] = None
    stream: Optional[bool] = False


class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Literal["stop", "length"]


class ChatCompletionResponseStreamChoice(BaseModel):
    index: int
    delta: DeltaMessage
    finish_reason: Optional[Literal["stop", "length"]]


class ChatCompletionResponse(BaseModel):
    model: str
    object: Literal["chat.completion", "chat.completion.chunk"]
    choices: List[Union[ChatCompletionResponseChoice,
                        ChatCompletionResponseStreamChoice]]
    created: Optional[int] = Field(default_factory=lambda: int(time.time()))

class SearchItem(BaseModel):
    url: str
    icon_url: str
    site_name:str
    snippet:str
    title:str 

class SearchItemList(BaseModel):
    search_items: List[SearchItem] = []
 
class SearchResp(BaseModel):
    code:int
    msg:str
    data: List[SearchItem] = []
 

@app.get("/v1/models", response_model=ModelList)
async def list_models():
    global model_args
    model_card = ModelCard(id="gpt-3.5-turbo")
    return ModelList(data=[model_card])


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(request: ChatCompletionRequest):
    global model, tokenizer
    print(request)
    if request.messages[-1].role != "user":
        raise HTTPException(status_code=400, detail="Invalid request")
    query = request.messages[-1].content


    generate = predict(query, "", request.model)
    return EventSourceResponse(generate, media_type="text/event-stream")

 

def predict(query: str, history: None, model_id: str):
    choice_data = ChatCompletionResponseStreamChoice(
        index=0,
        delta=DeltaMessage(role="assistant"),
        finish_reason=None
    )
    chunk = ChatCompletionResponse(model=model_id, choices=[
                                choice_data], object="chat.completion.chunk")
    yield "{}".format(chunk.json(exclude_unset=True))
    new_response = ""
    current_length = 0
    for token in free_ask_internet.ask_internet(query=query):
    
        new_response += token
        if len(new_response) == current_length:
            continue

        new_text = new_response[current_length:]
        current_length = len(new_response)

        choice_data = ChatCompletionResponseStreamChoice(
            index=0,
            delta=DeltaMessage(content=new_text,role="assistant"),
            finish_reason=None
        )
        chunk = ChatCompletionResponse(model=model_id, choices=[
                                       choice_data], object="chat.completion.chunk")
        yield "{}".format(chunk.json(exclude_unset=True))

    choice_data = ChatCompletionResponseStreamChoice(
        index=0,
        delta=DeltaMessage(),
        finish_reason="stop"
    )
    chunk = ChatCompletionResponse(model=model_id, choices=[
                                   choice_data], object="chat.completion.chunk")
    yield "{}".format(chunk.json(exclude_unset=True))
    yield '[DONE]'
 


@app.post("/api/search/get_search_refs", response_model=SearchResp)
async def get_search_refs(request: QueryRequest):

    global search_results
    search_results = []
    search_item_list = []
    if request.ask_type == "search":
        search_links,search_results = free_ask_internet.search_web_ref(request.query)
        for search_item in search_links:
            snippet = search_item.get("snippet")
            url = search_item.get("url")
            icon_url = search_item.get("icon_url")
            site_name = search_item.get("site_name")
            title = search_item.get("title")
    

            si = SearchItem(snippet=snippet,url=url,icon_url=icon_url,site_name=site_name,title=title)

            search_item_list.append(si)

    resp = SearchResp(code=0,msg="success",data=search_item_list)
   
    return  resp

def generator(prompt:str, model:str, llm_auth_token:str,llm_base_url:str, using_custom_llm=False,is_failed=False):
    if is_failed:
        yield "搜索失败，没有返回结果"
    else:
        total_token = ""
        for token in  free_ask_internet.chat(prompt=prompt,model=model,llm_auth_token=llm_auth_token,llm_base_url=llm_base_url,using_custom_llm=using_custom_llm,stream=True):
            total_token += token
            yield token
 
@app.post("/api/search/stream/{search_uuid}")
async def stream(search_uuid:str,request: QueryRequest):
    global search_results

    if request.ask_type == "llm":
            
        answer_language = ' Simplified Chinese '
        if request.lang == "zh-CN":
            answer_language = ' Simplified Chinese '
        if request.lang == "zh-TW":
            answer_language = ' Traditional Chinese '
        if request.lang == "en-US":
            answer_language = ' English '
        prompt = ' You are a large language AI assistant develop by nash_su. Answer user question in ' + answer_language + '. And here is the user question: ' + request.query
        generate = generator(prompt,model=request.model,llm_auth_token=request.llm_auth_token, llm_base_url=request.llm_base_url, using_custom_llm=request.using_custom_llm)
    else:
        prompt = None
        limit_count = 10

        while limit_count > 0:
            try:
                if len(search_results) > 0:
                    prompt = free_ask_internet.gen_prompt(request.query,search_results,lang=request.lang,context_length_limit=8000)
                    break
                else:
                    limit_count -= 1
                    time.sleep(1)
            except Exception as err:
                limit_count -= 1
                time.sleep(1)
        total_token =  ""
        if prompt:   
            generate = generator(prompt,model=request.model,llm_auth_token=request.llm_auth_token, llm_base_url=request.llm_base_url, using_custom_llm=request.using_custom_llm)
        else:
            generate = generator(prompt,model=request.model,llm_auth_token=request.llm_auth_token,llm_base_url=request.llm_base_url, using_custom_llm=request.using_custom_llm,is_failed=True)

    # return EventSourceResponse(generate, media_type="text/event-stream")
    return StreamingResponse(generate, media_type="text/event-stream")

def main():

    port = 8000

    search_results = []
 
   
    uvicorn.run(app, host='0.0.0.0', port=port, workers=1)


if __name__ == "__main__":
    main()
