#!/usr/bin/env python3
"""
Main entry point for the Ithaca scheduler system.
"""
import argparse
import sys
from ithaca.scheduler import SimpleScheduler
from ithaca.workflow.holistic_workflow import HolisticWorkflow
from ithaca.agents.agent_types import HolisticInput
from ithaca.logger import logger

def main():
    parser = argparse.ArgumentParser(
        description="Ithaca Marketing Scheduler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 启动后台调度器
  python -m ithaca.main start --product-name "Smart Watch" --product-url "https://example.com" --budget 10000 --daemon
  
  # 前台运行
  python -m ithaca.main start --product-name "Smart Watch" --product-url "https://example.com" --budget 10000
  
  # 控制调度器
  python -m ithaca.scheduler_cli status
  python -m ithaca.scheduler_cli pause
  python -m ithaca.scheduler_cli resume
  python -m ithaca.scheduler_cli stop
        """
    )
    
    subparsers = parser.add_subparsers(dest="action", help="Available actions")
    
    # start命令
    start_parser = subparsers.add_parser("start", help="Start scheduler")
    start_parser.add_argument("--product-name", required=True, help="Product name")
    start_parser.add_argument("--product-url", required=True, help="Product URL")
    start_parser.add_argument("--budget", type=float, required=True, help="Total budget")
    start_parser.add_argument("--picture-url", help="Product picture URL")
    start_parser.add_argument("--interval", type=int, default=3600, help="Interval in seconds (default: 3600 = 1 hour)")
    start_parser.add_argument("--name", default="scheduler", help="Scheduler name")
    start_parser.add_argument("--daemon", "-d", action="store_true", help="Run as daemon")
    
    args = parser.parse_args()
    
    if not args.action:
        parser.print_help()
        return 1
    
    if args.action == "start":
        try:
            # 创建workflow输入
            workflow_input = HolisticInput(
                total_budget=args.budget,
                product_name=args.product_name,
                product_url=args.product_url,
                product_picture_url=args.picture_url
            )
            
            # 创建workflow
            workflow = HolisticWorkflow(workflow_input)
            
            # 创建调度器
            scheduler = SimpleScheduler(
                workflow=workflow,
                interval_seconds=args.interval,
                name=args.name
            )
            
            # 启动调度器
            if args.daemon:
                logger.info("Starting scheduler as daemon...")
                success = scheduler.start_daemon()
                if not success:
                    return 1
            else:
                logger.info("Starting scheduler in foreground...")
                scheduler.start_foreground()
                
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            return 0
        except Exception as e:
            logger.error(f"Error: {e}")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())