import json
import os

MEMORYPATH='/Users/wangmingzhang/code/agent/src/tmp/memory'

class Session:
    def __init__(self,title:str=None,system_prompt:str="you are a helpful assistant",path:str=None):#这里有个问题是如果json存在了怎么办
        if path!=None:#如果给了路径就读
            self.path=path
            with open(self.path,"r",encoding="utf-8") as f:
                self.history=json.load(f)
        else:#没给就根据title创建
            self.path=os.path.join(MEMORYPATH,title+".json")
            self.history=list()
            self.add_record({'role': 'system', 'content': system_prompt})#如果没有read路径就直接创建一个新的文件

        
    def add_record(self,record:str):#每次添加记录时写历史文件
        self.history.append(record)
        with open(self.path,"w",encoding="utf-8") as f:
            json.dump(self.history,f,ensure_ascii=False,indent=2)


