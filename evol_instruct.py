from openai_client import get_openai_client
import os
import json
import uuid

class EvolInstruct:
    def __init__(self):
        self.client = get_openai_client()

    def breath_prompt(self, system_data):
        prompt = f"""
        Generate a new rarely but related incident scenario that could occur in the same system based on:
        1. Similar components but different root cause
        2. Different components but similar pattern
        3. Cascade effect from the original issue
        4. Alternative failure mode
        5. Related configuration issue

        ###Old Incident Data###
        {system_data}

        Format the response as a structured JSON document.
        """
        return prompt
        
    def depth_prompt(self, system_data):
        prompt = f"""
        Take this root cause analysis scenario and make it more complex by adding ONE of the following:
        1. Additional contributing factors
        2. Environmental complications
        3. Misleading symptoms
        4. Infrastructure dependencies
        5. Configuration complexities

        ###Old Incident Data###
        {system_data}

        Format the response as a structured JSON document.
        """
        return prompt
    
    def situation_prompt(self, system_data):
        prompt = f"""
        基于现有故障场景，创建一个更具体的虚拟场景，要求：
        1. 设定真实的业务背景（如特定行业、系统环境）
        2. 添加具体的时间、地点等环境信息
        3. 增加用户行为或业务流程细节
        4. 补充系统配置或架构细节
        5. 添加相关的监控指标和阈值

        ###Old Incident Data###
        {system_data}

        Format the response as a structured JSON document.
        """
        return prompt
    
    def causal_prompt(self, system_data):
        prompt = f"""
        基于现有故障场景，深入分析因果关系：
        1. 识别潜在的根本原因链
        2. 分析故障传播路径
        3. 推导可能的连锁反应
        4. 预测潜在的后续影响
        5. 分析预防措施的有效性

        ###Old Incident Data###
        {system_data}

        Format the response as a structured JSON document.
        """
        return prompt
    
    def constraints_prompt(self, system_data):
        prompt = f"""
        为现有故障场景添加更多约束条件：
        1. 系统资源限制
        2. 安全策略要求
        3. 业务规则约束
        4. 性能指标要求
        5. 合规性要求

        ###Old Incident Data###
        {system_data}

        Format the response as a structured JSON document.
        """
        return prompt
    
    def complex_reasoning_prompt(self, system_data):
        prompt = f"""
        将现有故障场景转化为需要多步骤推理的复杂问题：
        1. 添加多个相互依赖的系统组件
        2. 引入时序依赖关系
        3. 增加条件分支场景
        4. 添加多重故障模式
        5. 引入系统状态转换

        ###Old Incident Data###
        {system_data}

        Format the response as a structured JSON document.
        """
        return prompt

    def quality_filter_prompt(self, system_data):
        prompt = f"""
        Evaluate the quality of this generated incident data based on:
        1. Realism of the incident
        2. Completeness of observability data
        3. Clarity of the analysis
        4. Educational value
        5. Technical accuracy

        Output only 'remove' if any aspect scores below 3 in your internal evaluation, otherwise output 'keep'. Respond with exactly one lowercase word.
        
        ### Incident Data ###
        {system_data}
        """
        return prompt

    def _generate_incident(self, system_data, prompt_method):
        """
        通用的场景生成方法
        :param system_data: 输入的系统数据
        :param prompt_method: 使用的 prompt 方法（类的成员方法）
        :return: 生成的新场景
        """
        response = self.client.chat.completions.create(
            model="qwen-max-2025-01-25",
            messages=[
                {'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'user', 'content': prompt_method(system_data)}
            ],
            response_format={"type": "json_object"}
        )
        new_scenario = json.loads(response.choices[0].message.content.strip())
        
        # 为场景添加 UUID
        if 'incident' in new_scenario:
            new_scenario['incident']['id'] = str(uuid.uuid4())
        else:
            new_scenario['id'] = str(uuid.uuid4())
            
        return new_scenario

    def generate_related_incident(self, system_data):
        return self._generate_incident(system_data, self.breath_prompt)

    def generate_complex_incident(self, system_data):
        return self._generate_incident(system_data, self.depth_prompt)

    def generate_situation_incident(self, system_data):
        return self._generate_incident(system_data, self.situation_prompt)

    def generate_causal_incident(self, system_data):
        return self._generate_incident(system_data, self.causal_prompt)

    def generate_constraints_incident(self, system_data):
        return self._generate_incident(system_data, self.constraints_prompt)

    def generate_complex_reasoning_incident(self, system_data):
        return self._generate_incident(system_data, self.complex_reasoning_prompt)

    def quality_filter(self, system_data):        
        response = self.client.chat.completions.create(
            model="qwen-max-2025-01-25",
            messages=[
                {'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'user', 'content': self.quality_filter_prompt(system_data)}
            ],
            max_tokens=10
        )
        is_quality = response.choices[0].message.content.strip()
        # 根据返回值判断是否保留该场景
        return is_quality == "keep"

# Example usage
if __name__ == "__main__":
    sample_incident = {
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
                    "柜面服务效率下降",
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
    
    generator = EvolInstruct()
    related_scenario = generator.generate_related_incident(sample_incident)
    print("Related Scenario:")
    print(json.dumps(related_scenario, ensure_ascii=False, indent=2))
