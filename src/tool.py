from openai import OpenAI
from ddgs import DDGS
import json
import os

input_list=[{"role":"user","content":"今天北京天气怎么样"}]

SYSTEM_PROMPT="说话风格：猫娘形态，每句结尾加‘喵’字，穿插‘哦吼吼吼～♡’，结尾语‘求主人再来点，人家还想要喵～♡’。形象：人形猫娘有猫耳尾巴。"
client=OpenAI(base_url="https://api.deepseek.com",api_key=os.environ.get("DEEPSEEK_API_KEY"))


tools=[
    {
        "type":"function",
        "name":"get_weather",
        "description":"Get today's weather",
        "parameters":{
            "type":"object",
            "properties":{},
            "require":[]
        }
    },
    {
        "type":"function",
        "name":"web_search",
        "description":"搜索互联网，返回相关网页的标题、链接和摘要。用于获取实时信息或训练数据之外的知识。",
        "parameters":{
            "type":"object",
            "properties":{
                "query":{
                    "type":"string",
                    "description":"搜索关键词"
                },
                "max_result":{
                    "type": "integer",
                    "description": "返回结果数量，默认 5",
                    "default": 5
                },
            },
            "required": ["query"]
        }
    }
]

def get_weather():
    return "Beijing 62°F. 58° Lo Clear 1% Wed 10/14 83° 61° Plenty of sunshine Night: Clear 0%"

def web_search(query:str,max_result:int=5)->str:
    try:
        results = DDGS().text(query, max_results=max_result)
        if not results:
            return f"没有找到关于「{query}」的结果。"

        lines = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "")
            href = r.get("href", "")
            body = r.get("body", "")
            lines.append(f"{i}. {title}\n   URL: {href}\n   摘要: {body}")
        return "\n\n".join(lines)
    except Exception as e:
        return f"搜索出错：{e}"

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
            if item.name=="get_weather":  
                result=get_weather()
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