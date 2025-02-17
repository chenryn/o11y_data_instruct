from init_seed import generate_incidents
from enrich_problem import enrich_incident_context
from evol_instruct import EvolInstruct
from define_metric_pattern import design_abnormal_patterns
from generate_log_data import generate_log_data
from generate_event_timeline import generate_event_timeline
from generate_metric_data import generate_synthetic_data
from init_rca_cot import get_root_cause_analysis
# from evol_consistency_check import check_scenario_consistency
import json
import os
import time
import logging
import uuid

class PipelineExecutor:
    def __init__(self):
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        self.evol_instruct = EvolInstruct()
        self.incidents = []
        self.enriched_incidents = []
        self.metrics_data = {}
        self.logs_data = {}
        self.events_data = {}
        self.analysis_data = {}
        self.metrics_pattern = {}
        # 添加限速控制
        self.last_api_call = 0

    def rate_limit(self):
        """实现简单的限速控制"""
        current_time = time.time()
        # 固定每次调用间隔为 60 秒
        elapsed = current_time - self.last_api_call
        if elapsed < 60:
            time.sleep(60 - elapsed)
        
        self.last_api_call = time.time()

    def init_seed(self):
        self.logger.info("开始生成初始故障场景...")
        self.incidents = generate_incidents()
        self.logger.info(f"成功生成 {len(self.incidents)} 个初始故障场景")

    def enrich_incident(self):
        self.logger.info("开始丰富故障场景上下文...")
        for i, incident in enumerate(self.incidents, 1):
            self.logger.info(f"正在处理第 {i}/{len(self.incidents)} 个故障场景")
            enriched = enrich_incident_context(incident)
            enriched['id'] = str(uuid.uuid4())
            self.enriched_incidents.append(enriched)
        self.logger.info("故障场景上下文丰富完成")

    def generate_more_incidents(self):
        self.logger.info("开始生成相关和复杂故障场景...")
        # 对原有场景进行质量过滤
        filtered_incidents = []
        for incident in self.enriched_incidents:
            if self.evol_instruct.quality_filter(incident):
                filtered_incidents.append(incident)
                self.rate_limit()
        
        self.logger.info(f"质量过滤后保留 {len(filtered_incidents)}/{len(self.enriched_incidents)} 个原始场景")
        self.enriched_incidents = filtered_incidents

        # 生成新的场景
        new_incidents = []
        for i, incident in enumerate(self.enriched_incidents, 1):
            self.logger.info(f"正在处理第 {i}/{len(self.enriched_incidents)} 个故障场景的衍生场景")
            
            # 生成相关场景
            self.rate_limit()
            related = self.evol_instruct.generate_related_incident(incident)
            if self.evol_instruct.quality_filter(related):
                new_incidents.append(related)
            
            # 生成复杂场景
            self.rate_limit()
            complex = self.evol_instruct.generate_complex_incident(incident)
            if self.evol_instruct.quality_filter(complex):
                new_incidents.append(complex)
            
            # 生成情境场景
            self.rate_limit()
            situation = self.evol_instruct.generate_situation_incident(incident)
            if self.evol_instruct.quality_filter(situation):
                new_incidents.append(situation)
            
            # 生成因果分析场景
            self.rate_limit()
            causal = self.evol_instruct.generate_causal_incident(incident)
            if self.evol_instruct.quality_filter(causal):
                new_incidents.append(causal)
            
            # 生成约束条件场景
            self.rate_limit()
            constraints = self.evol_instruct.generate_constraints_incident(incident)
            if self.evol_instruct.quality_filter(constraints):
                new_incidents.append(constraints)
            
            # 生成复杂推理场景
            self.rate_limit()
            complex_reasoning = self.evol_instruct.generate_complex_reasoning_incident(incident)
            if self.evol_instruct.quality_filter(complex_reasoning):
                new_incidents.append(complex_reasoning)

        self.enriched_incidents.extend(new_incidents)
        self.logger.info(f"故障场景扩展完成，总计 {len(self.enriched_incidents)} 个场景")

    def define_metric_pattern(self):
        for incident in self.enriched_incidents:
            self.metrics_pattern[incident['id']] = design_abnormal_patterns(incident)
            self.rate_limit()

    def generate_log_data(self):
        for incident in self.enriched_incidents:
            self.logs_data[incident['id']] = generate_log_data(
                incident,
                self.metrics_pattern[incident['id']]
            )
            self.rate_limit()

    def generate_event_timeline(self):
        for incident in self.enriched_incidents:
            self.events_data[incident['id']] = generate_event_timeline(
                incident,
                self.metrics_pattern[incident['id']],
                self.logs_data[incident['id']]
            )
            self.rate_limit()

    def generate_metric_data(self):
        for incident in self.enriched_incidents:
            self.metrics_data[incident['id']] = generate_synthetic_data(
                self.metrics_pattern[incident['id']]
            )
            self.rate_limit()

    def init_rca_cot(self):
        for incident in self.enriched_incidents:
            incident_id = incident['id']
            self.analysis_data[incident_id] = get_root_cause_analysis(
                incident,
                self.metrics_data[incident_id],
                self.logs_data[incident_id],
                self.events_data[incident_id]
            )
            self.rate_limit()
            # # 一致性检查
            # check_scenario_consistency(
            #     incident,
            #     self.metrics_data[incident_id],
            #     self.logs_data[incident_id],
            #     self.events_data[incident_id],
            #     self.analysis_data[incident_id]
            # )

    def save_step_data(self, output_dir, step_name):
        """保存指定步骤的数据"""
        self.logger.info(f"保存 {step_name} 步骤的数据...")
        os.makedirs(output_dir, exist_ok=True)
        
        for incident in self.enriched_incidents:
            incident_id = incident['id']
            incident_dir = os.path.join(output_dir, f'incident_{incident_id}')
            os.makedirs(incident_dir, exist_ok=True)
            
            # 根据步骤保存相应数据
            if step_name in ['init_seed', 'enrich_incident', 'generate_more_incidents']:
                with open(os.path.join(incident_dir, 'incident.json'), 'w', encoding='utf-8') as f:
                    json.dump(incident, f, indent=2, ensure_ascii=False)
            
            elif step_name == 'define_metric_pattern':
                with open(os.path.join(incident_dir, 'metrics_pattern.json'), 'w', encoding='utf-8') as f:
                    json.dump(self.metrics_pattern.get(incident_id, {}), f, indent=2, ensure_ascii=False)
            
            elif step_name == 'generate_log_data':
                with open(os.path.join(incident_dir, 'logs.txt'), 'w', encoding='utf-8') as f:
                    f.write(self.logs_data.get(incident_id, ''))
            
            elif step_name == 'generate_event_timeline':
                with open(os.path.join(incident_dir, 'events.json'), 'w', encoding='utf-8') as f:
                    json.dump(self.events_data.get(incident_id, {}), f, indent=2, ensure_ascii=False)
            
            elif step_name == 'generate_metric_data':
                with open(os.path.join(incident_dir, 'metrics.txt'), 'w', encoding='utf-8') as f:
                    f.write(self.metrics_data.get(incident_id, ''))
            
            elif step_name == 'init_rca_cot':
                with open(os.path.join(incident_dir, 'analysis.json'), 'w', encoding='utf-8') as f:
                    json.dump(self.analysis_data.get(incident_id, {}), f, indent=2, ensure_ascii=False)

    def run_pipeline(self, output_dir='output', start_step=None):
        """
        执行故障场景生成流水线
        :param output_dir: 数据保存目录
        :param start_step: 从指定步骤开始执行，如果为None则从头开始
        """
        steps = [
            ('init_seed', self.init_seed),
            ('enrich_incident', self.enrich_incident),
            ('generate_more_incidents', self.generate_more_incidents),
            ('define_metric_pattern', self.define_metric_pattern),
            ('generate_log_data', self.generate_log_data),
            ('generate_event_timeline', self.generate_event_timeline),
            ('generate_metric_data', self.generate_metric_data),
            ('init_rca_cot', self.init_rca_cot)
        ]
        
        # 确定起始步骤
        start_idx = 0
        if start_step:
            for idx, (step_name, _) in enumerate(steps):
                if step_name == start_step:
                    start_idx = idx
                    break
        
        self.logger.info(f"=== 开始执行故障场景生成流水线 (从 {steps[start_idx][0]} 步骤开始) ===")
        
        # 如果不是从头开始，先加载已有数据
        if start_idx > 0:
            self.load_data(output_dir)
        
        # 执行流水线步骤
        for step_name, step_func in steps[start_idx:]:
            self.logger.info(f"执行步骤: {step_name}")
            step_func()
            self.save_step_data(output_dir, step_name)
            self.rate_limit()
        
        self.logger.info("=== 故障场景生成流水线执行完成 ===")

    def load_data(self, output_dir):
        """从指定目录加载已保存的数据"""
        self.logger.info(f"从 {output_dir} 加载已有数据...")
        
        # 遍历输出目录下的所有incident目录
        for incident_dir in os.listdir(output_dir):
            if not incident_dir.startswith('incident_'):
                continue
                
            incident_path = os.path.join(output_dir, incident_dir)
            if not os.path.isdir(incident_path):
                continue
                
            incident_id = incident_dir.replace('incident_', '')
            
            # 加载incident数据
            incident_file = os.path.join(incident_path, 'incident.json')
            if os.path.exists(incident_file):
                with open(incident_file, 'r', encoding='utf-8') as f:
                    incident = json.load(f)
                    self.enriched_incidents.append(incident)
            
            # 加载metrics pattern数据
            pattern_file = os.path.join(incident_path, 'metrics_pattern.json')
            if os.path.exists(pattern_file):
                with open(pattern_file, 'r', encoding='utf-8') as f:
                    self.metrics_pattern[incident_id] = json.load(f)
            
            # 加载logs数据
            logs_file = os.path.join(incident_path, 'logs.txt')
            if os.path.exists(logs_file):
                with open(logs_file, 'r', encoding='utf-8') as f:
                    self.logs_data[incident_id] = f.read()
            
            # 加载events数据
            events_file = os.path.join(incident_path, 'events.json')
            if os.path.exists(events_file):
                with open(events_file, 'r', encoding='utf-8') as f:
                    self.events_data[incident_id] = json.load(f)
            
            # 加载metrics数据
            metrics_file = os.path.join(incident_path, 'metrics.txt')
            if os.path.exists(metrics_file):
                with open(metrics_file, 'r', encoding='utf-8') as f:
                    self.metrics_data[incident_id] = f.read()
            
            # 加载analysis数据
            analysis_file = os.path.join(incident_path, 'analysis.json')
            if os.path.exists(analysis_file):
                with open(analysis_file, 'r', encoding='utf-8') as f:
                    self.analysis_data[incident_id] = json.load(f)
        
        self.logger.info(f"成功加载 {len(self.enriched_incidents)} 个故障场景的数据")

if __name__ == "__main__":
    executor = PipelineExecutor()
    executor.run_pipeline('output')
    # 示例：从 generate_metric_data 步骤开始执行
    # executor.run_pipeline('output', start_step='generate_metric_data')