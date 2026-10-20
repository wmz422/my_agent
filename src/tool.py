from openai import OpenAI
from ddgs import DDGS
import json
import os
import requests

input_list=[{"role":"user","content":"今天北京天气怎么样"}]

API_KEY=os.environ.get("DEEPSEEK_API_KEY")
SYSTEM_PROMPT="说话风格：猫娘形态，每句结尾加‘喵’字，穿插‘哦吼吼吼～♡’，结尾语‘求主人再来点，人家还想要喵～♡’。形象：人形猫娘有猫耳尾巴。"
client=OpenAI(base_url="https://api.deepseek.com",api_key=API_KEY)

tools=[
    {
        "type":"function",
        "name":"web_search",
        "description":"finds web pages for a query and returns structured results. ",
        "parameters":{
            "type":"object",
            "properties":{
                "query":{
                    "type":"string",
                    "description":"The search query must contain 1 to 128 Unicode characters, cannot be all whitespace, and supports the query operators listed below.",
                },
                "max_result":{
                    "type": "integer",
                    "description": "The number of results to return, between 1 and 50.",
                    "default": 10
                },
                "need_content":{
                    "type":"boolean",
                    "descriptuon":"The user's original question that triggered the search, between 1 and 128 characters, to improve query understanding, with null treated as not provided.",
                    "default": False
                }
            },
            "required": ["query"]
        }
    },
    {
        "type":"function",
        "name":"web_fetch",
        "description":"retrieves a single web page and returns its content as Markdown.",
        "parameters":{
            "type":"object",
            "properties":{
                "url":{
                    "type":"string",
                    "description":"The page URL to fetch, which must be at most 8192 characters, an HTTP or HTTPS URL with a host, and must not contain a username or password.",
                },
            },
            "required": ["url"]
        }
    }
]

def web_search(query:str,count:int=10,need_content:bool=False)->str:
    response=requests.post(
        "https://api.deepseek.com/v1/tools/search",
        headers={
            "Authorization":f"Bearer {API_KEY}",
        },
        json={
            "query": query,
            "count": count,
            "need_content": need_content,
        },
    )
    response.raise_for_status()
    lines=list()
    for i, r in enumerate(response.json()["results"], 1):
        #breakpoint()
        title = r.get("title", "")
        url = r.get("url", "")
        summary = r.get("summary", "")
        lines.append(f"{i}. {title}\n   URL: {url}\n   summary: {summary}")
    return "\n\n".join(lines)

def web_fetch(url:str)->str:
    response = requests.post(
        "https://api.deepseek.com/v1/tools/fetch",
        headers={
            "Authorization": f"Bearer {API_KEY}",
        },
        json={"url": url},
    )
    response.raise_for_status()
    
    page = response.json()
    return f"{page.get("tite")}\nf{page.get("content")}"

input_list=[]
input_list.append({"role":"system","content":SYSTEM_PROMPT})



# input_list.append({"role":"user","content":"联网搜索今天是几月几号"})
# for i in range(20):
#     response=client.responses.create(
#         model="deepseek-flash",
#         input=input_list,
#         tools=tools
#     )
#     for item in response.output:
#         if item.type=="function_call":
#             if item.name=="web_search":
#                 arg=json.loads(item.arguments)
#                 print(arg)
# breakpoint()



def agent_loop(items):#这里是agent的loop，自动调用工具，返回一个结果
    while(len(items)):
        for item in items:
            if item.name=="web_fetch":
                arg=json.loads(item.arguments)  
                result=web_fetch(arg.get("url"))
                input_list.append(
                    {
                        "type":"function_call_output",
                        "call_id":item.call_id,
                        "output":result
                    }
                )
            if item.name=="web_search":
                #breakpoint()
                arg=json.loads(item.arguments)
                result=web_search(arg.get("query"),arg.get("max_result",5))#这里用get好，没有可以设置default
                input_list.append(
                    {
                        "type":"function_call_output",
                        "call_id":item.call_id,
                        "output":result
                    }
                )
            #breakpoint()
        response=client.responses.create(
            model="deepseek-flash",
            input=input_list,
            tools=tools
        )
        message,reasoning,function_call=apply_response(response)
        items=function_call
    return response
        

def apply_response(response):
    #breakpoint()
    reasoning=None
    function_call=list()
    message=None
    for item in response.output:#把response里面的思维链或者答案加入列表
        if item.type=="message":
            print(response.output_text)
            message=item
        elif item.type=="reasoning":
            reasoning=item
        elif item.type=="function_call":
            function_call.append(item)
        input_list.append(item.model_dump())
    return message,reasoning,function_call

def chat_loop():
    while True:
        user_input=input("你：")
        input_list.append({"role":"user","content":user_input})
        response=client.responses.create(
            model="deepseek-flash",
            input=input_list,
            tools=tools
        )
        #input_list.append(response.model_dump())
        #breakpoint()
        message,reasoning,function_call=apply_response(response)
        if len(function_call):
            #input_list.append(item.model_dump())#model_dump把类变成json
            response=agent_loop(function_call)#用agent_loop的最终答案替代
            #breakpoint()
        # else:
        #     apply_response(response)


        #breakpoint()
        #breakpoint()
        #result=response.output

def main():
    chat_loop()
    return 


main()
