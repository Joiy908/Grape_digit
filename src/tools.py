from datetime import datetime, timedelta, timezone


def utc_to_shanghai_time(utc_time: datetime) -> str:
    """
    将 UTC 时间转换为上海时间（UTC+8），返回带 +08:00 的字符串。

    参数:
        utc_time (datetime): UTC 时间，带时区信息的 datetime 对象
    返回:
        str: 上海时间的 ISO 格式字符串，例如 "2025-04-05T14:00:00+08:00"
    """
    # 定义 UTC+8 的时区
    shanghai_offset = timezone(timedelta(hours=8))

    # 确保输入是 UTC 时间，如果没有时区信息则假设为 UTC
    if utc_time.tzinfo is None:
        utc_time = utc_time.replace(tzinfo=timezone.utc)

    # 转换为上海时间
    shanghai_time = utc_time.astimezone(shanghai_offset)

    # 返回 ISO 格式字符串
    return shanghai_time.isoformat()
