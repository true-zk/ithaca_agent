"""
Main entry point for the Ithaca project.
"""
from ithaca.scheduler.simple_scheduler import SimpleScheduler

def main():
    """Main function - support command line arguments"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Simple Marketing Scheduler")
    parser.add_argument("--product-name", required=True, help="Product name")
    parser.add_argument("--product-url", required=True, help="Product URL")
    parser.add_argument("--budget", type=float, required=True, help="Total budget")
    parser.add_argument("--interval", type=int, default=168, help="Interval in hours (default: 168 = 1 week)")
    parser.add_argument("--picture-url", help="Product picture URL")
    parser.add_argument("--background", "-b", action="store_true", help="Run in background mode")
    
    args = parser.parse_args()
    
    # Create scheduler
    scheduler = SimpleScheduler(
        product_name=args.product_name,
        product_url=args.product_url,
        total_budget=args.budget,
        interval_hours=args.interval,
        product_picture_url=args.picture_url
    )
    
    # Start scheduler
    if args.background:
        scheduler.start_background()
    else:
        scheduler.start_foreground()

if __name__ == "__main__":
    main()