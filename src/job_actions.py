import pandas as pd
import subprocess
from email_alert import send_warning_email
from logger import setup_logger
from utils import log_job_section
import numpy as np
from slurm_utils import get_hostname
from datetime import datetime
from datetime import timedelta

logger = setup_logger()

JOB_WARNED = 'data/' + get_hostname() +'_warned.csv'

def handle_warnings(df: pd.DataFrame, criterion: dict, dry_run: bool = False):
    # Preprocess
    df.replace(np.nan, 0, inplace=True)
    df['GPU_TYPE'] = df['GPU_ALLOCATED'].apply(lambda x: str(x).split(':')[0])
    df['THRESHOLD'] = df['GPU_TYPE'].map(lambda x: int(criterion['gpu_limit'].get(x, 0)))

    warning_jobs = df[
        (df['UTILIZATION_PERCENTAGE'] <= df['THRESHOLD']) &
        (df['TIME_SECONDS'] >= int(criterion['warning']['time']))
    ].copy()

    if warning_jobs.empty:
        logger.info("No underutilized jobs to warn.")
        # return

    # Load previously warned jobs
    try:
        warned_prev = pd.read_csv(JOB_WARNED, parse_dates=['COUNT_DOWN'])
        if warned_prev.empty or warned_prev.columns.size == 0:
            raise ValueError("Empty or malformed CSV")
    except (FileNotFoundError, pd.errors.EmptyDataError, ValueError):
        warned_prev = pd.DataFrame(columns=['SLURM_JOB_ID', 'COUNT_DOWN'])

    # ⚠️ FIXED BUG: You used `current_warning_jobs`, but it doesn't exist
    current_underutilized_ids = set(warning_jobs['SLURM_JOB_ID'].tolist())

    # Remove recovered jobs (this line was commented out earlier — you can optionally restore it)
    warned_prev = warned_prev[warned_prev['SLURM_JOB_ID'].isin(current_underutilized_ids)]

    # Merge to retain previous COUNT_DOWN
    warning_jobs = warning_jobs.merge(
        warned_prev[['SLURM_JOB_ID', 'COUNT_DOWN']],
        on='SLURM_JOB_ID',
        how='left'
    )

    now = datetime.now()
    warning_jobs['COUNT_DOWN'] = warning_jobs['COUNT_DOWN'].fillna(now)

    warning_jobs['STATUS'] = (
        now - pd.to_datetime(warning_jobs['COUNT_DOWN'])
    ) > timedelta(
        hours=int(criterion['countdown']['timer']['hours']),
        minutes=int(criterion['countdown']['timer']['minutes']),
        seconds=int(criterion['countdown']['timer']['seconds'])
    )

    # Identify new jobs not previously warned
    new_warnings = warning_jobs[~warning_jobs['SLURM_JOB_ID'].isin(warned_prev['SLURM_JOB_ID'])].copy()

    if new_warnings.empty:
        logger.info("All underutilized jobs have already been warned.")
    else:
        logger.info(f"Found {len(new_warnings)} *new* underutilized job(s) to warn")
        for _, row in new_warnings.iterrows():
            if dry_run:
                logger.info(f"[Dry Run] Would warn job {row['SLURM_JOB_ID']} user {row['USER']}")
            else:
                pass
                # Placeholder: send_warning_email(...)
                # Send email here if enabled
                success = send_warning_email(
                 user_netid=row['USER'],
                 slurm_job_id=row['SLURM_JOB_ID'],
                 gpu_allocated=row['GPU_ALLOCATED'],
                 used_memory_mb=row['USED_MEMORY'],
                 gpu_node=row['NODELIST(REASON)']
             )
             
                logger.info(f"Sent email to {row['USER']} for job {row['SLURM_JOB_ID']} → {'✅' if success else '❌'}")

    # ✅ FIXED BUG: You referred to `warning_df` but it doesn't exist. It's `warning_jobs`.
    columns_to_save = [
        'SLURM_JOB_ID', 'PARTITION', 'NAME', 'USER', 'ST', 'TIME', 'NODES',
        'NODELIST(REASON)', 'GPU_ALLOCATED', 'TIME_SECONDS', 'GPU_UUID', 'PID',
        'USED_MEMORY', 'PROCESS_NAME', 'UTILIZATION_PERCENTAGE',
        'COUNT_DOWN', 'STATUS'
    ]
    columns_to_save = [col for col in columns_to_save if col in warning_jobs.columns]

    warning_jobs[columns_to_save].to_csv(JOB_WARNED, index=False)

    logger.info("📝 Updated warned jobs file.")

    if not dry_run and not new_warnings.empty:
        log_job_section("WARNING JOBS", new_warnings)
    
    return warning_jobs

def handle_kills(df: pd.DataFrame, dry_run: bool = False):
    # Filter jobs with STATUS == True (ready to be killed)
    #logger.info(df)
    
    if df.empty:
        logger.info("Data Frame Empty - Handle Kills")
        return

    kill_jobs = df[df['STATUS'] == True].copy()

    if kill_jobs.empty:
        logger.info("No jobs to kill.")
        return

    logger.warning(f"Found {len(kill_jobs)} job(s) to be killed due to inefficiency")

    for _, row in kill_jobs.iterrows():
        job_id = row['SLURM_JOB_ID']
        if dry_run:
            logger.info(f"[Dry Run] Would cancel job {job_id}")
        else:
            #pass
            try:
                subprocess.run(['scancel', str(job_id)], check=True)
                logger.critical(f"Cancelled job {job_id}")
            except Exception as e:
                logger.error(f"Failed to cancel job {job_id}: {e}")

    # Save list of killed jobs
    kill_jobs.to_csv('data/job_killed.csv', index=False)
    logger.info("Updated killed jobs file.")

    if not dry_run:
        log_job_section("KILLED JOBS", kill_jobs)
