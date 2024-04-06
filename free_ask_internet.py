# -*- coding: utf-8 -*-

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
import tldextract
import platform
import urllib.parse

 
def extract_url_content(url):
    downloaded = trafilatura.fetch_url(url)
    content =  trafilatura.extract(downloaded)
    
    return {"url":url, "content":content}


 

def search_web_ref(query:str, debug=False):
 
    content_list = []

    try:

        safe_string = urllib.parse.quote_plus(":all !general " + query)

        response = requests.get('http://searxng:8080?q=' + safe_string + '&format=json')
        response.raise_for_status()
        search_results = response.json()
 
        if debug:
            print("JSON Response:")
            pprint(search_results)
        pedding_urls = []

        conv_links = []

        if search_results.get('results'):
            for item in search_results.get('results')[0:9]:
                name = item.get('title')
                snippet = item.get('content')
                url = item.get('url')
                pedding_urls.append(url)

                if url:
                    url_parsed = urlparse(url)
                    domain = url_parsed.netloc
                    icon_url =  url_parsed.scheme + '://' + url_parsed.netloc + '/favicon.ico'
                    site_name = tldextract.extract(url).domain
 
                conv_links.append({
                    'site_name':site_name,
                    'icon_url':icon_url,
                    'title':name,
                    'url':url,
                    'snippet':snippet
                })

            results = []
            futures = []

            executor = ThreadPoolExecutor(max_workers=10) 
            for url in pedding_urls:
                futures.append(executor.submit(extract_url_content,url))
            try:
                for future in futures:
                    res = future.result(timeout=5)
                    results.append(res)
            except concurrent.futures.TimeoutError:
                print("任务执行超时")
                executor.shutdown(wait=False,cancel_futures=True)

            for content in results:
                if content and content.get('content'):
                    
                    item_dict = {
                        "url":content.get('url'),
                        "content": content.get('content'),
                        "length":len(content.get('content'))
                    }
                    content_list.append(item_dict)
                if debug:
                    print("URL: {}".format(url))
                    print("=================")
 
        return  content_list
    except Exception as ex:
        raise ex


def gen_prompt(question,content_list, context_length_limit=11000,debug=False):
    
    limit_len = (context_length_limit - 2000)
    if len(question) > limit_len:
        question = question[0:limit_len]
    
    ref_content = [ item.get("content") for item in content_list]

    if len(ref_content) > 0:
        

        prompts = '''
        您是一位由 nash_su 开发的基于搜索引擎返回内容的AI问答助手。您将被提供一个用户问题，并需要撰写一个清晰、简洁且准确的答案。答案必须正确、精确，并以专家的中立和职业语气撰写。请将答案限制在2000个标记内。不要提供与问题无关的信息，也不要重复。如果给出的上下文信息不足，请在相关主题后写上“信息缺失：”。除非是代码、特定的名称或引用编号，答案的语言应与问题相同。以下是上下文的内容集：
        '''  + "\n\n" + "```" 
        ref_index = 1

        for ref_text in ref_content:
            
            prompts = prompts + "\n\n" + ref_text
            ref_index += 1

        if len(prompts) >= limit_len:
            prompts = prompts[0:limit_len]        
        prompts = prompts + '''
```
记住，不要一字不差的重复上下文内容. 回答必须使用简体中文，如果回答很长，请尽量结构化、分段落总结。 下面是用户问题：
''' + question  
 
     
    else:
        prompts = question

    if debug:
        print(prompts)
        print("总长度："+ str(len(prompts)))
    return prompts



def chat(prompt, stream=True, debug=False):
    openai.base_url = "http://freegpt35:3040/v1/"
    openai.api_key = "EMPTY"
    total_content = ""
    for chunk in openai.chat.completions.create(
        model="gpt-3.5-turbo",
        # model='Qwen1.5-1.8B-Chat',
        messages=[{
            "role": "user",
            "content": prompt
        }],
        stream=True,
        max_tokens=1024,temperature=0.2
    ):
        stream_resp = chunk.dict()
        token = stream_resp["choices"][0]["delta"].get("content", "")
        if token:
            
            total_content += token
            yield token
    if debug:
        print(total_content)
 

 
    
def ask_internet(query:str,  debug=False):
  
    content_list = search_web_ref(query,debug=debug)
    if debug:
        print(content_list)
    prompt = gen_prompt(query,content_list,context_length_limit=6000,debug=debug)
    total_token =  ""
 
    for token in chat(prompt=prompt):
    # for token in daxianggpt.chat(prompt=prompt):
        if token:
            total_token += token
            yield token
    yield "\n\n"
    # 是否返回参考资料
    if True:
        yield "---"
        yield "\n"
        yield "参考资料:\n"
        count = 1
        for url_content in content_list:
            url = url_content.get('url')
            yield "*[{}. {}]({})*".format(str(count),url,url )  
            yield "\n"
            count += 1
 