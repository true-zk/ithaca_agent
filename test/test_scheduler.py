import asyncio
import json
import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from ithaca.scheduler import SimpleScheduler
from ithaca.workflow.base import BaseWorkFlow


class DummyWorkFlow(BaseWorkFlow):

    def __str__(self):
        return "Dummy workflow for test only"

    def run(self):
        print(f"DummyWorkFlow running at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        time.sleep(3)
        return True
    

def test_scheduler_daemon():
    """测试后台模式"""
    print("Testing daemon mode...")
    workflow = DummyWorkFlow()
    scheduler = SimpleScheduler(workflow=workflow, interval_seconds=10, name="test_daemon")
    
    success = scheduler.start_daemon()
    if success:
        print("Daemon started successfully")
    else:
        print("Failed to start daemon")
    return success


def test_scheduler_foreground():
    """测试前台模式"""
    print("Testing foreground mode...")
    workflow = DummyWorkFlow()
    scheduler = SimpleScheduler(workflow=workflow, interval_seconds=10, name="test_foreground")
    
    # 前台模式会阻塞，所以这个函数不会返回（除非被中断）
    scheduler.start_foreground()


def test_scheduler_with_timeout():
    """测试调度器（带超时）"""
    import threading
    import time
    
    workflow = DummyWorkFlow()
    scheduler = SimpleScheduler(workflow=workflow, interval_seconds=5, name="test_timeout")
    
    # 在单独线程中启动调度器
    def run_scheduler():
        scheduler.start_foreground()
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    # 等待一段时间让调度器运行
    print("Scheduler running for 30 seconds...")
    time.sleep(30)
    
    # 停止调度器
    scheduler.stop()
    print("Scheduler stopped")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["daemon", "foreground", "timeout"], default="daemon")
    args = parser.parse_args()
    
    if args.mode == "daemon":
        test_scheduler_daemon()
    elif args.mode == "foreground":
        test_scheduler_foreground()
    elif args.mode == "timeout":
        test_scheduler_with_timeout()