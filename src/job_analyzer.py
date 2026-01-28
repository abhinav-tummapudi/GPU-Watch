import re
import numpy as np
import pandas as pd
import subprocess
from slurm_utils import get_running_jobs, get_hostname
from nvidia_utils import get_nvidia_processes, map_pid_to_job
from job_processor import convert_duration_to_seconds

def enrich_job_data(criterion: dict) -> pd.DataFrame:
    hostname = get_hostname()
    jobs = get_running_jobs(hostname)

    if jobs.empty:
        return pd.DataFrame()

    jobs["JOBID"] = jobs["JOBID"].str.replace(r'_\d+$', '', regex=True)
    jobs['GPU_ALLOCATED'] = np.nan
    jobs['TIME_SECONDS'] = np.nan

    for idx in range(len(jobs)):
        job_id = jobs.loc[idx, 'JOBID']
        try:
            output = subprocess.run(["scontrol", "show", "job", str(job_id), "-o"],
                                    stdout=subprocess.PIPE, text=True, check=True)
            match = re.search(r"TresPerNode=[^\s]*", output.stdout)
            if match:
                jobs.loc[idx, 'GPU_ALLOCATED'] = match.group(0).split('gpu:')[1]
        except:
            pass

        try:
            jobs.loc[idx, 'TIME_SECONDS'] = convert_duration_to_seconds(jobs.loc[idx, 'TIME'])
        except:
            pass

    nvidia_df = get_nvidia_processes()
    nvidia_df['SLURM_JOB_ID'] = nvidia_df['PID'].apply(map_pid_to_job)
    nvidia_df = nvidia_df.dropna(subset=['SLURM_JOB_ID'])

    jobs.rename(columns={"JOBID": "SLURM_JOB_ID"}, inplace=True)
    merged = pd.merge(jobs, nvidia_df, on='SLURM_JOB_ID', how='left')
    merged = merged.groupby('SLURM_JOB_ID', as_index = False).agg({
                'SLURM_JOB_ID': 'first',
                'PARTITION': 'first',
                'NAME': 'first',
                'USER': 'first',
                'ST': 'first',
                'TIME': 'first',
                'NODES': 'first',
                'NODELIST(REASON)': 'first',
                'GPU_ALLOCATED': 'first',
                'TIME_SECONDS': 'first',
                'GPU_UUID': 'first',
                'PID': 'first',
                'USED_MEMORY': 'max',
                'PROCESS_NAME': 'first'})

    merged = merged.drop_duplicates(subset=['PID', 'SLURM_JOB_ID']).reset_index(drop=True)
    
    merged['UTILIZATION_PERCENTAGE'] = np.nan
    for idx in range(len(merged)):
        try:
            match = re.search(r'\.(\d+)gb', str(merged.loc[idx, 'GPU_ALLOCATED']).lower())
            if match:
                gpu_mem = int(match.group(1)) * 1000
                used = float(merged.loc[idx, 'USED_MEMORY'])
                merged.loc[idx, 'UTILIZATION_PERCENTAGE'] = (used / gpu_mem) * 100
        except:
            continue

    merged = merged.astype({
        "SLURM_JOB_ID": int,
        "USED_MEMORY": float,
        "UTILIZATION_PERCENTAGE": float
    }, errors='ignore')

    return merged

