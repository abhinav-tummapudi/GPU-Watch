from datetime import datetime
import socket
import os

def log_job_section(header: str, jobs_df, log_dir="logs/nodes_log/"):
    # Get current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Get the hostname
    hostname = socket.gethostname()

    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)

    # Create log path based on hostname
    log_path = os.path.join(log_dir, f"{hostname}.log")

    # Write to log
    with open(log_path, 'a') as f:
        f.write(f"\n\n==================== {header.upper()} ({timestamp}) ====================\n\n")
        for _, row in jobs_df.iterrows():
            f.write(f"SLURM_JOB_ID: {row['SLURM_JOB_ID']}\n")
            f.write(f"USER: {row['USER']}\n")
            f.write(f"USED_MEMORY: {row['USED_MEMORY']} MB\n")
            f.write(f"GPU_TYPE: {str(row['GPU_ALLOCATED']).split(':')[0]}\n")
            f.write(f"ALLOCATED: {row['GPU_ALLOCATED']}\n")
            f.write(f"UTILIZED: {row['UTILIZATION_PERCENTAGE']:.2f}%\n")
            f.write(f"THRESHOLD: {row['THRESHOLD']}%\n\n")

