"""
Simple scheduler for looping marketing tasks.
Supports foreground and background (daemon) execution modes.
"""
import time
import signal
import sys
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json
import os

from ithaca.agents.holisticagent import HolisticAgent
from ithaca.agents.agent_types import HolisticInput, HolisticOutput, EvaluationInput, EvaluationOutput
from ithaca.db import IthacaDB, HistoryModel
from ithaca.logger import logger

class SimpleScheduler:
    """
    Simple marketing scheduler for looping tasks.
    """
    
    def __init__(
        self,
        product_name: str,
        product_url: str,
        total_budget: float,
        interval_hours: int = 24 * 7,  # default: 1 week
        product_picture_url: Optional[str] = None
    ):
        self.product_name = product_name
        self.product_url = product_url
        self.total_budget = total_budget
        self.interval_hours = interval_hours
        self.product_picture_url = product_picture_url
        
        self.agent = HolisticAgent()
        self.running = False
        self.cycle_count = 0
        self.last_run_time = None
        
        # for background mode command handling
        self.command_thread = None
        self.daemon_mode = False
        
        # set signal handler
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"Simple scheduler initialized for {product_name}")
    
    def _signal_handler(self, signum, frame):
        """Handle stop signal"""
        logger.info(f"Received signal {signum}, stopping scheduler...")
        self.stop()
    
    def start_foreground(self):
        """Start scheduler in FOREGROUND mode"""
        logger.info("Starting scheduler in FOREGROUND mode")
        logger.info("Press Ctrl+C to stop")
        
        self.daemon_mode = False
        self.running = True
        self._run_loop()
    
    def start_background(self):
        """Start scheduler in BACKGROUND mode"""
        logger.info("Starting scheduler in BACKGROUND mode")
        logger.info("Available commands: 'stop', 'status', 'help'")
        logger.info("Type 'help' for more information")
        
        self.daemon_mode = True
        self.running = True
        
        # Start command listener thread
        self.command_thread = threading.Thread(
            target=self._command_listener,
            daemon=True
        )
        self.command_thread.start()
        
        # Start main loop
        self._run_loop()
    
    def stop(self):
        """Stop scheduler"""
        if self.running:
            self.running = False
            logger.info("Scheduler stopped")
    
    def _run_loop(self):
        """Main running loop"""
        try:
            while self.running:
                try:
                    # execute marketing task
                    self._execute_marketing_task()
                    self.cycle_count += 1
                    self.last_run_time = datetime.now()
                    
                    # calculate next run time
                    next_run = datetime.now() + timedelta(hours=self.interval_hours)
                    logger.info(f"Cycle #{self.cycle_count} completed. Next run at {next_run}")
                    
                    # wait for specified time
                    self._wait_for_next_cycle()
                    
                except Exception as e:
                    logger.error(f"Error in marketing task: {e}")
                    logger.info("Waiting 30 minutes before retry...")
                    self._sleep_with_check(30 * 60)  # 30 minutes later retry
                    
        except KeyboardInterrupt:
            logger.info("Scheduler interrupted")
        finally:
            self.running = False
    
    def _execute_marketing_task(self):
        """Execute marketing task"""
        logger.info(f"Starting marketing task for {self.product_name}")
        
        # prepare input
        holistic_input = HolisticInput(
            total_budget=self.total_budget,
            product_name=self.product_name,
            product_url=self.product_url,
            product_picture_url=self.product_picture_url,
            marketing_history=None  # Agent will automatically load from database
        )
        
        # execute Agent
        start_time = datetime.now()
        result = self.agent.run(holistic_input)
        end_time = datetime.now()
        
        if result and result.get("parsed_output"):
            output = result["parsed_output"]
            logger.info(f"Marketing task completed in {(end_time - start_time).total_seconds():.2f}s")
            logger.info(f"Generated {len(output.marketing_plans)} marketing plans")
            
            # save to database
            self._save_to_history(output)
            
        else:
            logger.error("Marketing task failed - no valid output")
    
    def _save_to_history(self, output: HolisticOutput):
        """Save results to history database"""
        try:
            for plan in output.marketing_plans:
                history_record = HistoryModel(
                    product_name=self.product_name,
                    product_url=self.product_url,
                    plan_id=plan.plan_uuid,
                    plan_description=plan.plan_description,
                    plan_details=plan.plan_details,
                    plan_evaluation=None,  # temporarily empty
                    plan_score=None,       # temporarily empty
                    created_at=datetime.now()
                )
                
                success = IthacaDB.add(history_record)
                if success:
                    logger.debug(f"Saved plan {plan.plan_uuid} to history")
                else:
                    logger.error(f"Failed to save plan {plan.plan_uuid}")
                    
        except Exception as e:
            logger.error(f"Error saving to history: {e}")
    
    def _wait_for_next_cycle(self):
        """Wait for next execution"""
        total_seconds = self.interval_hours * 3600
        self._sleep_with_check(total_seconds)
    
    def _sleep_with_check(self, seconds: int):
        """Sleep with check"""
        while seconds > 0 and self.running:
            sleep_time = min(60, seconds)  # Check every minute
            time.sleep(sleep_time)
            seconds -= sleep_time
    
    def _command_listener(self):
        """Background command listener"""
        while self.running:
            try:
                command = input().strip().lower()
                self._handle_command(command)
            except (EOFError, KeyboardInterrupt):
                break
            except Exception as e:
                logger.error(f"Command error: {e}")
    
    def _handle_command(self, command: str):
        """Handle user command"""
        if command == "stop":
            logger.info("Received STOP command")
            self.stop()
            
        elif command == "status":
            self._show_status()
            
        elif command == "help":
            self._show_help()
            
        elif command == "info":
            self._show_info()
            
        elif command.startswith("interval "):
            try:
                new_interval = int(command.split()[1])
                self.interval_hours = new_interval
                logger.info(f"Interval changed to {new_interval} hours")
            except (ValueError, IndexError):
                logger.error("Invalid interval format. Use: interval <hours>")
                
        else:
            logger.warning(f"Unknown command: {command}. Type 'help' for available commands")
    
    def _show_status(self):
        """Show scheduler status"""
        status = {
            "running": self.running,
            "mode": "background" if self.daemon_mode else "foreground",
            "product": self.product_name,
            "cycle_count": self.cycle_count,
            "interval_hours": self.interval_hours,
            "last_run": self.last_run_time.isoformat() if self.last_run_time else "Never",
            "next_run": (datetime.now() + timedelta(hours=self.interval_hours)).isoformat() if self.running else "Stopped"
        }
        
        print("\n" + "="*50)
        print("SCHEDULER STATUS")
        print("="*50)
        for key, value in status.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
        print("="*50 + "\n")
    
    def _show_help(self):
        """Show help information"""
        help_text = """
Available Commands:
  stop              - Stop the scheduler
  status            - Show current status
  info              - Show product information
  interval <hours>  - Change interval (e.g., interval 48)
  help              - Show this help message

Examples:
  status            - Check scheduler status
  interval 72       - Set interval to 72 hours (3 days)
  stop              - Stop the scheduler
        """
        print(help_text)
    
    def _show_info(self):
        """Show product information"""
        print(f"\nProduct Information:")
        print(f"  Name: {self.product_name}")
        print(f"  URL: {self.product_url}")
        print(f"  Budget: ${self.total_budget}")
        print(f"  Picture: {self.product_picture_url or 'Not provided'}")
        print()
