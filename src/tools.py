from datetime import datetime, timedelta, timezone

TZ_UTC8 = timezone(timedelta(hours=8))

def assert_timezone_aware(dt: datetime) -> None:
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise ValueError("dt must be timezone-aware")

def assert_china_time(dt: datetime) -> None:
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) != TZ_UTC8.utcoffset(dt):
        raise ValueError("dt must be Shanghai time (UTC+8)")


# def utc_to_shanghai_time(utc_time: datetime) -> str:
#     """
#     将 UTC 时间转换为上海时间（UTC+8），返回带 +08:00 的字符串。

#     参数:
#         utc_time (datetime): UTC 时间，带时区信息的 datetime 对象
#     返回:
#         str: 上海时间的 ISO 格式字符串，例如 "2025-04-05T14:00:00+08:00"
#     """
#     # 定义 UTC+8 的时区
#     assert_timezone_aware(utc_time)

#     # 转换为上海时间
#     shanghai_time = utc_time.astimezone(TZ_UTC8)

#     # 返回 ISO 格式字符串
#     return shanghai_time.isoformat()
