import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(line_buffering=True)

import logging
_old_log = logging.Logger._log
def _suppress_noisy_log(self, level, msg, args, exc_info=None, extra=None, stack_info=False, stacklevel=1):
    if isinstance(msg, str) and ("Redirects are currently not supported" in msg or "dataset_list" in msg):
        return
    return _old_log(self, level, msg, args, exc_info=exc_info, extra=extra, stack_info=stack_info, stacklevel=stacklevel)
logging.Logger._log = _suppress_noisy_log

import json
import argparse
from pathlib import Path

src_path = Path(__file__).parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from core import config
from core.parsers import ensure_xyz
from core.xtb import XTBParams, XTBScan, XTBConstrain, xtbscan
from core.uma import UMAParams, UMAScan, UMAConstrain, umascan, get_uma_calculator

def main():
    parser = argparse.ArgumentParser(description="xtbscan2 Backend CLI")
    parser.add_argument("job_file", type=str, help="Path to JSON job file")
    args = parser.parse_args()
    
    job_file = Path(args.job_file).absolute()
    if not job_file.exists():
        print(f"Error: Job file {job_file} not found.")
        sys.exit(1)
        
    with open(job_file, 'r', encoding='utf-8') as f:
        job_data = json.load(f)
        
    engine = job_data.get("engine", "xtb").lower()
    input_file = Path(job_data.get("input_file"))
    job_name = job_data.get("job_name", "job")
    
    # Pre-parse input file into init.xyz
    workdir = input_file.parent
    init_xyz = ensure_xyz(input_file, workdir)
    
    scans = job_data.get("scans", [])
    constrains = job_data.get("constrains", [])
    concerted = job_data.get("concerted", False)
    cpus = int(job_data.get("cpus", config.get("NUM_THREADS", 1)))
    memory = str(job_data.get("memory", config.get("MEMORY_PER_THREAD", "500M")))
    keep_log_val = int(job_data.get("keep_log", config.get("KEEP_LOG", 1)))
    
    if engine == "xtb":
        method = job_data.get("method", "gfn2")
        solvent = job_data.get("solvent")
        solvation = "alpb" if solvent else None
        if method in ["gfnff", "gxtb"]:
            solvent = None
            solvation = None

        from core.xtb import setenv_xtb
        setenv_xtb(num_threads=cpus, memory_per_thread=memory)

        xtb_params = XTBParams(
            method=method,
            charge=job_data.get("charge", 0),
            uhf=job_data.get("mult", 1) - 1, # uhf = mult - 1
            solvation=solvation,
            solvent=solvent
        )
        
        parsed_scans = []
        for s in scans:
            parsed_scans.append(XTBScan(
                scan_type=s["type"],
                atom_indices=s["atoms"],
                start=s["start"],
                end=s["end"],
                num_step=s["steps"]
            ))
            
        parsed_constrains = []
        for c in constrains:
            parsed_constrains.append(XTBConstrain(
                constrain_type=c["type"],
                atom_indices=c["atoms"],
                value=c.get("value")
            ))
            
        force_constant = job_data.get("force_constant", "1.0")
        
        try:
            xtbscan(
                input_xyz_file=init_xyz,
                job_name=job_name,
                xtb_params=xtb_params,
                scans=parsed_scans,
                constrains=parsed_constrains,
                force_constant=force_constant,
                concerted=concerted,
                keep_log=keep_log_val
            )
            print("Calculation completed successfully.")
        except Exception as e:
            print(f"Calculation failed: {e}")
            sys.exit(1)
            
    elif engine == "uma":
        uma_params = UMAParams(
            charge=job_data.get("charge", 0),
            mult=job_data.get("mult", 1),
            fmax=job_data.get("fmax", 0.02),
            max_cycles=job_data.get("max_cycles", 1000)
        )
        
        parsed_scans = []
        for s in scans:
            parsed_scans.append(UMAScan(
                scan_type=s["type"],
                atom_indices=s["atoms"],
                start=s["start"],
                end=s["end"],
                num_step=s["steps"]
            ))
            
        parsed_constrains = []
        for c in constrains:
            parsed_constrains.append(UMAConstrain(
                constrain_type=c["type"],
                atom_indices=c["atoms"],
                value=c.get("value")
            ))
            
        try:
            from core.uma import setenv_uma
            setenv_uma(num_threads=cpus, memory_per_thread=memory)

            device = "cuda" if config.UMA_USE_GPU else "cpu"
            model_path = Path(config.UMA_PARAM_PATH)
            calculator = get_uma_calculator(model_path, device)
            
            umascan(
                input_xyz_file=init_xyz,
                job_name=job_name,
                calculator=calculator,
                uma_params=uma_params,
                scans=parsed_scans,
                constrains=parsed_constrains,
                concerted=concerted,
                keep_log=keep_log_val
            )
            print("Calculation completed successfully.")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Calculation failed: {e}")
            sys.exit(1)
    else:
        print(f"Error: Unknown engine {engine}")
        sys.exit(1)

if __name__ == "__main__":
    main()
