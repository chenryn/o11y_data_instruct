from openai_client import get_openai_client
import numpy as np
from datetime import datetime

class MetricAgent:
    """
    指标分析Agent，负责对原始指标数据进行预处理，包括关键指标提取和数据压缩表示
    """
    def __init__(self):
        self.client = get_openai_client()
    
    def extract_key_metrics(self, metrics_data, incident=None, metrics_pattern=None):
        """
        从原始指标数据中提取关键指标
        
        Args:
            metrics_data: 原始指标数据文本
            incident: 事件信息，用于提供上下文
            metrics_pattern: 已废弃参数，保留仅为兼容性考虑
            
        Returns:
            提取后的关键指标信息
        """
        # 解析原始指标数据，提取指标名称和时间序列
        metrics_dict = self._parse_metrics_data(metrics_data)
        
        # 如果指标数量过多，进行初步筛选
        if len(metrics_dict) > 10:
            metrics_dict = self._filter_metrics(metrics_dict, incident)
        
        # 对每个指标进行统计分析和异常检测
        analyzed_metrics = self._analyze_metrics(metrics_dict)
        
        # 生成压缩表示
        compressed_representation = self._generate_compressed_representation(analyzed_metrics, incident)
        
        return compressed_representation
    
    def _parse_metrics_data(self, metrics_data):
        """
        解析原始指标数据，提取指标名称和时间序列
        
        Args:
            metrics_data: 原始指标数据文本
            
        Returns:
            解析后的指标字典，格式为 {metric_name: {metadata: {}, data: [(timestamp, value), ...]}}
        """
        metrics_dict = {}
        current_metric = None
        current_metadata = {}
        current_data = []
        
        for line in metrics_data.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # 检查是否是指标定义行
            if line.startswith('#metric='):
                # 如果已有指标数据，保存之前的指标
                if current_metric:
                    metrics_dict[current_metric] = {
                        'metadata': current_metadata,
                        'data': current_data
                    }
                
                # 解析新的指标定义
                metadata_str = line[8:]
                parts = metadata_str.split(',')
                current_metric = parts[0]
                current_metadata = {}
                current_data = []
                
                # 解析元数据
                for part in parts[1:]:
                    if '=' in part:
                        key, value = part.split('=', 1)
                        current_metadata[key] = value
            else:
                # 解析数据行
                try:
                    parts = line.split(',')
                    if len(parts) == 2:
                        timestamp, value = parts
                        current_data.append((int(timestamp), float(value)))
                except Exception:
                    continue
        
        # 保存最后一个指标
        if current_metric:
            metrics_dict[current_metric] = {
                'metadata': current_metadata,
                'data': current_data
            }
        
        return metrics_dict
    
    def _filter_metrics(self, metrics_dict, incident=None):
        """
        根据事件信息和指标特征，筛选最相关的指标
        
        Args:
            metrics_dict: 解析后的指标字典
            incident: 事件信息
            
        Returns:
            筛选后的指标字典
        """
        
        # 自动识别关键指标模式
        # 1. 计算每个指标的变异系数，用于评估波动性
        metric_scores = {}
        for metric_name, metric_data in metrics_dict.items():
            values = [v for _, v in metric_data['data']]
            if not values:
                continue
                
            mean = np.mean(values)
            std = np.std(values)
            # 变异系数 = 标准差/均值，用于评估相对波动性
            cv = std / mean if mean != 0 else 0
            # 计算最大值与最小值的比率
            max_min_ratio = max(values) / min(values) if min(values) != 0 else 0
            # 计算异常点比例（超过2个标准差的点）
            anomaly_ratio = sum(1 for v in values if abs(v - mean) > 2 * std) / len(values) if std != 0 else 0
            
            # 综合评分
            score = cv * 0.4 + max_min_ratio * 0.3 + anomaly_ratio * 0.3
            metric_scores[metric_name] = score
        
        # 按评分排序并选择前10个指标
        sorted_metrics = sorted(metric_scores.items(), key=lambda x: x[1], reverse=True)
        top_metrics = [m[0] for m in sorted_metrics[:10]]
        
        return {m: metrics_dict[m] for m in top_metrics if m in metrics_dict}
    
    def _analyze_metrics(self, metrics_dict):
        """
        对每个指标进行统计分析和异常检测
        
        Args:
            metrics_dict: 指标字典
            
        Returns:
            分析后的指标信息
        """
        analyzed_metrics = {}
        
        for metric_name, metric_data in metrics_dict.items():
            values = [v for _, v in metric_data['data']]
            timestamps = [ts for ts, _ in metric_data['data']]
            
            if not values or not timestamps:
                continue
            
            # 基本统计信息
            stats = {
                'mean': np.mean(values),
                'median': np.median(values),
                'std': np.std(values),
                'min': np.min(values),
                'max': np.max(values),
                'range': np.max(values) - np.min(values),
                'start_time': min(timestamps),
                'end_time': max(timestamps),
                'duration': max(timestamps) - min(timestamps),
                'data_points': len(values)
            }
            
            # 趋势分析
            if len(values) > 2:
                # 简单线性回归计算趋势
                x = np.array(range(len(values)))
                y = np.array(values)
                A = np.vstack([x, np.ones(len(x))]).T
                m, c = np.linalg.lstsq(A, y, rcond=None)[0]
                stats['trend'] = m
                stats['trend_direction'] = 'increasing' if m > 0 else 'decreasing' if m < 0 else 'stable'
            
            # 异常检测
            mean = stats['mean']
            std = stats['std']
            anomalies = []
            
            for i, (ts, val) in enumerate(metric_data['data']):
                if std > 0 and abs(val - mean) > 2 * std:
                    anomalies.append({
                        'timestamp': ts,
                        'value': val,
                        'deviation': (val - mean) / std if std > 0 else 0
                    })
            
            # 按偏差程度排序异常点
            anomalies.sort(key=lambda x: abs(x['deviation']), reverse=True)
            stats['anomalies'] = anomalies[:10]  # 只保留最显著的10个异常点
            
            # 计算异常区间
            if anomalies:
                anomaly_timestamps = [a['timestamp'] for a in anomalies]
                anomaly_start = min(anomaly_timestamps)
                anomaly_end = max(anomaly_timestamps)
                stats['anomaly_period'] = (anomaly_start, anomaly_end)
            
            analyzed_metrics[metric_name] = {
                'metadata': metric_data['metadata'],
                'stats': stats
            }
        
        return analyzed_metrics
    
    def _generate_compressed_representation(self, analyzed_metrics, incident=None):
        """
        生成指标数据的压缩表示
        
        Args:
            analyzed_metrics: 分析后的指标信息
            incident: 事件信息
            
        Returns:
            指标数据的压缩表示
        """
        # 构建压缩表示
        compressed = {
            'metrics_summary': {
                'total_metrics': len(analyzed_metrics),
                'time_range': self._get_overall_time_range(analyzed_metrics),
                'key_metrics': []
            }
        }
        
        # 添加每个指标的摘要信息
        for metric_name, metric_info in analyzed_metrics.items():
            stats = metric_info['stats']
            metadata = metric_info['metadata']
            
            # 构建指标摘要
            metric_summary = {
                'name': metric_name,
                'type': metadata.get('type', 'unknown'),
                'labels': metadata,
                'statistics': {
                    'mean': round(stats['mean'], 4),
                    'median': round(stats['median'], 4),
                    'std': round(stats['std'], 4),
                    'min': round(stats['min'], 4),
                    'max': round(stats['max'], 4),
                    'range': round(stats['range'], 4)
                },
                'trend': stats.get('trend_direction', 'unknown'),
                'data_points': stats['data_points']
            }
            
            # 添加异常信息
            if 'anomalies' in stats and stats['anomalies']:
                metric_summary['anomalies'] = {
                    'count': len(stats['anomalies']),
                    'top_anomalies': [
                        {
                            'timestamp': a['timestamp'],
                            'value': round(a['value'], 4),
                            'deviation': round(a['deviation'], 2)
                        } for a in stats['anomalies'][:5]  # 只包含前5个最显著的异常
                    ]
                }
                
                if 'anomaly_period' in stats:
                    start, end = stats['anomaly_period']
                    metric_summary['anomalies']['period'] = {
                        'start': start,
                        'end': end,
                        'duration': end - start
                    }
            
            compressed['metrics_summary']['key_metrics'].append(metric_summary)
        
        # 如果有事件信息，添加关联分析
        if incident:
            compressed['incident_correlation'] = self._correlate_with_incident(analyzed_metrics, incident)
        
        return compressed
    
    def _get_overall_time_range(self, analyzed_metrics):
        """
        获取所有指标的整体时间范围
        
        Args:
            analyzed_metrics: 分析后的指标信息
            
        Returns:
            整体时间范围
        """
        start_times = []
        end_times = []
        
        for metric_info in analyzed_metrics.values():
            stats = metric_info['stats']
            if 'start_time' in stats and 'end_time' in stats:
                start_times.append(stats['start_time'])
                end_times.append(stats['end_time'])
        
        if start_times and end_times:
            return {
                'start': min(start_times),
                'end': max(end_times),
                'duration': max(end_times) - min(start_times)
            }
        
        return {'start': None, 'end': None, 'duration': None}
    
    def _correlate_with_incident(self, analyzed_metrics, incident):
        """
        将指标与事件信息进行关联分析
        
        Args:
            analyzed_metrics: 分析后的指标信息
            incident: 事件信息
            
        Returns:
            关联分析结果
        """
        # 提取事件的时间范围
        incident_time_range = None
        if 'time_range' in incident:
            try:
                start_str = incident['time_range']['start']
                end_str = incident['time_range']['end']
                
                # 转换为时间戳
                start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
                
                incident_time_range = {
                    'start': int(start_dt.timestamp()),
                    'end': int(end_dt.timestamp())
                }
            except Exception:
                pass
        
        # 如果无法获取事件时间范围，返回空结果
        if not incident_time_range:
            return {}
        
        # 分析每个指标在事件时间范围内的行为
        correlation_results = {
            'metrics_in_incident_period': [],
            'anomalous_metrics': [],
            'potential_causes': [],
            'affected_services': set()
        }
        
        for metric_name, metric_info in analyzed_metrics.items():
            stats = metric_info['stats']
            metadata = metric_info['metadata']
            
            # 检查指标是否在事件时间范围内有数据
            if stats['start_time'] <= incident_time_range['end'] and stats['end_time'] >= incident_time_range['start']:
                # 提取事件期间的数据点
                incident_period_data = []
                for ts, val in metric_info.get('data', []):
                    if incident_time_range['start'] <= ts <= incident_time_range['end']:
                        incident_period_data.append((ts, val))
                
                # 如果事件期间有数据，添加到相关指标列表
                if incident_period_data:
                    correlation_results['metrics_in_incident_period'].append({
                        'name': metric_name,
                        'type': metadata.get('type', 'unknown'),
                        'service': metadata.get('service', 'unknown'),
                        'data_points_in_period': len(incident_period_data)
                    })
                    
                    # 记录受影响的服务
                    if 'service' in metadata:
                        correlation_results['affected_services'].add(metadata['service'])
            
            # 检查指标是否有异常，且异常时间与事件时间重叠
            if 'anomalies' in stats and stats['anomalies'] and 'anomaly_period' in stats:
                anomaly_start, anomaly_end = stats['anomaly_period']
                
                # 检查异常时间是否与事件时间重叠
                if anomaly_start <= incident_time_range['end'] and anomaly_end >= incident_time_range['start']:
                    # 计算重叠程度
                    overlap_start = max(anomaly_start, incident_time_range['start'])
                    overlap_end = min(anomaly_end, incident_time_range['end'])
                    overlap_duration = overlap_end - overlap_start
                    incident_duration = incident_time_range['end'] - incident_time_range['start']
                    overlap_percentage = (overlap_duration / incident_duration) * 100 if incident_duration > 0 else 0
                    
                    correlation_results['anomalous_metrics'].append({
                        'name': metric_name,
                        'type': metadata.get('type', 'unknown'),
                        'service': metadata.get('service', 'unknown'),
                        'anomaly_count': len(stats['anomalies']),
                        'overlap_percentage': round(overlap_percentage, 2),
                        'max_deviation': max([abs(a['deviation']) for a in stats['anomalies']]) if stats['anomalies'] else 0
                    })
                    
                    # 如果异常开始时间早于事件开始时间，可能是潜在原因
                    if anomaly_start < incident_time_range['start']:
                        correlation_results['potential_causes'].append({
                            'name': metric_name,
                            'type': metadata.get('type', 'unknown'),
                            'service': metadata.get('service', 'unknown'),
                            'anomaly_start': anomaly_start,
                            'time_before_incident': incident_time_range['start'] - anomaly_start
                        })
        
        # 转换集合为列表
        correlation_results['affected_services'] = list(correlation_results['affected_services'])
        
        # 按重要性排序
        if correlation_results['anomalous_metrics']:
            correlation_results['anomalous_metrics'].sort(key=lambda x: x['max_deviation'], reverse=True)
        
        if correlation_results['potential_causes']:
            correlation_results['potential_causes'].sort(key=lambda x: x['time_before_incident'])
        
        return correlation_results