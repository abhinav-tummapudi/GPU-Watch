import argparse
from logger import setup_logger
from config_loader import load_criterion
from job_analyzer import enrich_job_data
from job_actions import handle_warnings, handle_kills
import warnings

warnings.filterwarnings("ignore")

logger = setup_logger()

def parse_args():
    parser = argparse.ArgumentParser(description="GPU Job Monitor for SLURM")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--warn", action="store_true", help="Send warning emails only")
    group.add_argument("--kill", action="store_true", help="Kill inefficient jobs only")
    group.add_argument("--both", action="store_true", help="Send warnings and kill jobs")
    group.add_argument("--dry-run", action="store_true", help="Only log jobs, take no action")
    return parser.parse_args()

def main():
    args = parse_args()
    logger.info("GPU Monitor started with mode: %s", 
                "warn" if args.warn else "kill" if args.kill else "both" if args.both else "dry-run")
    
    criterion = load_criterion()
    job_df = enrich_job_data(criterion)

    if job_df.empty:
        logger.info("No jobs to process.")
        return

    if args.warn or args.both or args.dry_run:
        logger.info("Warning logic active")
        warn_df = handle_warnings(job_df, criterion, dry_run=args.dry_run)

    if args.kill or args.both or args.dry_run:
        logger.info("Kill logic active")
        handle_kills(warn_df, dry_run=args.dry_run)

if __name__ == "__main__":
    main()

