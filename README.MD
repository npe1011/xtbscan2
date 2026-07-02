# GUI Tool for PES Scan with xTB or uma/omol25

## 1. Introduction

### 1.1. Overview

This is an improved version of xtbscan (https://github.com/npe1011/xtbscan), a GUI tool for performing and analyzing so-called Scan (relaxed scan) calculations using Grimme's xTB
 or uma/omol25 (ASE + torch + fairchem-core). It supports 1D and 2D scans, as well as multi-parameter concerted scans. The GUI interface is written by Google Antigravity.

## 2. Requirements

You need uv (https://docs.astral.sh/uv/). All Python dependencies are installed automatically when launched.

For uma/omol25 calculation using GPU, the appropriate driver should be installed. PyTorch with CUDA 12.6 (pytorch-cu126) is installed by uv.

## 3. Launch

#### Windows
Run `xtbscan2.bat` or `xtbscan2_gpu.bat` (GPU enabled version).

#### Mac
Run `xtbscan2.command` or `xtbscan2_gpu.command` (GPU enabled version).

#### Caution
At the first run, dependencies are installed via uv, which download and save huge files (few GB or more).


## 4. Configuration

First, you need to select xtb binary and uma parameter file from **Settings > Configuration**. To run gxtb level calculation, xtb binary with gxtb implementation is required.

CPU, Memory, and GPU settings are also available here.

## 5. Usage

### 5.1. Load Initial Structure File

- Load a file by dropping it at the top area.
- ORCA6, Gaussian16, or xyz files can be read.
- For other files, cclib library is tried to parse it.

### 5.2. Setting Calculation
- **Job Name**: Used as a prefix for output files (xyz and csv). 
- **Engine**: xtb or uma 

#### 5.2.1 XTB Settings

- `Method`: xtb parameters. `gxtb` is generally recommended, although solvation is not useful for gxtb and thus is disabled.
- `Solvent`: Implicit solvation via ALPB model. Currently not available for gxtb.
- `Charge`: Total charge.
- `Multiplicity`: Spin multiplicity (internally converted to UHF parameter for xtb).

#### 5.2.2 UMA Settings

- `Charge`: Total charge.
- `Multiplicity`: Spin multiplicity (passed to the UMA/OMol calculator).

### 5.3. Setting Scan Conditions

- You can scan distances (2 atoms), angles (3 atoms), and dihedrals (4 atoms).
- Enter parameters and click **Add Scan** to add them to the table.
- Atoms are indexed from 1, separated by spaces or commas.
- **Start / End / Steps** specify the initial value, final value, and the number of scan steps.
- One condition: 1D scan, Two conditions: 2D scan. 3D or higher dimension scans are not possible.
- Checking **Concerted Scan** enables concerted scans, where multiple geometrical parameters change synchronously
  in a 1D scan. **Steps** must be identical for all scan parameters.
- If no scan conditions are given, a simple geometry optimization is performed.
- With xTB, scans are run via the built-in function of the xTB binary.
  With uma/omol25, scans are done by repeated ASE constraint optimizations, so behaviors may differ.

### 5.4. Additional Parameter Fixing: Constrain Conditions

- Additional geometrical parameters can be fixed.
- For fixing at the current value, you can use current or auto (auto is not available in scan settings).
- Complex constraint/scan combinations are not well tested. Atom constraints may not work when combined with
  other scans or constraints (especially when using UMA).

### 5.5. Run Calculations

- Click **Run Calculation**.
- You can cancel calculation by clicking **Stop**. You cannot resume the calculation.

### 5.6. Visualize Results

- When performing simple optimization, only an optimized structure xyz file is given. 
- Upon successful termination of scans, you will be asked whether to load the results.
- Once the results are loaded, you can view the scan plot in the Result tab.
- Results are saved as **JOBNAME.csv (energies)** and **JOBNAME.xyz (structures)**.
- Previous results can be loaded by opening CSV files (drop onto the top area or Result tab).
- **Show Table Data** opens a window displaying the full numerical data.

## 6. License
This project is licensed under the MIT License.

