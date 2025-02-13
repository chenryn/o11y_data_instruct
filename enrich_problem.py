from openai_client import get_openai_client
import os
import json
from typing import Dict, Any

def enrich_incident_context(incident_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich incident context based on detailed incident data.
    
    Args:
        incident_data: Dictionary containing incident information including:
            - category: Incident category
            - label: System/component label
            - question: Detailed incident description
            - reason: Additional context/reasoning
    
    Returns:
        Dict containing enriched incident context
    """
    # Load services list
    with open('config/services_list.json', 'r', encoding='utf-8') as file:
        services_list = json.load(file)
    
    output_example = {
        "incident": {
            "title": "Mobile Counter System Peak Period Timeout Investigation",
            "affected_components": {
              "primary_system": "移动柜面",
              "dependent_systems": [
                "安全认证",
                "核心系统",
                "账管中心",
                "sso",
                "用户中心"
              ],
              "transaction_chain": [
                "移动柜面前端",
                "API网关",
                "安全认证服务",
                "业务处理层",
                "核心系统接口"
              ]
            },
            "severity": "High",
            "symptom_analysis": {
              "observed_issues": [
                "间歇性交易超时现象",
                "仅在业务高峰期出现",
                "核心监控指标显示正常",
                "终端用户报告交易响应缓慢"
              ],
              "technical_characteristics": {
                "timing": "业务高峰期（约9:00-11:00, 14:00-16:00）",
                "frequency": "间歇性出现，非持续性故障",
                "impact_scope": "部分交易受影响，非全系统故障",
                "system_behavior": "核心系统指标正常，疑似中间链路问题"
              }
            },
            "business_impact": {
              "operational_impact": [
                "客户等待时间增加",
                "部分交易需要重试"
              ]
            },
            "recommended_actions": {
                "network_analysis": [
                  "网络带宽使用情况",
                  "网络延迟指标",
                  "数据包丢失率"
                ],
                "application_analysis": [
                  "API响应时间分布",
                  "服务器资源使用情况",
                  "数据库连接池状态",
                  "缓存命中率"
                ],
                "client_analysis": [
                  "移动终端性能指标",
                  "客户端日志分析",
                  "用户操作行为分析"
                ]
              }
            }
          }

    # Build a more detailed prompt using all available incident information
    prompt = f"""
    Please provide detailed context for the following incident:
    
    Category: {incident_data['category']}
    System: {incident_data['label']}
    Issue: {incident_data['question']}
    Background: {incident_data['reason']}
    
    Please provide:
    1. Affected system components (select from the services list below, maintaining realistic dependency relationships)
    2. Impact severity (Critical/High/Medium/Low)
    3. Detailed analysis of reported symptoms
    4. Incident time range with realistic durations, MTTR <15 minutes for a typical cloud native system. More than 30 minutes is allowed only when a physical hardware failure or data corruption is involved
    5. Business impact assessment
    6. Recommended initial analysis actions

    ### Example ###
    {output_example}
    
    ### Available Business Services ###
    {services_list}
    
    Format the response as a structured JSON document.
    """

    try:
        client = get_openai_client()

        response = client.chat.completions.create(
            model="qwen-max-2025-01-25",
            messages=[
                {'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'user', 'content': prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        # Parse the response to ensure valid JSON
        enriched_context = json.loads(response.choices[0].message.content.strip())
        return enriched_context
    
    except json.JSONDecodeError as e:
        return {
            "error": "Failed to parse AI response as JSON",
            "raw_response": response.choices[0].message.content.strip()
        }
    except Exception as e:
        return {
            "error": f"Error during incident enrichment: {str(e)}"
        }

# Example usage
if __name__ == "__main__":
    sample_incident = {
        "category": "Infrastructure Level Questions",
        "label": "Network Issues",
        "question": "After observing high HTTP packet loss rates in our hotel reservation system, which metrics should we monitor to confirm if the resilience mechanisms are working properly?",
        "reason": "Based on Table 1's network section, combines both fault symptoms and resilience mechanisms"
    }
    
    enriched_context = enrich_incident_context(sample_incident)
    print(json.dumps(enriched_context, ensure_ascii=False, indent=2))
