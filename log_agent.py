from openai_client import get_openai_client
import json
import re
from datetime import datetime

class LogAgent:
    """
    日志分析Agent，负责对原始日志数据进行预处理，包括关键日志提取和多维度分析
    """
    def __init__(self):
        self.client = get_openai_client()
    
    def extract_key_logs(self, logs_data, incident=None):
        """
        从原始日志数据中提取关键日志信息
        
        Args:
            logs_data: 原始日志数据文本
            incident: 事件信息，用于提供上下文和生成查询关键字
            
        Returns:
            提取后的关键日志信息
        """
        # 解析原始日志数据
        parsed_logs = self._parse_logs_data(logs_data)
        
        # 根据incident生成查询关键字
        if incident:
            keywords = self._generate_keywords_from_incident(incident)
            # 使用关键字过滤日志
            filtered_logs = self._filter_logs_by_keywords(parsed_logs, keywords)
        else:
            filtered_logs = parsed_logs
        
        # 对日志进行时间聚合和异常检测
        analyzed_logs = self._analyze_logs(filtered_logs)
        
        # 生成多维度分析结果
        analysis_results = self._generate_multidimensional_analysis(analyzed_logs, incident)
        
        # 生成压缩表示
        compressed_representation = self._generate_compressed_representation(analyzed_logs, analysis_results, incident)
        
        return compressed_representation
    
    def _parse_logs_data(self, logs_data):
        """
        解析原始日志数据，提取时间戳、级别、组件、主机和消息内容
        
        Args:
            logs_data: 原始日志数据文本
            
        Returns:
            解析后的日志列表，每条日志为一个字典
        """
        parsed_logs = []
        
        # 移除Markdown格式和注释部分
        clean_logs = self._clean_markdown_format(logs_data)
        
        # 日志格式正则表达式 - 适配log4j风格
        # 例如: 2023-10-01T08:05:00Z [file_transfer_service] ERROR [primary_server] Disk space exhausted...
        log_pattern = r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\s+\[([^\]]+)\]\s+(\w+)\s+\[([^\]]+)\]\s+(.+)'
        
        for line in clean_logs.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            match = re.match(log_pattern, line)
            if match:
                timestamp_str, component, level, host, message = match.groups()
                
                # 解析时间戳
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%SZ')
                except ValueError:
                    # 如果时间戳格式不匹配，跳过或使用默认值
                    continue
                
                # 提取消息中的指标信息（如果有）
                metric_match = re.search(r'\(metric:\s*([^\)]+)\)', message)
                metric = metric_match.group(1) if metric_match else None
                
                # 构建结构化日志条目
                log_entry = {
                    'timestamp': timestamp,
                    'timestamp_str': timestamp_str,
                    'component': component.strip(),
                    'level': level.strip(),
                    'host': host.strip(),
                    'message': message.strip(),
                    'metric': metric
                }
                
                parsed_logs.append(log_entry)
        
        # 按时间戳排序
        parsed_logs.sort(key=lambda x: x['timestamp'])
        
        return parsed_logs
    
    def _clean_markdown_format(self, logs_data):
        """
        清理日志数据中的Markdown格式和注释
        
        Args:
            logs_data: 原始日志数据文本
            
        Returns:
            清理后的日志文本
        """
        # 移除Markdown标题、分隔符等
        clean_text = re.sub(r'^#+\s+.*$', '', logs_data, flags=re.MULTILINE)
        clean_text = re.sub(r'^---+$', '', clean_text, flags=re.MULTILINE)
        
        # 提取代码块中的日志内容
        code_blocks = re.findall(r'```log\n([\s\S]*?)```', clean_text)
        if code_blocks:
            return '\n'.join(code_blocks)
        
        # 如果没有代码块，尝试直接提取日志行
        log_lines = []
        for line in clean_text.split('\n'):
            # 检查是否是日志行（以时间戳开头）
            if re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', line.strip()):
                log_lines.append(line.strip())
        
        return '\n'.join(log_lines) if log_lines else clean_text
    
    def _generate_keywords_from_incident(self, incident):
        """
        根据事件信息生成查询关键字
        
        Args:
            incident: 事件信息
            
        Returns:
            关键字列表
        """
        keywords = []
        
        # 从incident中提取关键信息
        if isinstance(incident, str):
            try:
                incident_data = json.loads(incident)
            except json.JSONDecodeError:
                incident_data = {"incident": {"title": incident}}
        elif isinstance(incident, dict):
            incident_data = incident
        else:
            return keywords
        
        # 提取标题关键词
        if 'incident' in incident_data and 'title' in incident_data['incident']:
            title = incident_data['incident']['title']
            # 分词并添加到关键字列表
            title_words = re.findall(r'\w+', title)
            keywords.extend([word for word in title_words if len(word) > 2])
        
        # 提取受影响组件
        if 'incident' in incident_data and 'affected_components' in incident_data['incident']:
            affected_components = incident_data['incident']['affected_components']
            
            # 主要系统
            if 'primary_system' in affected_components:
                primary_system = affected_components['primary_system']
                if isinstance(primary_system, str):
                    keywords.append(primary_system)
            
            # 依赖系统
            if 'dependent_systems' in affected_components:
                dependent_systems = affected_components['dependent_systems']
                if isinstance(dependent_systems, str):
                    systems = [s.strip() for s in dependent_systems.split(',')]
                    keywords.extend(systems)
                elif isinstance(dependent_systems, list):
                    keywords.extend(dependent_systems)
        
        # 提取观察到的问题
        if 'incident' in incident_data and 'symptom_analysis' in incident_data['incident']:
            symptom_analysis = incident_data['incident']['symptom_analysis']
            
            if 'observed_issues' in symptom_analysis:
                observed_issues = symptom_analysis['observed_issues']
                if isinstance(observed_issues, str):
                    # 提取关键词
                    issue_words = re.findall(r'\w+', observed_issues)
                    keywords.extend([word for word in issue_words if len(word) > 3])
                elif isinstance(observed_issues, list):
                    for issue in observed_issues:
                        issue_words = re.findall(r'\w+', issue)
                        keywords.extend([word for word in issue_words if len(word) > 3])
        
        # 去重并返回
        return list(set(keywords))
    
    def _filter_logs_by_keywords(self, parsed_logs, keywords):
        """
        使用关键字过滤日志
        
        Args:
            parsed_logs: 解析后的日志列表
            keywords: 关键字列表
            
        Returns:
            过滤后的日志列表
        """
        if not keywords:
            return parsed_logs
        
        filtered_logs = []
        
        for log in parsed_logs:
            # 检查日志消息是否包含任何关键字
            message = log['message'].lower()
            component = log['component'].lower()
            
            for keyword in keywords:
                keyword = keyword.lower()
                if keyword in message or keyword in component:
                    filtered_logs.append(log)
                    break
        
        # 如果过滤后的日志太少，可能关键字太严格，返回原始日志
        if len(filtered_logs) < len(parsed_logs) * 0.1 and len(filtered_logs) < 10:
            # 尝试只过滤ERROR和WARN级别的日志
            error_warn_logs = [log for log in parsed_logs if log['level'] in ['ERROR', 'WARN']]
            if error_warn_logs:
                return error_warn_logs
            return parsed_logs
        
        return filtered_logs
    
    def _analyze_logs(self, filtered_logs):
        """
        对过滤后的日志进行时间聚合和异常检测
        
        Args:
            filtered_logs: 过滤后的日志列表
            
        Returns:
            分析后的日志信息
        """
        if not filtered_logs:
            return {}
        
        # 按级别统计日志数量
        level_counts = {}
        for log in filtered_logs:
            level = log['level']
            level_counts[level] = level_counts.get(level, 0) + 1
        
        # 按组件统计日志数量
        component_counts = {}
        for log in filtered_logs:
            component = log['component']
            component_counts[component] = component_counts.get(component, 0) + 1
        
        # 按主机统计日志数量
        host_counts = {}
        for log in filtered_logs:
            host = log['host']
            host_counts[host] = host_counts.get(host, 0) + 1
        
        # 按时间段统计日志数量（每分钟）
        time_series = {}
        for log in filtered_logs:
            # 将时间戳截断到分钟
            minute_key = log['timestamp'].strftime('%Y-%m-%dT%H:%M:00Z')
            if minute_key not in time_series:
                time_series[minute_key] = {'total': 0, 'ERROR': 0, 'WARN': 0, 'INFO': 0, 'DEBUG': 0}
            
            time_series[minute_key]['total'] += 1
            level = log['level']
            if level in time_series[minute_key]:
                time_series[minute_key][level] += 1
        
        # 识别异常时间段（日志突增）
        anomaly_periods = []
        if len(time_series) > 1:
            # 计算每个时间段的日志数量
            time_points = sorted(time_series.keys())
            counts = [time_series[tp]['total'] for tp in time_points]
            
            # 计算平均值和标准差
            avg_count = sum(counts) / len(counts)
            std_count = (sum((c - avg_count) ** 2 for c in counts) / len(counts)) ** 0.5
            
            # 识别异常点（超过平均值+2倍标准差）
            threshold = avg_count + 2 * std_count
            for i, tp in enumerate(time_points):
                if counts[i] > threshold:
                    anomaly_periods.append({
                        'time': tp,
                        'count': counts[i],
                        'expected': avg_count,
                        'deviation': (counts[i] - avg_count) / std_count if std_count > 0 else 0
                    })
        
        # 提取错误和警告日志
        error_logs = [log for log in filtered_logs if log['level'] == 'ERROR']
        warn_logs = [log for log in filtered_logs if log['level'] == 'WARN']
        
        # 构建分析结果
        analysis_result = {
            'total_logs': len(filtered_logs),
            'level_distribution': level_counts,
            'component_distribution': component_counts,
            'host_distribution': host_counts,
            'time_series': time_series,
            'anomaly_periods': anomaly_periods,
            'error_logs': error_logs[:10],  # 只保留前10条错误日志
            'warn_logs': warn_logs[:10],    # 只保留前10条警告日志
            'start_time': filtered_logs[0]['timestamp_str'] if filtered_logs else None,
            'end_time': filtered_logs[-1]['timestamp_str'] if filtered_logs else None
        }
        
        return analysis_result
    
    def _generate_multidimensional_analysis(self, analyzed_logs, incident=None):
        """
        生成类似Splunk SPL的多维度分析结果
        
        Args:
            analyzed_logs: 分析后的日志信息
            incident: 事件信息
            
        Returns:
            多维度分析结果
        """
        if not analyzed_logs or 'total_logs' not in analyzed_logs or analyzed_logs['total_logs'] == 0:
            return []
        
        # 构建分析查询和结果
        analysis_queries = []
        
        # 1. 按时间和级别统计日志数量
        time_level_query = {
            'query_name': '按时间和级别统计日志数量',
            'spl_like': '_index:yotta | timechart count() by level',
            'description': '按时间轴展示不同级别日志的数量分布',
            'result': []
        }
        
        for time_point in sorted(analyzed_logs['time_series'].keys()):
            entry = {'time': time_point}
            for level in ['ERROR', 'WARN', 'INFO', 'DEBUG']:
                entry[level] = analyzed_logs['time_series'][time_point].get(level, 0)
            time_level_query['result'].append(entry)
        
        analysis_queries.append(time_level_query)
        
        # 2. 按组件统计错误日志数量
        component_error_query = {
            'query_name': '按组件统计错误日志数量',
            'spl_like': '_index:yotta level:ERROR | stats count() by component | sort by -count',
            'description': '识别产生最多错误日志的组件',
            'result': []
        }
        
        # 统计每个组件的错误日志数量
        component_errors = {}
        for log in analyzed_logs.get('error_logs', []):
            component = log['component']
            component_errors[component] = component_errors.get(component, 0) + 1
        
        # 按错误数量排序
        sorted_components = sorted(component_errors.items(), key=lambda x: x[1], reverse=True)
        for component, count in sorted_components:
            component_error_query['result'].append({
                'component': component,
                'error_count': count
            })
        
        analysis_queries.append(component_error_query)
        
        # 3. 按主机统计日志级别分布
        host_level_query = {
            'query_name': '按主机统计日志级别分布',
            'spl_like': '_index:yotta | stats count() by hostname, level',
            'description': '分析不同主机的日志级别分布情况',
            'result': []
        }
        
        # 统计每个主机的日志级别分布
        host_levels = {}
        for log in analyzed_logs.get('error_logs', []) + analyzed_logs.get('warn_logs', []):
            host = log['host']
            level = log['level']
            if host not in host_levels:
                host_levels[host] = {'ERROR': 0, 'WARN': 0, 'INFO': 0, 'DEBUG': 0}
            host_levels[host][level] = host_levels[host].get(level, 0) + 1
        
        # 格式化结果
        for host, levels in host_levels.items():
            entry = {'host': host}
            entry.update(levels)
            host_level_query['result'].append(entry)
        
        analysis_queries.append(host_level_query)
        
        # 4. 错误消息模式分析
        error_pattern_query = {
            'query_name': '错误消息模式分析',
            'spl_like': '_index:yotta level:ERROR | parse field=raw_message "(?<error_pattern>.*?)"',
            'description': '提取错误日志中的常见模式',
            'result': []
        }
        
        # 提取错误消息中的关键模式
        error_patterns = {}
        for log in analyzed_logs.get('error_logs', []):
            message = log['message']
            # 简化错误消息，提取关键模式
            # 移除具体的数值、文件名等变量部分
            pattern = re.sub(r'\d+', 'N', message)
            pattern = re.sub(r'/[\w/\.]+', '/PATH', pattern)
            pattern = re.sub(r'\([^)]*\)', '(METRIC)', pattern)
            
            error_patterns[pattern] = error_patterns.get(pattern, 0) + 1
        
        # 按出现频率排序
        sorted_patterns = sorted(error_patterns.items(), key=lambda x: x[1], reverse=True)
        for pattern, count in sorted_patterns:
            error_pattern_query['result'].append({
                'pattern': pattern,
                'count': count
            })
        
        analysis_queries.append(error_pattern_query)
        
        return analysis_queries
        
    def _generate_compressed_representation(self, analyzed_logs, analysis_results, incident=None):
        """
        生成日志数据的压缩表示
        
        Args:
            analyzed_logs: 分析后的日志信息
            analysis_results: 多维度分析结果
            incident: 事件信息
            
        Returns:
            日志数据的压缩表示
        """
        # 构建压缩表示
        compressed = {
            'logs_summary': {
                'total_logs': analyzed_logs.get('total_logs', 0),
                'time_range': self._get_overall_time_range(analyzed_logs),
                'level_distribution': analyzed_logs.get('level_distribution', {}),
                'component_distribution': analyzed_logs.get('component_distribution', {}),
                'host_distribution': analyzed_logs.get('host_distribution', {}),
                'anomaly_periods': analyzed_logs.get('anomaly_periods', [])
            },
            'key_logs': {
                'error_logs': [],
                'warn_logs': []
            },
            'analysis_results': analysis_results
        }
        
        # 添加错误日志摘要
        for log in analyzed_logs.get('error_logs', []):
            compressed['key_logs']['error_logs'].append({
                'timestamp': log['timestamp_str'],
                'component': log['component'],
                'host': log['host'],
                'message': log['message']
            })
        
        # 添加警告日志摘要
        for log in analyzed_logs.get('warn_logs', []):
            compressed['key_logs']['warn_logs'].append({
                'timestamp': log['timestamp_str'],
                'component': log['component'],
                'host': log['host'],
                'message': log['message']
            })
        
        # 如果有事件信息，添加关联分析
        if incident:
            compressed['incident_correlation'] = self._correlate_with_incident(analyzed_logs, incident)
        
        return compressed
    
    def _get_overall_time_range(self, analyzed_logs):
        """
        获取日志的整体时间范围
        
        Args:
            analyzed_logs: 分析后的日志信息
            
        Returns:
            整体时间范围
        """
        start_time = analyzed_logs.get('start_time')
        end_time = analyzed_logs.get('end_time')
        
        if start_time and end_time:
            # 计算持续时间（如果时间格式允许）
            try:
                start_dt = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%SZ')
                end_dt = datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%SZ')
                duration_seconds = (end_dt - start_dt).total_seconds()
                
                return {
                    'start': start_time,
                    'end': end_time,
                    'duration_seconds': duration_seconds,
                    'duration_readable': self._format_duration(duration_seconds)
                }
            except Exception:
                return {
                    'start': start_time,
                    'end': end_time
                }
        
        return {'start': None, 'end': None}
    
    def _format_duration(self, seconds):
        """
        将秒数格式化为可读的持续时间
        
        Args:
            seconds: 持续时间（秒）
            
        Returns:
            格式化后的持续时间字符串
        """
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        
        parts = []
        if days > 0:
            parts.append(f"{int(days)}天")
        if hours > 0:
            parts.append(f"{int(hours)}小时")
        if minutes > 0:
            parts.append(f"{int(minutes)}分钟")
        if seconds > 0 or not parts:
            parts.append(f"{int(seconds)}秒")
        
        return ' '.join(parts)
    
    def _correlate_with_incident(self, analyzed_logs, incident):
        """
        将日志与事件信息进行关联分析
        
        Args:
            analyzed_logs: 分析后的日志信息
            incident: 事件信息
            
        Returns:
            关联分析结果
        """
        # 提取事件的时间范围
        incident_time_range = None
        if isinstance(incident, str):
            try:
                incident_data = json.loads(incident)
            except json.JSONDecodeError:
                incident_data = {"incident": {"title": incident}}
        elif isinstance(incident, dict):
            incident_data = incident
        else:
            return {}
        
        # 尝试从incident中提取时间范围
        if 'time_range' in incident_data:
            try:
                start_str = incident_data['time_range']['start']
                end_str = incident_data['time_range']['end']
                
                # 转换为datetime对象
                start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
                
                incident_time_range = {
                    'start': start_dt,
                    'end': end_dt
                }
            except Exception:
                pass
        
        # 如果无法从incident直接获取时间范围，尝试从incident的其他字段获取
        if not incident_time_range and 'incident' in incident_data:
            if 'detection_time' in incident_data['incident']:
                try:
                    detection_time = incident_data['incident']['detection_time']
                    detection_dt = datetime.fromisoformat(detection_time.replace('Z', '+00:00'))
                    
                    # 假设事件从检测时间前30分钟开始
                    start_dt = detection_dt.replace(minute=detection_dt.minute - 30)
                    end_dt = detection_dt
                    
                    incident_time_range = {
                        'start': start_dt,
                        'end': end_dt
                    }
                except Exception:
                    pass
        
        # 如果仍然无法获取事件时间范围，使用日志的时间范围
        if not incident_time_range:
            if analyzed_logs.get('start_time') and analyzed_logs.get('end_time'):
                try:
                    start_str = analyzed_logs['start_time']
                    end_str = analyzed_logs['end_time']
                    
                    start_dt = datetime.strptime(start_str, '%Y-%m-%dT%H:%M:%SZ')
                    end_dt = datetime.strptime(end_str, '%Y-%m-%dT%H:%M:%SZ')
                    
                    incident_time_range = {
                        'start': start_dt,
                        'end': end_dt
                    }
                except Exception:
                    return {}
            else:
                return {}
        
        # 分析日志在事件时间范围内的行为
        correlation_results = {
            'logs_in_incident_period': [],
            'error_logs_in_period': [],
            'warn_logs_in_period': [],
            'affected_components': set(),
            'affected_hosts': set(),
            'potential_causes': []
        }
        
        # 提取事件期间的错误和警告日志
        for log in analyzed_logs.get('error_logs', []) + analyzed_logs.get('warn_logs', []):
            log_dt = log['timestamp']
            
            # 检查日志时间是否在事件时间范围内
            if incident_time_range['start'] <= log_dt <= incident_time_range['end']:
                log_summary = {
                    'timestamp': log['timestamp_str'],
                    'level': log['level'],
                    'component': log['component'],
                    'host': log['host'],
                    'message': log['message']
                }
                
                correlation_results['logs_in_incident_period'].append(log_summary)
                
                # 分类错误和警告日志
                if log['level'] == 'ERROR':
                    correlation_results['error_logs_in_period'].append(log_summary)
                elif log['level'] == 'WARN':
                    correlation_results['warn_logs_in_period'].append(log_summary)
                
                # 记录受影响的组件和主机
                correlation_results['affected_components'].add(log['component'])
                correlation_results['affected_hosts'].add(log['host'])
                
                # 如果日志时间早于事件开始时间的前5分钟，可能是潜在原因
                if log_dt < incident_time_range['start'] and (incident_time_range['start'] - log_dt).total_seconds() < 300:
                    correlation_results['potential_causes'].append({
                        'timestamp': log['timestamp_str'],
                        'level': log['level'],
                        'component': log['component'],
                        'host': log['host'],
                        'message': log['message'],
                        'time_before_incident': (incident_time_range['start'] - log_dt).total_seconds()
                    })
        
        # 转换集合为列表
        correlation_results['affected_components'] = list(correlation_results['affected_components'])
        correlation_results['affected_hosts'] = list(correlation_results['affected_hosts'])
        
        # 按时间排序
        correlation_results['logs_in_incident_period'].sort(key=lambda x: x['timestamp'])
        correlation_results['error_logs_in_period'].sort(key=lambda x: x['timestamp'])
        correlation_results['warn_logs_in_period'].sort(key=lambda x: x['timestamp'])
        
        # 按接近事件开始时间的顺序排序潜在原因
        if correlation_results['potential_causes']:
            correlation_results['potential_causes'].sort(key=lambda x: x['time_before_incident'])
        
        return correlation_results