from openai_client import get_openai_client
import json
import os

def load_metric_set():
    with open('config/metric_set.json', 'r', encoding='utf-8') as file:
        return json.load(file)

def design_abnormal_patterns(enriched_incident):
    # Load metric set
    metric_set = load_metric_set()

    # Convert the JSON object to a string representation for the prompt
    enriched_incident_str = json.dumps(enriched_incident, ensure_ascii=False)
    
    prompt = f"""
    For the incident ###enriched_incident_str###, design the abnormal patterns that would appear in relevant metrics. For each metric:
    1. Metric name and type (gauge/counter)
    2. Normal range and unit
    3. Dimensional labels (service/url/ip/pod, etc.)
    4. Statistical characteristics (seasonal/trend/frequency/noise)
    3. Abnormal pattern type (shake/upward spike/downward spike/continuous upward spike/continuous downward spike/upward convex/downward convex/"sudden increase/sudden decrease/rapid rise followed by slow decline/slow rise followed by rapid decline/rapid decline followed by slow rise/slow decline followed by rapid rise/decrease after upward spike/increase after downward spike/increase after upward spike/decrease after downward spike/wide upward spike/wide downward spike)
    4. Time frame when the issue occurred
    5. Correlation with other metrics
    6. Use any available metric definitions from the ###metric_set###; absence of a metric does not prevent proceeding without it.

    ### Output format example ###
    {{
      "metrics": [
        {{
          "metric_name": "指标名称",
          "type": "gauge或counter",
          "normal_range": "正常范围，如0-5%",
          "unit": "单位，如percentage/requests/milliseconds等",
          "dimensional_labels": "标签维度，如service=xxx,url=xxx格式",
          "statistical_characteristics": "统计特征描述",
          "abnormal_pattern_type": "异常模式类型",
          "time_frame": {{
            "start": "异常时段起始时间",
            "end": "异常时段结束时间"
          }},
          "correlation_with_other_metrics": "与其他指标的相关性描述"
        }}
      ]
    }}

    ### metric_set ###
    {metric_set}

    ### enriched_incident_str ###
    {enriched_incident_str}

    Format the response as a JSON schema that can be used to generate time series data.
    """
    
    client = get_openai_client()

    response = client.chat.completions.create(
        model="qwen-max-2025-01-25",
        messages=[
            {'role': 'system', 'content': 'You are a helpful assistant.'},
            {'role': 'user', 'content': prompt}
        ],
        response_format={"type": "json_object"},
    )
    abnormal_patterns = response.choices[0].message.content.strip()
    
    return json.loads(abnormal_patterns)

# Example usage
if __name__ == "__main__":
    enriched_incident = {
      "incident": {
        "title": "实时风控决策延迟分析",
        "affected_components": {
          "primary_system": "实时风控决策（风险管理）",
          "dependent_systems": [
            "大数据平台",
            "核心系统",
            "安全认证",
            "用户中心",
            "反欺诈"
          ],
          "transaction_chain": [
            "业务请求接入层",
            "规则引擎计算节点",
            "风险特征计算服务",
            "外部数据源接口",
            "决策结果反馈通道"
          ]
        },
        "severity": "High",
        "symptom_analysis": {
          "observed_issues": [
            "单笔决策耗时从50ms上升至300-800ms",
            "吞吐量下降60%但CPU使用率<30%",
            "规则执行日志无异常告警",
            "第三方特征服务延迟波动（P99从120ms升至450ms）"
          ],
          "technical_characteristics": {
            "timing": "业务高峰时段（10:00-15:00）",
            "frequency": "持续发生但存在间歇性恢复",
            "impact_scope": "影响所有风控拦截类交易",
            "system_behavior": "JVM Full GC次数正常，线程池队列积压突增"
          }
        },
        "time_range": {
          "start": "2023-08-15T10:00:00+08:00",
          "end": "2023-08-15T14:00:00+08:00",
          "duration_hours": 4
        },
        "business_impact": {
          "operational_impact": [
            "支付类交易平均延迟增加2.3秒",
            "自动阻断率异常升高0.5%",
            "人工审核工单量激增120%"
          ],
          "customer_experience": [
            "电商支付失败率上升至0.8%",
            "客户投诉量增加65件/小时",
            "高风险交易人工复核导致用户体验下降"
          ]
        },
        "recommended_actions": {
          "dependency_analysis": [
            "检查大数据平台特征计算响应时间分布",
            "验证三方反欺诈接口SLI达标率",
            "跟踪规则引擎执行计划生成耗时"
          ],
          "system_analysis": [
            "分析决策服务线程池阻塞情况",
            "检查JIT编译热点方法变更",
            "验证缓存服务连接池利用率",
            "监控数据库慢查询日志"
          ],
          "dataflow_analysis": [
            "采样全链路trace分析耗时分布",
            "检查特征数据序列化/反序列化性能",
            "验证实时事件流处理延迟"
          ],
          "external_services": [
            "核查人行公安接口响应时间",
            "测试短信平台异步通知延迟",
            "评估安全认证服务令牌获取效率"
          ],
          "log_analysis": [
            "检索规则引擎调试日志中的warning模式",
            "分析线程dump中的锁竞争情况",
            "核对时钟同步服务状态"
          ]
        }
      }
    }
    abnormal_patterns = design_abnormal_patterns(enriched_incident)
    print(json.dumps(abnormal_patterns, indent=2, ensure_ascii=False))
