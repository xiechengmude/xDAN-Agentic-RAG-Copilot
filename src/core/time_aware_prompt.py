"""
时间感知提示类
提供时间相关的上下文信息
"""

import datetime
from typing import Dict


class TimeAwarePrompt:
    """时间感知提示类"""
    
    def __init__(self):
        self.now = datetime.datetime.now()
    
    def get_current_time_info(self) -> Dict[str, str]:
        """获取当前时间信息"""
        # 北京时间
        beijing_tz = datetime.timezone(datetime.timedelta(hours=8))
        beijing_time = self.now.astimezone(beijing_tz)
        
        # 计算本周和本月范围
        weekday = beijing_time.weekday()
        week_start = beijing_time - datetime.timedelta(days=weekday)
        week_end = week_start + datetime.timedelta(days=6)
        
        month_start = beijing_time.replace(day=1)
        if beijing_time.month == 12:
            month_end = beijing_time.replace(year=beijing_time.year + 1, month=1, day=1) - datetime.timedelta(days=1)
        else:
            month_end = beijing_time.replace(month=beijing_time.month + 1, day=1) - datetime.timedelta(days=1)
        
        # 市场状态判断
        hour = beijing_time.hour
        if 9 <= hour < 15:
            market_status = "交易时间"
        elif 15 <= hour < 20:
            market_status = "盘后时间"
        else:
            market_status = "休市时间"
        
        # 星期中文
        weekdays_cn = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        weekday_cn = weekdays_cn[weekday]
        
        return {
            "beijing_time": beijing_time.strftime("%Y-%m-%d %H:%M:%S"),
            "current_date": beijing_time.strftime("%Y-%m-%d"),
            "weekday_cn": weekday_cn,
            "week_start": week_start.strftime("%Y-%m-%d"),
            "week_end": week_end.strftime("%Y-%m-%d"),
            "month_start": month_start.strftime("%Y-%m-%d"),
            "month_end": month_end.strftime("%Y-%m-%d"),
            "market_status": market_status
        }