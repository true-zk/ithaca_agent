#!/usr/bin/env python3
"""
调度器命令行控制工具
"""
import argparse
import json
import socket
import sys
import os
import signal
from pathlib import Path

def send_command(scheduler_name: str, command: str) -> str:
    """向调度器发送命令"""
    socket_path = f"/tmp/ithaca_scheduler_{scheduler_name}.sock"
    
    if not os.path.exists(socket_path):
        return f"Scheduler '{scheduler_name}' is not running"
    
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(socket_path)
        client.send(command.encode('utf-8'))
        
        response = client.recv(4096).decode('utf-8')
        client.close()
        
        return response
        
    except Exception as e:
        return f"Error communicating with scheduler: {e}"

def get_scheduler_status(scheduler_name: str) -> dict:
    """获取调度器状态"""
    status_file = Path(f"/tmp/ithaca_scheduler_{scheduler_name}_status.json")
    
    if not status_file.exists():
        return {"error": f"Scheduler '{scheduler_name}' status not found"}
    
    try:
        with open(status_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        return {"error": f"Failed to read status: {e}"}

def main():
    parser = argparse.ArgumentParser(description="Scheduler Control CLI")
    parser.add_argument("--name", "-n", default="scheduler", help="Scheduler name")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # status命令
    status_parser = subparsers.add_parser("status", help="Show scheduler status")
    
    # stop命令
    stop_parser = subparsers.add_parser("stop", help="Stop scheduler")
    
    # pause命令
    pause_parser = subparsers.add_parser("pause", help="Pause scheduler")
    
    # resume命令
    resume_parser = subparsers.add_parser("resume", help="Resume scheduler")
    
    # interval命令
    interval_parser = subparsers.add_parser("interval", help="Change interval")
    interval_parser.add_argument("seconds", type=int, help="New interval in seconds")
    
    # kill命令（强制停止）
    kill_parser = subparsers.add_parser("kill", help="Force kill scheduler")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    scheduler_name = args.name
    
    if args.command == "status":
        status = get_scheduler_status(scheduler_name)
        if "error" in status:
            print(status["error"])
            return 1
        
        print(f"Scheduler '{scheduler_name}' Status:")
        print(f"  Running: {status.get('running', False)}")
        print(f"  Paused: {status.get('paused', False)}")
        print(f"  Steps completed: {status.get('step_count', 0)}")
        print(f"  Uptime: {status.get('uptime_seconds', 0):.0f} seconds")
        print(f"  Last run: {status.get('last_run_time', 'Never')}")
        print(f"  Next run: {status.get('next_run_time', 'Unknown')}")
        print(f"  Interval: {status.get('interval_seconds', 0)} seconds")
        print(f"  PID: {status.get('pid', 'Unknown')}")
        
    elif args.command == "kill":
        pid_file = Path(f"/tmp/ithaca_scheduler_{scheduler_name}.pid")
        if pid_file.exists():
            try:
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
                os.kill(pid, signal.SIGTERM)
                print(f"Sent SIGTERM to scheduler PID {pid}")
            except Exception as e:
                print(f"Failed to kill scheduler: {e}")
                return 1
        else:
            print(f"Scheduler '{scheduler_name}' PID file not found")
            return 1
    
    elif args.command == "interval":
        command = f"interval {args.seconds}"
        response = send_command(scheduler_name, command)
        print(response)
    
    else:
        # 其他命令直接发送
        response = send_command(scheduler_name, args.command)
        print(response)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())