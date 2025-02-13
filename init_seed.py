from openai_client import get_openai_client
import json
import os

def load_services():
    with open('config/services_list.json', 'r', encoding='utf-8') as file:
        return json.load(file)

def generate_incidents():
    services_list = load_services()
    services_list_str = json.dumps(services_list, ensure_ascii=False)

    prompt = f"""
    你是一名经验丰富的 SRE。列出 10 个可能的生产事故，这些事故需要根本原因分析。
    每个事故应以一句话描述，并涵盖系统操作的不同方面（例如，性能、可用性、可靠性）。
    重点关注 DevOps 团队经常遇到的现实场景。

    ### 可选的业务系统列表 ###
    {services_list_str}

    请务必按照 JSON 格式输出结果，JSON 内容包括 category, label, question, reason 四个属性。
    """

    client = get_openai_client()
    response = client.chat.completions.create(
        model="qwen-max-2025-01-25",
        messages=[
            {'role': 'user', 'content': prompt}
        ],
        response_format={"type": "json_object"},
    )
    
    incidents = json.loads(response.choices[0].message.content.strip())

    if isinstance(incidents, list):
        return incidents
    elif isinstance(incidents, dict) and 'incidents' in incidents:
        return incidents['incidents']
    else:
        raise ValueError(f"Unexpected response format. Raw response: {response.choices[0].message.content}")


if __name__ == '__main__':
    incidents = generate_incidents()
    print(json.dumps(incidents, indent=2, ensure_ascii=False))

