# GPU-Watch

GPU-Watch is an autonomous, node-level GPU utilization enforcement framework for Slurm-managed high-performance computing (HPC) clusters. It continuously monitors GPU usage on each compute node, issues user warnings for sustained underutilization, and automatically terminates idle jobs when corrective action is not taken.

The framework is designed to operate entirely in user space, requiring no centralized controller, shared database, or modifications to Slurm. GPU-Watch is intended for scalable, production-grade deployment on multi-node GPU clusters where utilization fairness and resource efficiency are critical.

This repository contains the reference implementation described in:

> **Abhinav Sai Tummapudi**  
> *GPU-Watch: An Autonomous Node-Level GPU Utilization Enforcement Framework for Slurm Clusters*  
> Practice and Experience in Advanced Research Computing (PEARC), 2026.

---

## Motivation and Design Goals

Modern GPU-based HPC clusters frequently experience resource underutilization due to idle or stalled jobs holding exclusive GPU allocations. Existing approaches often rely on centralized monitoring services, scheduler modifications, or administrative intervention.

GPU-Watch is designed with the following goals:

- Eliminate centralized monitoring bottlenecks
- Preserve scheduler autonomy and policy neutrality
- Enable deterministic, node-local enforcement
- Maintain enforcement state across restarts without centralized storage
- Require minimal operational overhead for deployment and maintenance

---

## Key Features

- **Node-level autonomy:**  
  Each compute node independently enforces utilization policy, eliminating single points of failure.

- **Threshold-based enforcement:**  
  GPU utilization thresholds, minimum evaluation runtime, warning durations, and termination countdowns are fully configurable.

- **Deterministic execution:**  
  Systemd service and timer units ensure non-overlapping, periodic enforcement cycles.

- **Persistent state tracking:**  
  Node-scoped CSV state files preserve warnings and enforcement history across service restarts and node reboots.

- **Dual-scope observability:**  
  Consolidated cluster-level logs are complemented by detailed node-local execution logs.

- **Optional cluster-wide verification:**  
  Ansible-based health checks validate service activity and generate HTML reports across all nodes.

- **User-space operation:**  
  No root privileges, kernel modules, or Slurm configuration changes are required.

---

## Repository Structure

```text
gpu-watch/
├── src/              # Core Python enforcement and monitoring logic
├── systemd/          # Systemd service and timer units
├── ansible/          # Cluster-wide health verification playbooks
├── config/           # Policy configuration and email templates
├── data/             # Runtime state (generated at execution time)
├── logs/             # Runtime logs (generated at execution time)
├── requirements.txt  # Python dependencies
├── README.md
└── LICENSE
```

> **Note:** The `data/` and `logs/` directories are intentionally excluded from version control.  
> They are created automatically at runtime and are node-scoped by design.

---

## System Requirements

GPU-Watch is designed for Linux-based Slurm compute nodes equipped with NVIDIA GPUs.

---

## Software Requirements

- Python 3.8 or newer
- Slurm client utilities (`squeue`, `scontrol`)
- NVIDIA drivers and utilities (`nvidia-smi`)
- systemd
- Ansible (optional, for cluster-wide verification)

---

## Installation

Install Python dependencies:

```bash
pip install -r requirements.txt
```

No Slurm configuration changes are required.

---

## Code Walkthrough (src/)

This section documents the main Python modules and the execution flow.

### Entry Point

- `src/main.py`  
  Primary entry point for GPU-Watch. It:
  1. Parses the execution mode (`--warn`, `--kill`, `--both`, `--dry-run`)
  2. Loads policy criteria from `config/criterion.json`
  3. Collects and enriches active Slurm job data (GPU allocation + utilization signals)
  4. Runs warning logic (optional)
  5. Runs termination logic (optional)

Execution modes (mutually exclusive):
- `--warn`    : Send warning emails only
- `--kill`    : Terminate inefficient jobs only
- `--both`    : Send warnings and terminate jobs (policy-driven)
- `--dry-run` : Log all actions but perform no enforcement (no emails, no kills)

### Core Modules

- `src/config_loader.py`  
  Loads and validates enforcement criteria (thresholds, grace periods, countdowns) from `config/criterion.json`.

- `src/job_analyzer.py`  
  Builds the job dataframe used for enforcement. Typically responsible for:
  - Discovering active GPU jobs from Slurm (`squeue`/`scontrol`)
  - Enriching each job with metadata (user, jobid, node, GPU allocation)
  - Attaching utilization signals (from `nvidia-smi` or node telemetry)

- `src/job_processor.py`  
  Normalizes and processes job records into a consistent structure for the policy engine (filtering, grouping, time-window handling, etc.).

- `src/job_actions.py`  
  Contains the enforcement policy actions:
  - `handle_warnings(...)` to evaluate warning criteria and send notifications
  - `handle_kills(...)` to evaluate termination criteria and issue job cancellations  
  This module typically consumes policy criteria + enriched job info + persisted state.

- `src/email_alert.py`  
  Generates and sends user/admin notifications. Uses `config/warning_mail.html` as the template.

- `src/slurm_utils.py`  
  Slurm integration utilities (wrappers around `squeue`, `scontrol`, `scancel`, parsing helpers).

- `src/nvidia_utils.py`  
  NVIDIA GPU signal utilities (e.g., `nvidia-smi` sampling/parsing, GPU UUID mapping, per-process signals if applicable).

- `src/logger.py`  
  Logging configuration (log formatting, log file routing, log levels).

- `src/utils.py`  
  Generic helper functions shared across modules.

---

## How to Run

GPU-Watch can be run manually (recommended for artifact review) or via systemd timer (recommended for deployment).

### 1) Quick Start (Dry Run)

Dry-run is the safest mode: it performs full analysis and logs intended actions, but does not email or terminate jobs.

From repository root:

```bash
cd gpu-watch
pip install -r requirements.txt

python3 -m src.main --dry-run
```

**Expected behavior:**

- Logs startup mode (`dry-run`)
- Loads `config/criterion.json`
- Queries active Slurm jobs
- Logs warning/kill decisions that *would* occur under real enforcement

---

#### 2) Warning Only

```bash
python3 -m src.main --warn
```

**Expected behavior:**

- Identifies jobs that violate utilization policy
- Sends warning emails using `config/warning_mail.html`
- Writes/updates runtime state in `data/` (warnings, countdowns)

---

#### 3) Kill Only

```bash
python3 -m src.main --kill
```

**Expected behavior:**

- Identifies jobs that have exceeded the allowed warning/countdown policy window
- Cancels jobs via Slurm (e.g., `scancel`)
- Logs all enforcement actions

---

#### 4) Full Enforcement (Warn + Kill)

```bash
python3 -m src.main --both
```

**Expected behavior:**

- Sends warnings when thresholds are violated
- Terminates jobs when countdown/grace policy is exhausted

---

## Configuration

All enforcement policy parameters are defined in a single configuration file:

- `config/criterion.json`

This file specifies:

- GPU utilization thresholds
- Minimum runtime before evaluation
- Warning grace periods
- Termination countdown durations
- (Any exclusions/whitelists if present)

User notification emails are generated using:

- `config/warning_mail.html`

Policy changes do **not** require code modification or service reinstallation.

---

## Runtime Output (Generated)

These directories are created at runtime and are excluded from version control:

- `data/`  
  Persistent enforcement state (CSV-based), such as:
  - warning history
  - countdown progress
  - termination decisions

- `logs/`  
  Execution logs, including:
  - consolidated enforcement actions
  - per-run debug/trace output (depending on logger settings)

---

## Deployment Model

### Node-Level Enforcement

Each compute node runs GPU-Watch as a systemd-managed service:

- `systemd/gpu-watch.service`
- `systemd/gpu-watch.timer`

The timer invokes enforcement at fixed intervals, ensuring deterministic and non-overlapping evaluation cycles.

This decentralized model avoids centralized schedulers, databases, or message brokers.

---

### Cluster-Wide Health Verification (Optional)

The `ansible/` directory contains playbooks that:

- Verify active GPU-Watch timers across nodes
- Detect inactive or failed services
- Generate per-node and consolidated HTML health reports
- Send alert notifications when enforcement gaps are detected


