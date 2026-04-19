"""
仪表盘分析引擎 - 执行聚合查询和数据统计
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from app.models.workflow import Template


class AnalyticsEngine:
    """分析引擎 - 执行各类聚合查询"""

    @staticmethod
    async def execute_aggregation(
        db: AsyncSession,
        config: Dict[str, Any],
        user_id: int = None
    ) -> Dict[str, Any]:
        """
        执行聚合查询
        config格式:
        {
            "type": "aggregation" | "grouped_aggregation" | "query",
            "template_id": 123,
            "aggregate": "count" | "sum" | "avg" | "max" | "min",
            "field": "amount",
            "filters": [{"field": "status", "op": "=", "value": "active"}],
            "group_by": "category",
            "date_range": "today" | "week" | "month" | "year"
        }
        """
        template_id = config.get("template_id")
        if not template_id:
            return {"error": "template_id is required"}

        # 获取表名
        result = await db.execute(
            text("SELECT config FROM templates WHERE id = :tid"),
            {"tid": template_id}
        )
        row = result.fetchone()
        if not row:
            return {"error": f"Template {template_id} not found"}

        tpl_config = row[0] or {}
        table_name = tpl_config.get("table_name", f"form_data_{template_id}")

        # 安全检查：表名必须以 form_data_ 开头
        if not table_name.startswith("form_data_"):
            return {"error": "Invalid table name"}

        # 构建 WHERE 子句
        where_clause, params = AnalyticsEngine._build_where_clause(config)

        # 执行聚合
        source_type = config.get("type", "aggregation")

        if source_type == "aggregation":
            return await AnalyticsEngine._do_aggregation(db, table_name, config, where_clause, params)
        elif source_type == "grouped_aggregation":
            return await AnalyticsEngine._do_grouped_aggregation(db, table_name, config, where_clause, params)
        elif source_type == "query":
            return await AnalyticsEngine._do_query(db, table_name, config, where_clause, params)
        else:
            return {"error": f"Unknown aggregation type: {source_type}"}

    @staticmethod
    def _build_where_clause(config: Dict[str, Any]) -> tuple:
        """构建WHERE子句"""
        where_parts = []
        params = {}

        # 日期范围
        date_range = config.get("date_range")
        date_field = config.get("date_field", "created_at")
        if date_range:
            now = datetime.now()
            if date_range == "today":
                start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                where_parts.append(f"{date_field} >= :dr_start AND {date_field} < :dr_end")
                params["dr_start"] = start
                params["dr_end"] = start + timedelta(days=1)
            elif date_range == "week":
                start = now - timedelta(days=7)
                where_parts.append(f"{date_field} >= :dr_start")
                params["dr_start"] = start
            elif date_range == "month":
                start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                where_parts.append(f"{date_field} >= :dr_start")
                params["dr_start"] = start
            elif date_range == "year":
                start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                where_parts.append(f"{date_field} >= :dr_start")
                params["dr_start"] = start

        # 自定义过滤器
        filters = config.get("filters", [])
        for i, f in enumerate(filters):
            field = f.get("field", "")
            op = f.get("op", "=")
            value = f.get("value", "")
            key = f"f{i}"

            if op == "=":
                where_parts.append(f"{field} = :{key}")
                params[key] = value
            elif op == ">":
                where_parts.append(f"{field} > :{key}")
                params[key] = value
            elif op == "<":
                where_parts.append(f"{field} < :{key}")
                params[key] = value
            elif op == ">=":
                where_parts.append(f"{field} >= :{key}")
                params[key] = value
            elif op == "<=":
                where_parts.append(f"{field} <= :{key}")
                params[key] = value
            elif op == "like":
                where_parts.append(f"{field} LIKE :{key}")
                params[key] = f"%{value}%"
            elif op == "in":
                if isinstance(value, list) and value:
                    placeholders = [f":{key}_{j}" for j in range(len(value))]
                    where_parts.append(f"{field} IN ({','.join(placeholders)})")
                    for j, v in enumerate(value):
                        params[f"{key}_{j}"] = v

        where_clause = " AND ".join(where_parts) if where_parts else "1=1"
        return where_clause, params

    @staticmethod
    async def _do_aggregation(
        db: AsyncSession,
        table_name: str,
        config: Dict[str, Any],
        where_clause: str,
        params: dict
    ) -> Dict[str, Any]:
        """执行单值聚合"""
        aggregate = config.get("aggregate", "count")
        field = config.get("field", "id")

        if aggregate == "count":
            select_expr = f"COUNT({field}) as value"
        elif aggregate == "sum":
            select_expr = f"SUM(CAST({field} AS REAL)) as value"
        elif aggregate == "avg":
            select_expr = f"AVG(CAST({field} AS REAL)) as value"
        elif aggregate == "max":
            select_expr = f"MAX({field}) as value"
        elif aggregate == "min":
            select_expr = f"MIN({field}) as value"
        else:
            select_expr = "COUNT(*) as value"

        sql = f"SELECT {select_expr} FROM {table_name} WHERE {where_clause}"
        result = await db.execute(text(sql), params)
        row = result.fetchone()

        value = row[0] if row else 0
        if value is None:
            value = 0

        return {
            "type": "single",
            "aggregate": aggregate,
            "value": value
        }

    @staticmethod
    async def _do_grouped_aggregation(
        db: AsyncSession,
        table_name: str,
        config: Dict[str, Any],
        where_clause: str,
        params: dict
    ) -> Dict[str, Any]:
        """执行分组聚合"""
        group_by = config.get("group_by")
        if not group_by:
            return await AnalyticsEngine._do_aggregation(db, table_name, config, where_clause, params)

        aggregate = config.get("aggregate", "count")
        field = config.get("field", "id")

        if aggregate == "count":
            select_expr = f"COUNT({field}) as value"
        elif aggregate == "sum":
            select_expr = f"SUM(CAST({field} AS REAL)) as value"
        elif aggregate == "avg":
            select_expr = f"AVG(CAST({field} AS REAL)) as value"
        elif aggregate == "max":
            select_expr = f"MAX({field}) as value"
        elif aggregate == "min":
            select_expr = f"MIN({field}) as value"
        else:
            select_expr = "COUNT(*) as value"

        sql = f"""
            SELECT {group_by} as name, {select_expr}
            FROM {table_name}
            WHERE {where_clause}
            GROUP BY {group_by}
            ORDER BY value DESC
            LIMIT 20
        """

        result = await db.execute(text(sql), params)
        rows = result.fetchall()

        data = [{"name": r[0] or "(空)", "value": r[1] or 0} for r in rows]
        total = sum(item["value"] for item in data)

        return {
            "type": "grouped",
            "aggregate": aggregate,
            "group_by": group_by,
            "data": data,
            "total": total
        }

    @staticmethod
    async def _do_query(
        db: AsyncSession,
        table_name: str,
        config: Dict[str, Any],
        where_clause: str,
        params: dict
    ) -> Dict[str, Any]:
        """执行列表查询"""
        order_by = config.get("order_by", "-created_at")
        if order_by.startswith("-"):
            order_clause = f"ORDER BY {order_by[1:]} DESC"
        else:
            order_clause = f"ORDER BY {order_by} ASC"

        limit = min(config.get("limit", 10), 100)

        sql = f"""
            SELECT * FROM {table_name}
            WHERE {where_clause}
            {order_clause}
            LIMIT :limit
        """
        params["limit"] = limit

        result = await db.execute(text(sql), params)
        rows = result.fetchall()
        columns = result.keys()

        data = [dict(zip(columns, row)) for row in rows]

        return {
            "type": "query",
            "data": data,
            "count": len(data)
        }


# 全局实例
analytics_engine = AnalyticsEngine()
