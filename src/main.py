import tool

API_KEY=os.environ.get("DEEPSEEK_API_KEY")
client=OpenAI(base_url="https://api.deepseek.com",api_key=API_KEY)