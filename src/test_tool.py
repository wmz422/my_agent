from tool import run_turn 
import tool
import core
import main
from copy import deepcopy
import os
from core import Session

class ResponseItem:
    def __init__(self,type,gt_output_text):
        self.type=type
        self.gt_output_text=gt_output_text
    def model_dump(self):
        return self.gt_output_text

class FakeResponse:
    def __init__(self,output,output_text):
        self.output=output
        self.output_text=output_text

class FakeResponses:
    def __init__(self,gt_response):
        #breakpoint()
        self.call_create_counts=0
        self.gt_response=gt_response
    def create(self,model,input,tools):
        #breakpoint()
        self.call_create_counts+=1
        return self.gt_response

class FakeClient:
    def __init__(self,fake_responses):
        self.responses=fake_responses



def test_run_turn_no_tool():#测试run_turn没有工具的一次调用
    SYSTEM_PROMPT="you are a helpful assistant"
    session=core.Session(system_prompt=SYSTEM_PROMPT,title="test")
    or_session_history=deepcopy(session.history)
    try:

        gt_output_text="hello"
        gt_output=[ResponseItem("message",gt_output_text)]
        gt_response=FakeResponse(gt_output,gt_output_text)
        #breakpoint()
        fake_responses=FakeResponses(gt_response)
        fake_client=FakeClient(fake_responses)
        client=fake_client

        user_input="你好"
        out_response=run_turn(client=client,session=session,user_input=user_input)
        #breakpoint()

    #这里检验历史维护逻辑
        #breakpoint()
        assert (len(session.history)-len(or_session_history))==2,"历史记录添加数量错误"
        assert session.history[-1]==gt_output_text,"历史记录添加错误" #因为通过item.model_dump添加，fake实现简单没有实现标准字典
        assert session.history[-2]["content"]==user_input,"历史记录添加错误" #这里是tool里面实现的添加标准一个字典比较复杂

        #检验输出
        assert out_response==gt_response,"run_turn 输出错误"

        #检验大模型调用次数
        assert fake_client.responses.call_create_counts==1,"run_turn直接回答大模型调用次数不为1"
        print("test_run_turn_no_tool passed")

    finally:
        print("end of test")
        #tool.input_list=tmp_input_list#try里面可能会直接报错，可以用except截获错误，不管有没有被截获都会继续执行finnaly然后再继续传播

def test_session():
    #新建、保存、重新加载。
    try:
        test_memory_path='/Users/wangmingzhang/code/agent/src/tmp/memory/test'
        test_record={"role":"user","content":"hello"}
        session_1=Session(title="test_1",memory_path=test_memory_path)
        session_1.add_record(test_record)
        tmp_history=deepcopy(session_1.history)
        session_2=Session(title="test_1",memory_path=test_memory_path)
        assert session_2.history==tmp_history,"记录未添加"
    finally:
        os.remove(session_1.path)

    try:
        session_3=Session(title="test_3",memory_path=test_memory_path)
        session_4=Session(title="test_4",memory_path=test_memory_path)
        tmp_history=deepcopy(session_4.history)
        session_3.add_record(test_record)
        assert tmp_history==session_4.history,"会话不独立"
    finally:
        os.remove(session_3.path)
        os.remove(session_4.path)
    print("test passed")
        


if __name__=="__main__":
    test_session()
    #test_run_turn_no_tool()