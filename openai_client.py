from openai import OpenAI
import os
from dotenv import load_dotenv

def get_openai_client():
    load_dotenv()  # 加载 .env 文件
    return OpenAI(
        api_key=os.getenv('OPENAI_API_KEY'),
        base_url=os.getenv('OPENAI_BASE_URL')
    )
