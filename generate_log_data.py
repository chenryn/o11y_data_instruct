from openai_client import get_openai_client
import json
import os

def generate_log_data(enriched_incident, metric_patterns):
    prompt = f"""
    For the incident ###enriched_incident### and generated metrics ###metric_patterns###, create log message 
    templates that would appear around the incident time. Include:
    1. Error messages from affected components
    2. Warning messages indicating developing issues
    3. Info messages showing system state changes
    4. Debug messages with relevant technical details

    ### enriched_incident ###
    {enriched_incident}

    ### metric_patterns ###
    {metric_patterns}

    Format as log4j style log with timestamp, hostname, severity levels and component tags.
    """

    client = get_openai_client()

    response = client.chat.completions.create(
        model="qwen-max-2025-01-25",
        messages=[
            {'role': 'system', 'content': 'You are a helpful assistant.'},
            {'role': 'user', 'content': prompt}
        ]
    )

    log_data = response.choices[0].message.content.strip()
    return log_data

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
    metric_patterns = {
      "metrics": [
        {
          "metric_name": "decision_latency_per_transaction",
          "type": "gauge",
          "normal_range": "50ms",
          "unit": "milliseconds",
          "dimensional_labels": ["service=risk_management", "url=/risk/decision"],
          "statistical_characteristics": ["trend", "noise"],
          "abnormal_pattern_type": "continuous upward spike",
          "time_frame": {
            "start": "2023-08-15T10:00:00+08:00",
            "end": "2023-08-15T14:00:00+08:00"
          },
          "correlation": ["third_party_feature_service_p99_latency", "thread_pool_queue_size"]
        },
        {
          "metric_name": "throughput_tps",
          "type": "counter",
          "normal_range": "5000-6000",
          "unit": "transactions/second",
          "dimensional_labels": ["service=risk_management", "component=rule_engine"],
          "statistical_characteristics": ["seasonal", "trend"],
          "abnormal_pattern_type": "continuous downward spike",
          "time_frame": {
            "start": "2023-08-15T10:00:00+08:00",
            "end": "2023-08-15T14:00:00+08:00"
          },
          "correlation": ["decision_latency_per_transaction", "thread_pool_queue_size"]
        },
        {
          "metric_name": "third_party_feature_service_p99_latency",
          "type": "gauge",
          "normal_range": "120ms",
          "unit": "milliseconds",
          "dimensional_labels": ["service=external_data_source", "ip=10.20.30.40"],
          "statistical_characteristics": ["frequency", "noise"],
          "abnormal_pattern_type": "wide upward spike",
          "time_frame": {
            "start": "2023-08-15T10:00:00+08:00",
            "end": "2023-08-15T14:00:00+08:00"
          },
          "correlation": ["decision_latency_per_transaction", "database_slow_query_count"]
        },
        {
          "metric_name": "thread_pool_queue_size",
          "type": "gauge",
          "normal_range": "0-50",
          "unit": "tasks",
          "dimensional_labels": ["service=risk_management", "thread_pool=decision_executor"],
          "statistical_characteristics": ["sudden_change", "noise"],
          "abnormal_pattern_type": "sudden increase",
          "time_frame": {
            "start": "2023-08-15T10:15:00+08:00",
            "end": "2023-08-15T13:45:00+08:00"
          },
          "correlation": ["throughput_tps", "decision_latency_per_transaction"]
        },
        {
          "metric_name": "database_slow_query_count",
          "type": "counter",
          "normal_range": "0-5",
          "unit": "queries/minute",
          "dimensional_labels": ["service=big_data_platform", "db_cluster=risk_features"],
          "statistical_characteristics": ["frequency", "trend"],
          "abnormal_pattern_type": "sudden increase",
          "time_frame": {
            "start": "2023-08-15T10:30:00+08:00",
            "end": "2023-08-15T14:00:00+08:00"
          },
          "correlation": ["third_party_feature_service_p99_latency", "decision_latency_per_transaction"]
        }
      ],
      "event_patterns": {
        "concurrent_anomalies": [
          {
            "metrics": ["decision_latency_per_transaction", "thread_pool_queue_size"],
            "pattern_type": "cascading_failure",
            "time_window": "10:00-11:00"
          },
          {
            "metrics": ["third_party_feature_service_p99_latency", "database_slow_query_count"],
            "pattern_type": "resource_contention",
            "time_window": "11:30-13:00"
          }
        ]
      }
    }

    log_data = generate_log_data(enriched_incident, metric_patterns)
    print(log_data)
