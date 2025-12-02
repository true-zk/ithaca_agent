"""
Simple scheduler for looping workflow or agent
支持后台运行和命令行控制
"""
import time
import signal
import sys
import os
import json
import threading
import socket
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
import fcntl
import atexit

from ithaca.workflow.base import BaseWorkFlow
from ithaca.logger import logger


class SimpleScheduler:
    """
    简单调度器 - 支持后台运行和命令行控制
    """
    
    def __init__(
        self,
        workflow: BaseWorkFlow,
        interval_seconds: int = 3600,  # 默认1小时
        name: str = "scheduler"
    ):
        self.workflow = workflow
        self.interval_seconds = interval_seconds
        self.name = name
        
        # 状态管理
        self.running = False
        self.paused = False
        self.step_count = 0
        self.start_time = None
        self.last_run_time = None
        self.next_run_time = None
        
        # 后台运行相关
        self.daemon_mode = False
        self.pid_file = Path(f"/tmp/ithaca_scheduler_{name}.pid")
        self.status_file = Path(f"/tmp/ithaca_scheduler_{name}_status.json")
        self.command_socket_path = f"/tmp/ithaca_scheduler_{name}.sock"
        self.command_server = None
        
        # 信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGUSR1, self._pause_handler)
        signal.signal(signal.SIGUSR2, self._resume_handler)
        
        # 注册退出清理
        atexit.register(self._cleanup)
        
        logger.info(f"Scheduler '{name}' initialized with {interval_seconds}s interval")
    
    def start_daemon(self):
        """启动为后台守护进程"""
        if self._is_running():
            logger.error(f"Scheduler '{self.name}' is already running")
            return False
        
        # 创建守护进程
        try:
            pid = os.fork()
            if pid > 0:
                # 父进程退出
                logger.info(f"Scheduler started as daemon with PID {pid}")
                sys.exit(0)
        except OSError as e:
            logger.error(f"Fork failed: {e}")
            return False
        
        # 子进程继续
        os.chdir("/")
        os.setsid()
        os.umask(0)
        
        # 第二次fork
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as e:
            logger.error(f"Second fork failed: {e}")
            sys.exit(1)
        
        # 重定向标准输入输出
        sys.stdout.flush()
        sys.stderr.flush()
        
        # 写入PID文件
        self._write_pid_file()
        
        # 启动后台模式
        self.daemon_mode = True
        self._start_command_server()
        self._run_loop()
        
        return True
    
    def start_foreground(self):
        """前台模式启动"""
        logger.info("Starting scheduler in foreground mode")
        logger.info("Press Ctrl+C to stop")
        
        self.daemon_mode = False
        self._run_loop()
    
    def stop(self):
        """停止调度器"""
        if self.running:
            self.running = False
            logger.info("Scheduler stopped")
            self._update_status()
    
    def pause(self):
        """暂停调度器"""
        if self.running and not self.paused:
            self.paused = True
            logger.info("Scheduler paused")
            self._update_status()
    
    def resume(self):
        """恢复调度器"""
        if self.running and self.paused:
            self.paused = False
            logger.info("Scheduler resumed")
            self._update_status()
    
    def get_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        now = datetime.now()
        return {
            "name": self.name,
            "running": self.running,
            "paused": self.paused,
            "daemon_mode": self.daemon_mode,
            "step_count": self.step_count,
            "interval_seconds": self.interval_seconds,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "last_run_time": self.last_run_time.isoformat() if self.last_run_time else None,
            "next_run_time": self.next_run_time.isoformat() if self.next_run_time else None,
            "uptime_seconds": (now - self.start_time).total_seconds() if self.start_time else 0,
            "pid": os.getpid(),
            "workflow": str(self.workflow)
        }
    
    def _run_loop(self):
        """主运行循环"""
        self.running = True
        self.start_time = datetime.now()
        self._update_status()
        
        logger.info("Scheduler main loop started")
        
        try:
            while self.running:
                if not self.paused:
                    # 执行workflow步骤
                    self._execute_step()
                    
                    # 计算下次运行时间
                    self.next_run_time = datetime.now() + timedelta(seconds=self.interval_seconds)
                    self._update_status()
                    
                    # 等待间隔时间
                    self._wait_for_next_step()
                else:
                    # 暂停状态下短暂睡眠
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            logger.info("Scheduler interrupted by user")
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
        finally:
            self.running = False
            self._update_status()
            self._cleanup()
    
    def _execute_step(self):
        """执行一个workflow步骤"""
        try:
            logger.info(f"Executing step #{self.step_count + 1}")
            step_start = datetime.now()

            # Init run at start
            if self.step_count == 0 and hasattr(self.workflow, "init_run"):
                logger.info(f"Executing init run")
                success = self.workflow.init_run()
            else:
                logger.info(f"Executing loop run")
                success = self.workflow.run()
                
            step_end = datetime.now()
            duration = (step_end - step_start).total_seconds()
                
            if success:
                self.step_count += 1
                self.last_run_time = step_end
                logger.info(f"Step #{self.step_count} completed successfully in {duration:.2f}s")
            else:
                logger.error(f"Step #{self.step_count + 1} failed after {duration:.2f}s")
                
        except Exception as e:
            logger.error(f"Error executing workflow step: {e}")
    
    def _wait_for_next_step(self):
        """等待下次执行"""
        remaining = self.interval_seconds
        while remaining > 0 and self.running and not self.paused:
            sleep_time = min(1, remaining)  # 每秒检查一次状态
            time.sleep(sleep_time)
            remaining -= sleep_time
    
    def _start_command_server(self):
        """启动命令服务器（用于接收控制命令）"""
        if os.path.exists(self.command_socket_path):
            os.unlink(self.command_socket_path)
        
        def server_thread():
            try:
                server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                server.bind(self.command_socket_path)
                server.listen(1)
                self.command_server = server
                
                while self.running:
                    try:
                        server.settimeout(1.0)
                        conn, addr = server.accept()
                        
                        data = conn.recv(1024).decode('utf-8').strip()
                        response = self._handle_command(data)
                        
                        conn.send(response.encode('utf-8'))
                        conn.close()
                        
                    except socket.timeout:
                        continue
                    except Exception as e:
                        logger.error(f"Command server error: {e}")
                        
            except Exception as e:
                logger.error(f"Failed to start command server: {e}")
        
        threading.Thread(target=server_thread, daemon=True).start()
    
    def _handle_command(self, command: str) -> str:
        """处理控制命令"""
        try:
            if command == "status":
                return json.dumps(self.get_status(), indent=2)
            elif command == "stop":
                self.stop()
                return "Scheduler stopped"
            elif command == "pause":
                self.pause()
                return "Scheduler paused"
            elif command == "resume":
                self.resume()
                return "Scheduler resumed"
            elif command.startswith("interval "):
                try:
                    new_interval = int(command.split()[1])
                    self.interval_seconds = new_interval
                    return f"Interval changed to {new_interval} seconds"
                except (ValueError, IndexError):
                    return "Invalid interval format. Use: interval <seconds>"
            else:
                return f"Unknown command: {command}"
                
        except Exception as e:
            return f"Command error: {e}"
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"Received signal {signum}")
        self.stop()
    
    def _pause_handler(self, signum, frame):
        """暂停信号处理器"""
        self.pause()
    
    def _resume_handler(self, signum, frame):
        """恢复信号处理器"""
        self.resume()
    
    def _write_pid_file(self):
        """写入PID文件"""
        try:
            with open(self.pid_file, 'w') as f:
                f.write(str(os.getpid()))
        except Exception as e:
            logger.error(f"Failed to write PID file: {e}")
    
    def _update_status(self):
        """更新状态文件"""
        try:
            with open(self.status_file, 'w') as f:
                json.dump(self.get_status(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to update status file: {e}")
    
    def _is_running(self) -> bool:
        """检查是否已经在运行"""
        if not self.pid_file.exists():
            return False
        
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # 检查进程是否存在
            os.kill(pid, 0)
            return True
            
        except (OSError, ValueError):
            # PID文件无效或进程不存在
            if self.pid_file.exists():
                self.pid_file.unlink()
            return False
    
    def _cleanup(self):
        """清理资源"""
        try:
            if self.command_server:
                self.command_server.close()
            
            if os.path.exists(self.command_socket_path):
                os.unlink(self.command_socket_path)
            
            if self.pid_file.exists():
                self.pid_file.unlink()
                
        except Exception as e:
            logger.error(f"Cleanup error: {e}")