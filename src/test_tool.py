from tool import run_turn 
import tool

class ResponseItem:
    def __init__(self,type):
        self.type=type
    def model_dump(self):
        return "1"

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

def make_fake_response_no_tool():
    output=[ResponseItem("message")]
    return FakeResponse(output,"你好")


def test_run_turn_no_tool():#测试run_turn没有工具的一次调用
    tmp_input_list=tool.input_list
    tool.input_list=list()
  
    gt_output=[ResponseItem("message")]
    gt_output_text="hello"
    gt_response=FakeResponse(gt_output,gt_output_text)
    #breakpoint()
    fake_responses=FakeResponses(gt_response)
    fake_client=FakeClient(fake_responses)
    client=fake_client

    user_input="你好"

    out_response=run_turn(client,user_input)
    #breakpoint()
    assert (len(tool.input_list)-len(tmp_input_list))==1,"历史记录添加错误"
    tool.input_list=tmp_input_list
    assert out_response==gt_response,"run_turn 输出错误"
    assert fake_client.responses.call_create_counts==1,"run_turn直接回答大模型调用次数不为1"
    print("test_run_turn_no_tool passed")


test_run_turn_no_tool()