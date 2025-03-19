import json
import os
import logging

logger = logging.getLogger(__name__)

def apply_consistency_corrections(consistency_report, incident_data, metrics_data, logs_data, events_data, analysis_data, incident_id, output_dir):
    """
    应用一致性检查报告中的修正建议到相应的数据
    
    :param consistency_report: 一致性检查报告（JSON字符串）
    :param incident_data: 原始事件数据
    :param metrics_data: 原始指标数据
    :param logs_data: 原始日志数据
    :param events_data: 原始事件序列数据
    :param analysis_data: 原始分析数据
    :param incident_id: 事件ID
    :param output_dir: 输出目录
    :return: 修正后的数据字典 {"incident": ..., "metrics": ..., "logs": ..., "events": ..., "analysis": ...}
    """
    logger.info(f"开始应用一致性修正到事件 {incident_id}")
    
    # 解析一致性报告
    try:
        report = json.loads(consistency_report)
    except json.JSONDecodeError:
        logger.error("一致性报告解析失败，无法应用修正")
        return {
            "incident": incident_data,
            "metrics": metrics_data,
            "logs": logs_data,
            "events": events_data,
            "analysis": analysis_data
        }
    
    # 初始化修正后的数据
    corrected_data = {
        "incident": incident_data,
        "metrics": metrics_data,
        "logs": logs_data,
        "events": events_data,
        "analysis": analysis_data
    }
    
    # 应用诊断修正
    if "diagnostics" in report and isinstance(report["diagnostics"], list):
        for diagnostic in report["diagnostics"]:
            source_location = diagnostic.get("source_location", "")
            corrected_content = diagnostic.get("corrected_content", "")
            
            if not source_location or not corrected_content:
                continue
                
            # 根据source_location确定要修改的数据类型
            if "incident_data" in source_location:
                # 如果是JSON格式的数据，尝试解析并更新
                try:
                    corrected_data["incident"] = json.loads(corrected_content)
                    logger.info(f"已更新事件数据: {incident_id}")
                except json.JSONDecodeError:
                    logger.warning(f"无法解析修正后的事件数据: {incident_id}")
            
            elif "metrics_data" in source_location:
                # 指标数据通常是文本格式
                corrected_data["metrics"] = corrected_content
                logger.info(f"已更新指标数据: {incident_id}")
            
            elif "logs_data" in source_location:
                # 日志数据通常是文本格式
                corrected_data["logs"] = corrected_content
                logger.info(f"已更新日志数据: {incident_id}")
            
            elif "events_data" in source_location:
                # 事件序列通常是JSON格式
                try:
                    corrected_data["events"] = json.loads(corrected_content)
                    logger.info(f"已更新事件序列数据: {incident_id}")
                except json.JSONDecodeError:
                    logger.warning(f"无法解析修正后的事件序列数据: {incident_id}")
            
            elif "analysis_data" in source_location:
                # 分析数据通常是JSON格式
                try:
                    corrected_data["analysis"] = json.loads(corrected_content)
                    logger.info(f"已更新分析数据: {incident_id}")
                except json.JSONDecodeError:
                    logger.warning(f"无法解析修正后的分析数据: {incident_id}")
    
    # 应用整体修正
    if "corrected_incident" in report and report["corrected_incident"]:
        try:
            corrected_data["incident"] = json.loads(report["corrected_incident"])
            logger.info(f"已应用整体事件修正: {incident_id}")
        except (json.JSONDecodeError, TypeError):
            # 如果不是JSON格式，可能是文本描述
            logger.info(f"整体事件修正不是JSON格式，跳过应用: {incident_id}")
    
    if "enhanced_analysis" in report and report["enhanced_analysis"]:
        try:
            corrected_data["analysis"] = json.loads(report["enhanced_analysis"])
            logger.info(f"已应用增强分析: {incident_id}")
        except (json.JSONDecodeError, TypeError):
            # 如果不是JSON格式，可能是文本描述
            logger.info(f"增强分析不是JSON格式，跳过应用: {incident_id}")
    
    # 保存修正后的数据
    save_corrected_data(corrected_data, incident_id, output_dir)
    
    return corrected_data

def save_corrected_data(corrected_data, incident_id, output_dir):
    """
    保存修正后的数据到文件
    
    :param corrected_data: 修正后的数据字典
    :param incident_id: 事件ID
    :param output_dir: 输出目录
    """
    incident_dir = os.path.join(output_dir, f'incident_{incident_id}')
    os.makedirs(incident_dir, exist_ok=True)
    
    # 保存修正后的事件数据
    with open(os.path.join(incident_dir, 'incident_corrected.json'), 'w', encoding='utf-8') as f:
        json.dump(corrected_data["incident"], f, indent=2, ensure_ascii=False)
    
    # 保存修正后的指标数据
    with open(os.path.join(incident_dir, 'metrics_corrected.txt'), 'w', encoding='utf-8') as f:
        f.write(corrected_data["metrics"])
    
    # 保存修正后的日志数据
    with open(os.path.join(incident_dir, 'logs_corrected.txt'), 'w', encoding='utf-8') as f:
        f.write(corrected_data["logs"])
    
    # 保存修正后的事件序列数据
    with open(os.path.join(incident_dir, 'events_corrected.json'), 'w', encoding='utf-8') as f:
        json.dump(corrected_data["events"], f, indent=2, ensure_ascii=False)
    
    # 保存修正后的分析数据
    with open(os.path.join(incident_dir, 'analysis_corrected.json'), 'w', encoding='utf-8') as f:
        json.dump(corrected_data["analysis"], f, indent=2, ensure_ascii=False)
    
    logger.info(f"已保存修正后的数据到 {incident_dir}")