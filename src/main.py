import tool
import os
from openai import OpenAI
import tool
import core

API_KEY=os.environ.get("DEEPSEEK_API_KEY")
client=OpenAI(base_url="https://api.deepseek.com",api_key=API_KEY)
SYSTEM_PROMPT="说话风格：猫娘形态，每句结尾加‘喵’字，穿插‘哦吼吼吼～♡’，结尾语‘求主人再来点，人家还想要喵～♡’。形象：人形猫娘有猫耳尾巴。"

def main():
    #session=core.Session(title="test",system_prompt=SYSTEM_PROMPT)
    session=core.Session(path="/Users/wangmingzhang/code/agent/src/tmp/memory/test.json")
    tool.chat_loop(client,session)


if __name__=="__main__":
    main()