from openai_client import get_openai_client
import json
import os

def generate_synthetic_data(metric_patterns):
    all_data = []
    for metric in metric_patterns['metrics']:
        metric_patterns_str = json.dumps(metric, ensure_ascii=False)
        
        prompt = f"""
        Using the metric pattern defined in ###metric_patterns_str###, generate Python code that creates synthetic time series data for this metric. The code should:
        1. Write a numpy function called `generate_series`, outputs a time series that matches the metric pattern
        2. All parameters from the data generating process should be drawn from reasonable distributions. You should also make sure that the scale of time series is realistic.
        3. Add appropriate noise and seasonality
        4. Only include data for the abnormal periods and an equal length of normal periods preceding them
        5. The function must return data in CSV format
        6. Use datetime objects or timestamps for time handling, avoid direct string manipulation of dates.
        7. After defining the function, add a line to call the function and assign its result to a variable named 'synthetic_data'.
        8. When using pandas to_csv(), use lineterminator='\\n' with proper escape characters.
        9. When using pandas date_range, use 's' instead of 'S' for seconds frequency.
        10. Make sure to assign the result to a variable named 'synthetic_data' before returning.
        11. When adding metadata as a comment at the top of the CSV, use proper escape characters for newlines (\\n).
        12. When combining timestamps, ensure that the timestamps array and values array have exactly the same length.
        13. Do not use timestamps_normal.union(timestamps_abnormal) as it may cause length mismatch. Instead, use np.concatenate for both timestamps and values.
        14. When using pd.date_range, always check the length of the resulting array and ensure it matches your expected number of points. If using start and end parameters together, verify the resulting length or use periods parameter instead.
        15. For abnormal periods, calculate the exact number of points needed and use periods parameter in pd.date_range instead of using start and end together.
        16. Before concatenating arrays, print their lengths to verify they match your expectations.
        17. After generating timestamps, explicitly verify that len(timestamps_normal) == len(normal_data) and len(timestamps_abnormal) == len(abnormal_data).

        ###CSV data Format Example###
        #metric=decision_latency_per_transaction,type=gauge,service=risk_management,url=/risk/decision
        1692064800,52.36
        1692064810,51.89

        ###metric_patterns_str###
        {metric_patterns_str}
        """
        
        client = get_openai_client()

        response = client.chat.completions.create(
            model="qwen-max-2025-01-25",
            messages=[
                {'role': 'system', 'content': 'You are a helpful assistant. Generate only valid Python code that can be executed directly.'},
                {'role': 'user', 'content': prompt}
            ],
        )
        code = response.choices[0].message.content.strip()

        # 提取实际的 Python 代码（如果代码被 Markdown 代码块包围）
        if '```python' in code:
            code = code.split('```python')[1].split('```')[0].strip()
        elif '```' in code:
            code = code.split('```')[1].split('```')[0].strip()
            
        exec_globals = {}
        try:
            # 首先尝试编译代码以捕获语法错误
            compile(code, '<string>', 'exec')
            # 如果编译成功，则执行代码
            exec(code, exec_globals)
            all_data.append(exec_globals['synthetic_data'])
        except SyntaxError as e:
            print(f"语法错误: {str(e)}\n代码:\n{code}")
            continue
        except Exception as e:
            print(f"执行错误: {str(e)}\n代码:\n{code}")
            continue
    
    return '\n\n'.join(all_data)

# Example usage
if __name__ == "__main__":
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

    synthetic_data = generate_synthetic_data(metric_patterns)
    print(synthetic_data)

