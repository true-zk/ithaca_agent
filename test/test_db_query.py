#!/usr/bin/env python3
"""
高级查询函数使用示例

展示如何使用 IthacaDB.advanced_query() 进行复杂的数据库查询
"""

from datetime import datetime, timedelta
from ithaca.db.utils import IthacaDB
from ithaca.db.history import HistoryModel


def example_queries():
    """演示各种高级查询用法"""
    
    print("=== 高级查询函数使用示例 ===\n")
    
    # 1. 查询最近5条记录
    print("1. 查询最近5条记录:")
    recent_records = IthacaDB.advanced_query(
        HistoryModel, 
        order_by="created_at", 
        order_desc=True, 
        limit=5
    )
    print(f"   找到 {len(recent_records)} 条记录")
    for record in recent_records:
        print(f"   - {record.product_name} (创建时间: {record.created_at})")
    print()
    
    # 2. 查询最近7天内的记录
    print("2. 查询最近7天内的记录:")
    week_records = IthacaDB.advanced_query(
        HistoryModel,
        time_filters={"created_at_within": timedelta(days=7)},
        order_by="created_at",
        order_desc=True
    )
    print(f"   最近7天内有 {len(week_records)} 条记录")
    print()
    
    # 3. 查询指定时间之后的记录
    print("3. 查询2024年1月1日之后的记录:")
    after_date_records = IthacaDB.advanced_query(
        HistoryModel,
        time_filters={"created_at_after": datetime(2024, 1, 1)},
        order_by="created_at",
        order_desc=True
    )
    print(f"   2024年1月1日之后有 {len(after_date_records)} 条记录")
    print()
    
    # 4. 查询评分大于等于8.0的记录
    print("4. 查询评分 >= 8.0 的记录:")
    high_score_records = IthacaDB.advanced_query(
        HistoryModel,
        filters={"plan_score": {">=": 8.0}},
        order_by="plan_score",
        order_desc=True
    )
    print(f"   评分 >= 8.0 的记录有 {len(high_score_records)} 条")
    for record in high_score_records:
        if record.plan_score is not None:
            print(f"   - {record.product_name}: {record.plan_score}")
    print()
    
    # 5. 复杂条件查询：评分大于8.0 OR 最近3天内的记录
    print("5. 复杂查询 (评分 >= 8.0 OR 最近3天内):")
    complex_records = IthacaDB.advanced_query(
        HistoryModel,
        filters={"plan_score": {">=": 8.0}},
        time_filters={"created_at_within": timedelta(days=3)},
        logical_operator="or",
        order_by="created_at",
        order_desc=True
    )
    print(f"   符合条件的记录有 {len(complex_records)} 条")
    print()
    
    # 6. 分页查询：跳过前5条，获取接下来的3条
    print("6. 分页查询 (跳过前5条，获取接下来3条):")
    paginated_records = IthacaDB.advanced_query(
        HistoryModel,
        order_by="created_at",
        order_desc=True,
        offset=5,
        limit=3
    )
    print(f"   分页结果: {len(paginated_records)} 条记录")
    print()
    
    # 7. 模糊查询：产品名包含特定关键词
    print("7. 模糊查询 (产品名包含 'phone'):")
    like_records = IthacaDB.advanced_query(
        HistoryModel,
        filters={"product_name": {"like": "%phone%"}},
        order_by="created_at",
        order_desc=True
    )
    print(f"   包含 'phone' 的产品有 {len(like_records)} 条")
    print()
    
    # 8. 多条件AND查询：指定产品且评分大于某值
    print("8. 多条件AND查询:")
    multi_and_records = IthacaDB.advanced_query(
        HistoryModel,
        filters={
            "plan_score": {">": 7.0}
        },
        time_filters={"created_at_within": timedelta(days=30)},
        logical_operator="and",  # 默认就是and
        order_by="plan_score",
        order_desc=True,
        limit=10
    )
    print(f"   最近30天内评分>7.0的记录: {len(multi_and_records)} 条")
    print()


def query_recent_by_product(product_name: str, days: int = 7, limit: int = 5):
    """
    查询指定产品最近几天的记录
    
    Args:
        product_name: 产品名称
        days: 天数
        limit: 限制条数
    """
    print(f"查询产品 '{product_name}' 最近 {days} 天的 {limit} 条记录:")
    
    records = IthacaDB.advanced_query(
        HistoryModel,
        filters={"product_name": product_name},
        time_filters={"created_at_within": timedelta(days=days)},
        order_by="created_at",
        order_desc=True,
        limit=limit
    )
    
    if records:
        for i, record in enumerate(records, 1):
            print(f"  {i}. 计划ID: {record.plan_id}")
            print(f"     评分: {record.plan_score}")
            print(f"     创建时间: {record.created_at}")
            print(f"     描述: {record.plan_description}")
            print()
    else:
        print(f"  没有找到产品 '{product_name}' 最近 {days} 天的记录")


def get_top_scored_plans(limit: int = 10):
    """获取评分最高的计划"""
    print(f"获取评分最高的 {limit} 个计划:")
    
    records = IthacaDB.advanced_query(
        HistoryModel,
        filters={"plan_score": {"!=": None}},  # 排除空评分
        order_by="plan_score",
        order_desc=True,
        limit=limit
    )
    
    if records:
        for i, record in enumerate(records, 1):
            print(f"  {i}. {record.product_name} - 评分: {record.plan_score}")
            print(f"     计划: {record.plan_description}")
            print()
    else:
        print("  没有找到有评分的记录")


if __name__ == "__main__":
    # 运行示例查询
    example_queries()
    
    # 演示特定用途的查询函数
    print("\n=== 特定用途查询示例 ===\n")
    
    # 查询特定产品的最近记录
    query_recent_by_product("iPhone", days=30, limit=3)
    
    # 获取评分最高的计划
    get_top_scored_plans(limit=5)
