import os
import uuid
from pathlib import Path
import numpy as np
from typing import Tuple, List

from core import xyzutils
from core.config import ATOM_LIST

try:
    import cclib
    CCLIB = True
except ImportError:
    CCLIB = False

def detect_file_type(file: Path) -> str:
    ext = file.suffix.lower()
    if ext == '.xyz':
        return 'xyz'
    
    with file.open('r', encoding='utf-8', errors='ignore') as f:
        data = f.read(4000) # read first 4000 chars
        
    if 'O   R   C   A' in data or '* O   R   C   A *' in data:
        return 'orca_log'
    elif 'Gaussian' in data or 'Entering Gaussian' in data or 'Gaussian, Inc.' in data:
        return 'gaussian_log'
    
    # Check input types
    if data.strip().startswith('!') or '* xyz' in data.lower() or '* int' in data.lower() or '%pal' in data.lower():
        return 'orca_inp'
    if data.strip().startswith('%') or data.strip().startswith('#'):
        return 'gaussian_inp'
        
    return 'other'

def parse_initial_structure(file: Path) -> Tuple[np.ndarray, np.ndarray]:
    """
    Parse an input file and return (atoms, coordinates).
    atoms: 1D numpy array of strings
    coordinates: 2D numpy array of floats (num_atoms, 3)
    """
    file_type = detect_file_type(file)
    
    if file_type == 'xyz':
        # Might be sequential, we just want the last one if so, but read_single_xyz_file reads first or last?
        # Let's use read_sequential_xyz_file and take the last frame.
        try:
            atoms, coords_list, _ = xyzutils.read_sequential_xyz_file(file)
            return atoms, coords_list[-1]
        except:
            atoms, coords = xyzutils.read_single_xyz_file(file)
            return atoms, coords
            
    elif file_type == 'gaussian_inp':
        return _parse_gaussian_input(file)
        
    elif file_type == 'gaussian_log':
        return _parse_gaussian_log(file)
        
    elif file_type == 'orca_inp':
        return _parse_orca_input(file)
        
    elif file_type == 'orca_log':
        return _parse_orca_log(file)
        
    else:
        if not CCLIB:
            raise RuntimeError('The cclib library is required to parse non-XYZ formats (e.g. Gaussian/ORCA logs). Please install cclib or provide an XYZ file.')
        data = cclib.io.ccread(str(file))
        coordinates = data.atomcoords[-1,::]
        atoms = np.array([ATOM_LIST[n] for n in data.atomnos])
        return atoms, coordinates

def ensure_xyz(file: Path, out_dir: Path, job_name: str = "job") -> Path:
    """
    Parses the given file and writes a unique temporary xyz file to out_dir.
    Returns the path to the newly created xyz file.
    """
    file = Path(file).absolute()
    out_dir = Path(out_dir).absolute()
    
    # Clean up old legacy init.xyz if it exists
    old_init = out_dir / 'init.xyz'
    if old_init.exists():
        try:
            old_init.unlink()
        except Exception:
            pass

    atoms, coords = parse_initial_structure(file)
    unique_id = uuid.uuid4().hex[:8]
    out_file = out_dir / f"_tmp_init_{job_name}_{unique_id}.xyz"
    xyzutils.save_xyz_file(out_file, atoms, coords, f'Extracted from {file.name}')
    return out_file

def _parse_gaussian_input(file: Path) -> Tuple[np.ndarray, np.ndarray]:
    with file.open(mode='r', encoding='utf-8', errors='ignore') as f:
        input_data = []
        chk_void = False
        line = f.readline()
        while line:
            line = line.lstrip()
            if not line:
                if not chk_void:
                    input_data.append("\n")
                    chk_void = True
            else:
                if line[0] != "!":
                    chk_void = False
                    input_data.append(line)
            line = f.readline()

    state = 0
    structure_data = []
    for data_line in input_data:
        if state == 0:
            if data_line.startswith('#'):
                state = 1
        elif state == 1:
            if data_line == '\n':
                state = 2
        elif state == 2:
            if data_line == '\n':
                state = 3
        else:
            if data_line != '\n':
                if data_line[0:2].upper() != 'LP':
                    structure_data.append(data_line)
            else:
                break

    atoms = []
    coordinates = []
    for line in structure_data[1:]: # skip charge/multi
        parts = line.strip().split()
        if len(parts) >= 4:
            atoms.append(parts[0].capitalize())
            coordinates.append([float(parts[1]), float(parts[2]), float(parts[3])])
            
    return np.array(atoms), np.array(coordinates, dtype=float)

def _parse_gaussian_log(file: Path) -> Tuple[np.ndarray, np.ndarray]:
    with file.open(mode='r', encoding='utf-8', errors='ignore') as f:
        log_data = f.readlines()

    num_coord = -1
    for num, line in enumerate(log_data):
        if 'Input orientation:' in line or "Standard orientation:" in line:
            num_coord = num

    if num_coord == -1:
        raise ValueError("Could not extract molecular coordinates from the Gaussian log file.")

    i = num_coord + 5
    atoms = []
    coordinates = []
    while i < len(log_data) and log_data[i].strip() and ('------' not in log_data[i]):
        parts = log_data[i].strip().split()
        atom_label = ATOM_LIST[int(parts[1])]
        atoms.append(atom_label)
        coordinates.append([float(parts[3]), float(parts[4]), float(parts[5])])
        i += 1

    return np.array(atoms), np.array(coordinates, dtype=float)

def _parse_orca_input(file: Path) -> Tuple[np.ndarray, np.ndarray]:
    with file.open('r', encoding='utf-8', errors='ignore') as f:
        data = f.readlines()
        
    atoms = []
    coordinates = []
    in_struct = False
    for line in data:
        line = line.strip()
        if line.startswith('*') and 'xyz' in line.lower():
            in_struct = True
            continue
        elif in_struct and line.startswith('*'):
            in_struct = False
            break
        elif in_struct and line:
            parts = line.split()
            if len(parts) >= 4:
                atoms.append(parts[0].capitalize())
                coordinates.append([float(parts[1]), float(parts[2]), float(parts[3])])
                
    return np.array(atoms), np.array(coordinates, dtype=float)

def _parse_orca_log(file: Path) -> Tuple[np.ndarray, np.ndarray]:
    with file.open('r', encoding='utf-8', errors='ignore') as f:
        log_data = f.readlines()
        
    start_idx = -1
    for i, line in enumerate(log_data):
        if line.strip().startswith('CARTESIAN COORDINATES (ANGSTROEM)'):
            start_idx = i + 2
            
    if start_idx == -1:
        # Fallback to input block if calculation failed early
        for i, line in enumerate(log_data):
            if '> * xyz' in line.lower():
                start_idx = i + 1
                break
                
        if start_idx == -1:
            raise ValueError("Could not extract molecular coordinates from the ORCA log file.")
            
        atoms = []
        coordinates = []
        while start_idx < len(log_data):
            line = log_data[start_idx].strip()
            if line.startswith('> *'):
                break
            if line.startswith('> '):
                parts = line[2:].strip().split()
                if len(parts) >= 4:
                    atoms.append(parts[0].capitalize())
                    coordinates.append([float(parts[1]), float(parts[2]), float(parts[3])])
            start_idx += 1
        return np.array(atoms), np.array(coordinates, dtype=float)
            
    atoms = []
    coordinates = []
    while start_idx < len(log_data):
        line = log_data[start_idx].strip()
        if not line or '------' in line:
            break
        parts = line.split()
        if len(parts) >= 4:
            atoms.append(parts[0].capitalize())
            coordinates.append([float(parts[1]), float(parts[2]), float(parts[3])])
        start_idx += 1
        
    return np.array(atoms), np.array(coordinates, dtype=float)
