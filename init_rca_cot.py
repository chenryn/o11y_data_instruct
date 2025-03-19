from openai_client import get_openai_client
from metric_agent import MetricAgent
from log_agent import LogAgent
import json
import os

def get_root_cause_analysis(enriched_incident, metrics_data, logs_data, events_data):
    """
    使用MetricAgent和LogAgent处理数据，然后进行根因分析
    
    Args:
        enriched_incident: 丰富的事件信息
        metrics_data: 原始指标数据
        logs_data: 日志数据
        events_data: 事件时间线数据
        
    Returns:
        根因分析结果
    """
    # 初始化MetricAgent并处理指标数据
    metric_agent = MetricAgent()
    compressed_metrics = metric_agent.extract_key_metrics(
        metrics_data, 
        enriched_incident
    )
    
    # 初始化LogAgent并处理日志数据
    log_agent = LogAgent()
    compressed_logs = log_agent.extract_key_logs(
        logs_data,
        enriched_incident
    )
    
    # 将压缩后的指标和日志数据转换为字符串表示
    compressed_metrics_str = json.dumps(compressed_metrics, ensure_ascii=False, indent=2)
    compressed_logs_str = json.dumps(compressed_logs, ensure_ascii=False, indent=2)

    prompt = f"""
Given the following observability data for incident "{enriched_incident}":
- Metrics Summary: {compressed_metrics_str}
- Logs Summary: {compressed_logs_str}
- Events: {events_data}

Please provide a comprehensive root cause analysis following these steps:

1. Impact Assessment
   - Determine if this is a systemic or isolated issue
   - Quantify affected users/services
   - Evaluate business impact severity
   - Define impact duration

2. Initial Symptom Analysis
   - Document observed anomalies
   - Identify primary error patterns
   - List affected components
   - Note any correlation with recent changes

3. Data Collection & Correlation
   - Analyze error logs and stack traces
   - Review monitoring metrics
   - Examine distributed traces
   - Correlate user feedback
   - Map system dependencies

4. Timeline Construction
   - Create incident timeline
   - Mark key events and changes
   - Identify potential trigger points
   - Note any pattern emergence

5. Pattern Recognition & Analysis
   - Identify anomaly patterns
   - Analyze performance bottlenecks
   - Map dependency relationships
   - Document system behavior changes

6. Hypothesis Formation
   - List potential root causes
   - Rank by probability
   - Document supporting evidence
   - Note conflicting indicators

7. Verification Steps
   - Define reproduction steps
   - Document test scenarios
   - List verification methods
   - Specify success criteria

8. Root Cause Confirmation
   - Present confirmed root cause
   - Provide supporting evidence
   - Document verification results
   - Address any uncertainty

9. Resolution Plan
   - Define immediate fixes
   - List long-term improvements
   - Specify validation steps
   - Include rollback plan

10. Prevention Measures
    - Recommend monitoring improvements
    - Suggest process changes
    - Define success metrics
    - Outline follow-up actions

Please follow this structure and provide detailed analysis for each section based on the available data.
"""

    client = get_openai_client()

    # 修改为流式输出方式
    response = client.chat.completions.create(
        model="qwq-plus",
        messages=[
            {'role': 'user', 'content': prompt}
        ],
        stream=True  # 启用流式输出
    )
    
    reasoning_content = ""  # 定义完整思考过程
    root_cause_analysis = ""  # 定义完整回复
    is_answering = False  # 判断是否结束思考过程并开始回复
    
    print("\n" + "=" * 20 + "思考过程" + "=" * 20 + "\n")
    
    for chunk in response:
        # 如果chunk.choices为空，则打印usage
        if not chunk.choices:
            if hasattr(chunk, 'usage'):
                print("\nUsage:")
                print(chunk.usage)
        else:
            delta = chunk.choices[0].delta
            # 打印思考过程
            if hasattr(delta, 'reasoning_content') and delta.reasoning_content is not None:
                print(delta.reasoning_content, end='', flush=True)
                reasoning_content += delta.reasoning_content
            else:
                # 开始回复
                if hasattr(delta, 'content') and delta.content and is_answering is False:
                    print("\n" + "=" * 20 + "完整回复" + "=" * 20 + "\n")
                    is_answering = True
                # 打印回复过程
                if hasattr(delta, 'content') and delta.content:
                    print(delta.content, end='', flush=True)
                    root_cause_analysis += delta.content
    
    print("\n")
    
    # 将思考过程和分析结果组织成JSON格式返回
    analysis_result = {
        "reasoning_process": reasoning_content,
        "analysis_result": root_cause_analysis
    }
    
    return analysis_result

# Example usage
if __name__ == "__main__":
    # 加载示例数据
    incident_id = "27b48495-7178-491d-a5eb-6b8312312b01"  # 示例ID
    base_dir = os.path.join("output", f"incident_{incident_id}")
    
    # 加载事件信息
    with open(os.path.join(base_dir, "incident.json"), "r", encoding="utf-8") as f:
        incident = json.load(f)
    
    # 加载指标数据
    with open(os.path.join(base_dir, "metrics.txt"), "r", encoding="utf-8") as f:
        metrics_data = f.read()
    
    # 加载日志数据
    with open(os.path.join(base_dir, "logs.txt"), "r", encoding="utf-8") as f:
        logs_data = f.read()
    
    # 加载事件时间线数据
    with open(os.path.join(base_dir, "events.json"), "r", encoding="utf-8") as f:
        events_data = json.load(f)
    
    # 执行根因分析
    analysis = get_root_cause_analysis_with_metric_agent(
        incident,
        metrics_data,
        logs_data,
        events_data
    )
    
    # 打印分析结果
    print(json.dumps(analysis, ensure_ascii=False, indent=2))
