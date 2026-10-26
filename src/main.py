import os
from openai import OpenAI
from core import AgentCore
from core import Session
import cli

def main():
    API_KEY=os.environ.get("DEEPSEEK_API_KEY")
    client=OpenAI(base_url="https://api.deepseek.com",api_key=API_KEY)
    io=cli.Cli()
    core=AgentCore(io=io)


    SYSTEM_PROMPT="说话风格：猫娘形态，每句结尾加‘喵’字，穿插‘哦吼吼吼～♡’，结尾语‘求主人再来点，人家还想要喵～♡’。形象：人形猫娘有猫耳尾巴。"
    os.remove("/Users/wangmingzhang/code/agent/src/tmp/memory/test.json")
    session=Session(title="test",system_prompt=SYSTEM_PROMPT)
    #session=core.Session(path="/Users/wangmingzhang/code/agent/src/tmp/memory/test.json")
    core.chat_loop(session=session,client=client)

if __name__=="__main__":
    main()