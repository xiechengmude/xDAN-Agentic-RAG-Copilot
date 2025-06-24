#!/usr/bin/env python3
"""
端口管理工具
自动处理端口占用问题
"""

import socket
import subprocess
import platform
import logging
import time
from typing import Optional, List

logger = logging.getLogger(__name__)

class PortManager:
    """端口管理器"""
    
    @staticmethod
    def is_port_in_use(port: int, host: str = '127.0.0.1') -> bool:
        """检查端口是否被占用"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, port))
                return False
            except socket.error:
                return True
    
    @staticmethod
    def find_process_using_port(port: int) -> Optional[List[str]]:
        """查找占用端口的进程信息"""
        system = platform.system()
        
        try:
            if system == "Darwin":  # macOS
                # 使用lsof命令
                result = subprocess.run(
                    ['lsof', '-i', f':{port}'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')[1:]  # 跳过标题行
                    return lines
            elif system == "Linux":
                # 使用lsof或netstat
                result = subprocess.run(
                    ['lsof', '-i', f':{port}'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')[1:]
                    return lines
            elif system == "Windows":
                # 使用netstat
                result = subprocess.run(
                    ['netstat', '-ano'],
                    capture_output=True,
                    text=True,
                    shell=True
                )
                if result.returncode == 0:
                    lines = []
                    for line in result.stdout.split('\n'):
                        if f':{port}' in line:
                            lines.append(line.strip())
                    return lines
        except Exception as e:
            logger.error(f"查找进程失败: {e}")
        
        return None
    
    @staticmethod
    def kill_process_on_port(port: int) -> bool:
        """终止占用端口的进程"""
        system = platform.system()
        
        try:
            if system in ["Darwin", "Linux"]:
                # 获取PID
                result = subprocess.run(
                    ['lsof', '-ti', f':{port}'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0 and result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    for pid in pids:
                        try:
                            subprocess.run(['kill', '-9', pid], check=True)
                            logger.info(f"已终止进程 PID: {pid}")
                        except subprocess.CalledProcessError:
                            logger.error(f"无法终止进程 PID: {pid}")
                            return False
                    return True
            elif system == "Windows":
                # Windows需要使用taskkill
                result = subprocess.run(
                    f'for /f "tokens=5" %a in (\'netstat -ano ^| findstr :{port}\') do taskkill /PID %a /F',
                    shell=True,
                    capture_output=True
                )
                return result.returncode == 0
        except Exception as e:
            logger.error(f"终止进程失败: {e}")
        
        return False
    
    @staticmethod
    def ensure_port_available(port: int, timeout: int = 10) -> bool:
        """
        确保端口可用
        
        Args:
            port: 端口号
            timeout: 等待超时时间（秒）
            
        Returns:
            端口是否可用
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if not PortManager.is_port_in_use(port):
                return True
            
            # 尝试查找并显示占用端口的进程
            processes = PortManager.find_process_using_port(port)
            if processes:
                logger.warning(f"端口 {port} 被以下进程占用:")
                for process in processes:
                    logger.warning(f"  {process}")
                
                # 询问是否终止进程（在自动化环境中跳过）
                if logger.level <= logging.INFO:
                    logger.info(f"尝试自动终止占用端口 {port} 的进程...")
                    if PortManager.kill_process_on_port(port):
                        time.sleep(1)  # 等待进程完全退出
                        if not PortManager.is_port_in_use(port):
                            logger.info(f"端口 {port} 已释放")
                            return True
            
            time.sleep(1)
        
        return False
    
    @staticmethod
    def find_free_port(start_port: int = 8000, end_port: int = 9000) -> Optional[int]:
        """
        查找可用的端口
        
        Args:
            start_port: 起始端口
            end_port: 结束端口
            
        Returns:
            可用的端口号，如果没有找到返回None
        """
        for port in range(start_port, end_port):
            if not PortManager.is_port_in_use(port):
                return port
        return None

# 便捷函数
def ensure_port_free(port: int, auto_kill: bool = True) -> bool:
    """
    确保端口空闲
    
    Args:
        port: 端口号
        auto_kill: 是否自动终止占用进程
        
    Returns:
        端口是否空闲
    """
    if not PortManager.is_port_in_use(port):
        return True
    
    logger.warning(f"端口 {port} 已被占用")
    
    if auto_kill:
        logger.info(f"尝试释放端口 {port}...")
        return PortManager.ensure_port_available(port)
    
    return False