# Observability Evol Instruct

借鉴 Evol Instruct 方法，利用 Deepseek R1 推理模型的能力，合成可观测性和根因分析数据。
Leveraging the Evol Instruct method and the capabilities of Deepseek R1 inference model to synthesize observability and root cause analysis data.

## 计划 | Plan

### prompt 调试 | Prompt Debugging

- [x] 根因分析问题的 seed 冷启动
    Cold start seed for root cause analysis problems

- [ ] 考虑 self_instruct 方法，从 service_list 中生产更多问题，但要考虑是否会重复率过高(试了几次，10 个冷启动的质量过滤都不能 100% 通过)
   Consider self_instruct method to generate more questions from service_list, but need to consider if the duplication rate would be too high (tried several times, 10 cold starts couldn't pass 100% quality filtering)

- [x] 补充问题的背景
    Enrich context to the problems

- [x] 扩展更多 Depth 和 Breath 问题
    Evol instruct for more Depth and Breadth questions

- [x] 问题质量检测过滤器
    Question quality detection filter

- [x] 生成问题对应的监控指标的行为模式
    Generate behavior patterns of monitoring metrics corresponding to the problems

- [x] 根据模式生成指标数据的 Python 代码
    Generate Python code for metric data based on patterns

- [x] 生成问题对应的日志和变更事件
    Generate corresponding logs and change events for the problems

- [ ] 生成问题对应的调用链数据(触发敏感审查了，奇怪)
   Generate corresponding trace data for the problems (triggered sensitive review, strange)

- [x] 生成 RCA 报告
    Generate RCA reports

- [x] 生成数据和报告之间的一致性检查
    Generate consistency check between data and reports

### pipeline 代码 | Pipeline Code

- [x] 单独脚本可运行
    Individual scripts are runnable

- [x] 主程序可运行
    Main program is runnable

- [x] 批量 incident/metric 要按 id 存储文件，方便多次运行
    Batch incident/metric files should be stored by id for convenient multiple runs

- [ ] 考虑一致性检查的后续处理
   Consider follow-up processing for consistency checks

- [ ] 考虑 metric data 超过 window 大小的方案
   Consider solutions for metric data exceeding window size

## 感谢 | Acknowledgements

感谢以下项目和工具的启发与帮助：
Thanks to the following projects and tools for their inspiration and help:

- distilabel: 提供了高质量数据标注和评估的初始思路
  distilabel: Provided initial ideas for high-quality data labeling and evaluation

- flip.ai: 提供了可观测性领域 evol-instruct 和 RLHAIF 的思路
  flip.ai: Provided ideas for evol-instruct and RLHAIF in the observability domain

- ChatTS: 为时序数据生成提供了指标属性和常见模式的样例
  ChatTS: Provided examples of metric properties and common patterns for time series data generation

- MCQ2: 为时序数据生成提供了 python 合成的思路
  MCQ2: Provided ideas for Python synthesis of time series data

- cursor: 提供了优秀的 AI 辅助编程体验
  cursor: Provided excellent AI-assisted programming experience

- deepseek: 提供了强大的开源推理模型能力，为大批量合成数据提供了可能性
  deepseek: Provided powerful open-source inference model capabilities, making large-scale data synthesis possible
