"""
业务服务 - 决策分析服务
智能洞察引擎
"""
from typing import Dict, Any, List, Optional
import json
from datetime import datetime, timedelta

from app.core.ai_digital_base.inference import inference_service


class AnalyticsService:
    """决策分析服务 - 智能洞察"""
    
    # 图表配置模板
    CHART_CONFIGS = {
        "line": {
            "type": "line",
            "title": "趋势图",
            "xAxis": {"type": "category"},
            "yAxis": {"type": "value"}
        },
        "bar": {
            "type": "bar",
            "title": "柱状图",
            "xAxis": {"type": "category"},
            "yAxis": {"type": "value"}
        },
        "pie": {
            "type": "pie",
            "title": "饼图",
            "radius": ["30%", "70%"]
        },
        "scatter": {
            "type": "scatter",
            "title": "散点图",
            "xAxis": {"type": "value"},
            "yAxis": {"type": "value"}
        },
        "gauge": {
            "type": "gauge",
            "title": "仪表盘",
            "min": 0,
            "max": 100
        },
        "radar": {
            "type": "radar",
            "title": "雷达图",
            "shape": "polygon"
        }
    }
    
    # 指标计算公式
    METRIC_FORMULAS = {
        "total": "SUM({field})",
        "average": "AVG({field})",
        "max": "MAX({field})",
        "min": "MIN({field})",
        "count": "COUNT(*)",
        "growth_rate": "(current - previous) / previous * 100",
        "yoy_growth": "(current_year - last_year) / last_year * 100",
        "running_total": "SUM({field}) OVER (ORDER BY date)"
    }
    
    @classmethod
    async def query_data(
        cls,
        query: str,
        data_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """自然语言数据查询"""
        # AI解析查询意图
        result = await inference_service.analyze_data(query, str(data_context))
        
        return {
            "sql": result.get("sql", ""),
            "explanation": result.get("explanation", ""),
            "data": result.get("data", [])
        }
    
    @classmethod
    async def generate_chart_config(
        cls,
        query: str,
        data_description: str
    ) -> Dict[str, Any]:
        """生成图表配置"""
        # AI推荐图表类型
        result = await inference_service.generate_chart_config(query, data_description)
        
        if "error" not in result:
            return result
        
        # 默认返回折线图配置
        return {
            "chart_type": "line",
            "title": "数据趋势",
            "x_axis": "日期",
            "y_axis": ["数值"],
            "config": cls.CHART_CONFIGS["line"]
        }
    
    @classmethod
    async def generate_insight_report(
        cls,
        data: Dict[str, Any],
        report_type: str = "general"
    ) -> Dict[str, Any]:
        """生成洞察报告"""
        prompts = {
            "trend": "趋势分析：识别数据中的趋势、季节性和周期性模式",
            "anomaly": "异常检测：发现数据中的异常值和离群点",
            "correlation": "相关性分析：找出变量之间的关联关系",
            "forecast": "预测分析：基于历史数据预测未来趋势",
            "comparison": "对比分析：比较不同维度或时间段的差异",
            "general": "综合分析：提供数据的关键发现和洞察"
        }
        
        system_prompt = f"""你是一个数据分析专家。进行{prompts.get(report_type, prompts['general'])}。

分析提供的数据，提供：
1. **关键发现**：最重要的3-5个发现
2. **数据摘要**：核心指标的统计信息
3. **异常情况**：如有异常值，详细说明
4. **建议行动**：基于数据的建议

输出JSON格式：
{{
    "key_findings": ["发现1", "发现2", ...],
    "summary": {{
        "total": 数值,
        "average": 数值,
        "max": 数值,
        "min": 数值,
        "trend": "上升/下降/稳定"
    }},
    "anomalies": ["异常1", ...],
    "recommendations": ["建议1", ...]
}}"""
        
        from app.core.ai_digital_base.gateway import ai_gateway
        
        result = await ai_gateway.chat_with_system_prompt(
            system_prompt=system_prompt,
            user_message=f"分析数据：\n{json.dumps(data, ensure_ascii=False, indent=2)}"
        )
        
        if "error" in result:
            return {"error": result["error"]}
        
        try:
            content = result["content"].strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            return json.loads(content)
        except:
            return {"report": result["content"]}
    
    @classmethod
    async def predict_trend(
        cls,
        historical_data: List[Dict[str, Any]],
        metric: str,
        periods: int = 3
    ) -> Dict[str, Any]:
        """预测趋势"""
        if len(historical_data) < 3:
            return {"error": "数据不足，至少需要3个历史数据点"}
        
        # 简单移动平均预测
        values = [d.get(metric, 0) for d in historical_data]
        
        # 计算移动平均
        window = min(3, len(values))
        ma = sum(values[-window:]) / window
        
        # 计算趋势
        if len(values) >= 2:
            trend = (values[-1] - values[0]) / len(values)
        else:
            trend = 0
        
        # 生成预测
        predictions = []
        last_value = values[-1]
        for i in range(1, periods + 1):
            pred_value = last_value + trend * i
            predictions.append({
                "period": i,
                "value": round(pred_value, 2),
                "confidence": max(0.5, 1 - (i * 0.1))
            })
        
        return {
            "metric": metric,
            "current_value": last_value,
            "trend": "上升" if trend > 0 else "下降" if trend < 0 else "稳定",
            "trend_value": round(trend, 2),
            "predictions": predictions,
            "method": "移动平均法"
        }
    
    @classmethod
    def calculate_metrics(
        cls,
        data: List[Dict[str, Any]],
        metrics: List[str],
        group_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """计算指标"""
        if not data:
            return {"error": "没有数据"}
        
        result = {}
        
        for metric in metrics:
            values = [d.get(metric, 0) for d in data if metric in d]
            if not values:
                continue
            
            result[metric] = {
                "total": round(sum(values), 2),
                "average": round(sum(values) / len(values), 2),
                "max": max(values),
                "min": min(values),
                "count": len(values)
            }
        
        if group_by:
            grouped = {}
            for item in data:
                key = item.get(group_by, "unknown")
                if key not in grouped:
                    grouped[key] = []
                grouped[key].append(item)
            
            result["grouped"] = {
                k: cls.calculate_metrics(v, metrics)
                for k, v in grouped.items()
            }
        
        return result
    
    @classmethod
    def get_dashboard_widgets(cls) -> List[Dict[str, Any]]:
        """获取仪表盘组件配置"""
        return [
            {
                "id": "kpi_cards",
                "name": "KPI卡片",
                "type": "kpi",
                "config": {
                    "metrics": ["销售额", "订单数", "客户数", "转化率"]
                }
            },
            {
                "id": "trend_chart",
                "name": "趋势图",
                "type": "line",
                "config": {
                    "xAxis": "日期",
                    "yAxis": ["销售额"],
                    "period": "最近30天"
                }
            },
            {
                "id": "region_pie",
                "name": "地区分布",
                "type": "pie",
                "config": {
                    "dimension": "地区",
                    "metric": "销售额"
                }
            },
            {
                "id": "top_products",
                "name": "TOP产品",
                "type": "bar",
                "config": {
                    "dimension": "产品",
                    "metric": "销量",
                    "limit": 10
                }
            },
            {
                "id": "funnel",
                "name": "漏斗图",
                "type": "funnel",
                "config": {
                    "steps": ["访问", "注册", "下单", "支付"]
                }
            }
        ]


analytics_service = AnalyticsService()
