from openai_client import get_openai_client
import json
import os
import glob
import re

def load_services():
    with open('config/services_list.json', 'r', encoding='utf-8') as file:
        return json.load(file)

def load_postmortem_files():
    """加载postmortem目录下的所有markdown文件"""
    postmortem_files = glob.glob('config/postmortem/*.md')
    # 排除README.md文件
    return [file for file in postmortem_files if not file.endswith('README.md')]

def generate_incidents_from_services():
    """从服务列表生成事故数据"""
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

def extract_postmortem_content(file_path):
    """从postmortem文档中提取内容
    
    由于postmortem文件格式多样，不再尝试解析特定章节，而是直接返回整个文件内容。
    如果文件内容超过LLM上下文长度限制（如32k），则会将内容分成多个批次返回，而不是简单截断。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
    except UnicodeDecodeError:
        # 尝试使用其他编码打开文件
        with open(file_path, 'r', encoding='latin-1') as file:
            content = file.read()
    
    # 提取标题（如果有）
    title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
    if not title_match:
        title_match = re.search(r'^## (.+)$', content, re.MULTILINE)
    
    # 如果没有找到标题，使用文件名作为标题
    if title_match:
        title = title_match.group(1).strip()
    else:
        title = os.path.basename(file_path).replace('_', ' ').replace('.md', '')
    
    # 处理内容
    max_content_length = 30000  # 略小于32k，留出一些空间给其他内容
    
    # 如果内容长度超过限制，则分批处理
    if len(content) > max_content_length:
        # 将内容分成多个部分
        content_parts = []
        for i in range(0, len(content), max_content_length):
            part = content[i:i + max_content_length]
            part_num = i // max_content_length + 1
            total_parts = (len(content) + max_content_length - 1) // max_content_length
            content_parts.append({
                'part': part_num,
                'total_parts': total_parts,
                'content': part
            })
        
        return {
            'title': title,
            'content_parts': content_parts,
            'is_multipart': True
        }
    else:
        # 内容长度在限制范围内，直接返回
        return {
            'title': title,
            'content': content,
            'is_multipart': False
        }

def generate_incidents_from_postmortem(file_path):
    """从单个postmortem文档生成事故数据"""
    postmortem_content = extract_postmortem_content(file_path)
    
    # 处理多部分内容的情况
    if postmortem_content.get('is_multipart', False):
        # 构建包含多部分信息的提示
        title = postmortem_content['title']
        content_parts = postmortem_content['content_parts']
        total_parts = content_parts[0]['total_parts']
        
        # 构建提示，告知LLM这是一个分批处理的文档
        prompt = f"""
        你是一名经验丰富、擅长举一反三的 SRE。我将分{total_parts}批次提供一个故障复盘文档，请在阅读完整个文档后，列出10个类似的生产事故，这些事故需要根本原因分析。
        每个事故应以一句话描述，并涵盖系统操作的不同方面（例如，性能、可用性、可靠性）。
        重点关注 DevOps 团队经常遇到的现实场景。
        
        ### 故障复盘文档标题 ###
        {title}
        
        ### 故障复盘文档内容（第1批，共{total_parts}批） ###
        {content_parts[0]['content']}
        """
        
        # 创建初始消息
        messages = [{'role': 'user', 'content': prompt}]
        
        # 添加后续批次的内容
        for i in range(1, len(content_parts)):
            part = content_parts[i]
            part_prompt = f"""### 故障复盘文档内容（第{part['part']}批，共{part['total_parts']}批） ###
            {part['content']}
            
            请继续阅读，不要生成回复，直到你看到所有批次的内容。"""
            messages.append({'role': 'user', 'content': part_prompt})
        
        # 添加最终指令
        final_prompt = """
        现在你已经阅读了完整的故障复盘文档，请列出10个类似的生产事故，这些事故需要根本原因分析。
        请务必按照 JSON 格式输出结果，JSON 内容包括 category, label, question, reason 四个属性。
        """
        messages.append({'role': 'user', 'content': final_prompt})
    else:
        # 处理单部分内容的情况（原有逻辑）
        prompt = f"""
        你是一名经验丰富、擅长举一反三的 SRE。在阅读下面的故障复盘文档后，列出 10 个类似的生产事故，这些事故需要根本原因分析。
        每个事故应以一句话描述，并涵盖系统操作的不同方面（例如，性能、可用性、可靠性）。
        重点关注 DevOps 团队经常遇到的现实场景。
        
        ### 故障复盘文档 ###
        {json.dumps(postmortem_content, ensure_ascii=False)}
        
        请务必按照 JSON 格式输出结果，JSON 内容包括 category, label, question, reason 四个属性。
        """
        messages = [{'role': 'user', 'content': prompt}]
    
    client = get_openai_client()
    response = client.chat.completions.create(
        model="qwen-max-2025-01-25",
        messages=messages,
        response_format={"type": "json_object"},
    )
    
    incident = json.loads(response.choices[0].message.content.strip())
    return incident

def generate_incidents(source='services'):
    """生成事故数据
    
    参数:
        source (str): 数据源，可选值为 'services' 或 'postmortem'
    
    返回:
        list: 事故数据列表
    """
    if source == 'services':
        return generate_incidents_from_services()
    elif source == 'postmortem':
        postmortem_files = load_postmortem_files()
        if not postmortem_files:
            print("警告: 没有找到postmortem文档，将使用服务列表生成事故数据")
            return generate_incidents_from_services()
        
        incidents = []
        for file_path in postmortem_files:
            try:
                incident = generate_incidents_from_postmortem(file_path)
                incidents.append(incident)
                print(f"成功从 {file_path} 生成事故数据")
            except Exception as e:
                print(f"从 {file_path} 生成事故数据时出错: {str(e)}")
        
        return incidents
    else:
        raise ValueError(f"不支持的数据源: {source}，可选值为 'services' 或 'postmortem'")



if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='生成事故数据')
    parser.add_argument('--source', type=str, choices=['services', 'postmortem'], default='services',
                        help='数据源，可选值为 services（服务列表）或 postmortem（事后分析文档）')
    args = parser.parse_args()
    
    incidents = generate_incidents(source=args.source)
    print(json.dumps(incidents, indent=2, ensure_ascii=False))

