import json
import os
from openai import OpenAI
from ddgs import DDGS
import requests
import subprocess

#MEMORYPATH='/Users/wangmingzhang/code/agent/src/tmp/memory'
API_KEY=os.environ.get("DEEPSEEK_API_KEY")#这个只有web搜索还在用，后面优化掉
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
                "count":{
                    "type": "integer",
                    "description": "The number of results to return, between 1 and 50.",
                    "default": 10
                },
                "need_content":{
                    "type":"boolean",
                    "description":"Whether to return page content in content, which is always an empty string when false.",
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
    },
    {
        "type":"function",
        "name":"run_bash",
        "description":"Execute a bash command inside an isolated sandbox and return its exit code, stdout, and stderr. Use this tool to inspect files, search code, run tests, build projects, or install dependencies. Commands are limited to a single working directory, cannot access the network, and are terminated after reaching the timeout. Prefer read-only commands; never run destructive commands such as rm -rf, mkfs, reboot, or anything requiring sudo.",
        "parameters":{
            "type":"object",
            "properties":{
                "command":{
                    "type":"string",
                    "description":"The bash command to execute, for example: ls -la or pytest -q tests/"
                },
                "timeout_ms":{
                    "type": "integer",
                    "description": "Maximum execution time in milliseconds before the process is killed. Defaults to 30000, maximum 120000.",
                    "default":30000
                },
                "workdir": {
                    "type": "string",
                    "description": "Working directory for the command, relative to the sandbox root.",
                    "default": "."
                }
            },
            "required": ["command"]
        }
    }
]

class Session:
    def __init__(self,title:str=None,system_prompt:str="you are a helpful assistant",memory_path='/Users/wangmingzhang/code/agent/src/tmp/memory'):#这里有个问题是如果json存在了怎么办
        #如果path存在则读取，否则保存
        self.title=title
        self.path=os.path.join(memory_path,title+".json")
        if os.path.exists(self.path):#如果给了路径就读
            with open(self.path,"r",encoding="utf-8") as f:
                self.history=json.load(f)
        else:#没给就根据title创建
            self.history=list()
            self.add_record({'role': 'system', 'content': system_prompt})#如果没有read路径就直接创建一个新的文件

        
    def add_record(self,record:str):#每次添加记录时写历史文件
        self.history.append(record)
        with open(self.path,"w",encoding="utf-8") as f:
            json.dump(self.history,f,ensure_ascii=False,indent=2)


class AgentCore:#一个agent应用需要规定client和io方式，可以切换session
    def __init__(self,io):
        #self.client=client这里做一个待定，client到底是参数还是属性
        self.io=io

    def run_bash(self,command:str,timeout_ms:int=30000,workdir:str=".")->str:
        print(f"bash permission request:\n{command}")#这里待完成
        user_input=None
        while(user_input!="Yes" and user_input!="No"):
            user_input=input("Yes or No:")
        if user_input=="No":
            return json.dumps({"error": "run_bash permission rejected by user"})
        else:
            try:
                p=subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,#经过 /bin/sh，支持 | && > 等语法
                    text=True,#输出解码成 str（不是 bytes）
                    timeout=timeout_ms/1000,
                    cwd="/Users/wangmingzhang/code/agent",
                    stdin=subprocess.DEVNULL,#stdin 接黑洞，防交互卡死
                )
                return json.dumps({
                    "exit_code":p.returncode,
                    "stdout":p.stdout[-4000:],
                    "stderr":p.stderr[-2000:],
                },ensure_ascii=False)#原样保留中文，不然会转成`\uXXXX` 转义序列
            except subprocess.TimeoutExpired:
                return json.dumps({"error":"timeout"})
            except Exception as e:
                return json.dumps({"error":str(e)})
        


    def web_search(self,query:str,count:int=10,need_content:bool=False)->str:
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
        return f"{page.get("title","")}\n{page.get("content","")}"




    def agent_loop(self,items,client,session):#这里是agent的loop，自动调用工具，返回一个结果
        while(len(items)):
            for item in items:
                if item.name=="run_bash":
                    arg=json.loads(item.arguments)  
                    result=self.run_bash(arg.get("command"),arg.get("timeout_ms",30000),arg.get("workdir","."))
                    session.add_record(
                        {
                            "type":"function_call_output",
                            "call_id":item.call_id,
                            "output":result
                        }
                    )
                if item.name=="web_fetch":
                    arg=json.loads(item.arguments)  
                    result=self.web_fetch(arg.get("url"))
                    session.add_record(
                        {
                            "type":"function_call_output",
                            "call_id":item.call_id,
                            "output":result
                        }
                    )
                if item.name=="web_search":
                    #breakpoint()
                    arg=json.loads(item.arguments)
                    result=self.web_search(arg.get("query"),arg.get("count",10),need_content=arg.get("need_content", False))#这里用get好，没有可以设置default
                    session.add_record(
                        {
                            "type":"function_call_output",
                            "call_id":item.call_id,
                            "output":result
                        }
                    )
                #breakpoint()
            response=client.responses.create(
                model="deepseek-flash",
                input=session.history,
                tools=tools
            )
            message,reasoning,function_call=self.apply_response(response,session)
            items=function_call
        return response
            

    def apply_response(self,response,session):
        #breakpoint()
        reasoning=None
        function_call=list()
        message=None
        for item in response.output:#把response里面的思维链或者答案加入列表
            if item.type=="message":
                self.io.show_answer(response.output_text)#这一步很关键
                message=item
            elif item.type=="reasoning":
                reasoning=item
            elif item.type=="function_call":
                function_call.append(item)
            session.add_record(item.model_dump())
        return message,reasoning,function_call

    def chat_loop(self,client,session):
        #breakpoint()
        while True:
            user_input=self.io.read_prompt("你:")
            response=self.run_turn(client,session,user_input)
            assert response!=None
            #print(response==None)

        
    def run_turn(self,client,session,user_input):
        #breakpoint()
        session.add_record({"role":"user","content":user_input})
        response=client.responses.create(
            model="deepseek-flash",
            input=session.history,
            tools=tools
        )
        message,reasoning,function_call=self.apply_response(response,session)
        if len(function_call):
            response=self.agent_loop(function_call,client,session)#用agent_loop的最终答案替代
        return response

        
