import json
from pathlib import Path

# Config files
CONFIG_DIR = Path.home() / '.xtbscan2'
CONFIG_FILE = CONFIG_DIR / 'config.json'
DEFAULT_CONFIG_FILE = Path(__file__).parent / 'config_default.json'

# Global configuration dictionary
settings = {}

def load_config():
    global settings
    
    # Load defaults first
    if DEFAULT_CONFIG_FILE.exists():
        with open(DEFAULT_CONFIG_FILE, 'r', encoding='utf-8') as f:
            settings.update(json.load(f))
            
    # Load user config
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            user_settings = json.load(f)
            settings.update(user_settings)

def save_config(new_settings=None):
    if new_settings is not None:
        settings.update(new_settings)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=4)

load_config()

def get(key, default=None):
    return settings.get(key, default)

# For compatibility with older code, map the constants dynamically,
# or define them statically based on the dictionary.
# Using __getattr__ to provide dynamic access:
def __getattr__(name):
    if name in settings:
        return settings[name]
    if name in globals():
        return globals()[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# Constants (not necessary to edit)
JOULE_TO_KCAL = 2.390E-4
HARTREE_TO_JOULE_PER_MOL = 2.6255E6
HARTREE_TO_KCAL = 627.51
ANG_TO_BOHR = 1.8897259886

XTB_NAME = 'xtbscan2'
XTB_OPT_FILE = 'xtbopt.xyz'
XTB_SCAN_FILE = 'xtbscan.log'
XTB_LOG_FILE = 'xtblog.txt'
XTB_INPUT_FILE = 'xtbinp.txt'

XYZ_FORMAT = '{:<2s}  {:>12.8f}  {:>12.8f}  {:>12.8f}\n'

INIT_XYZ_FILE = 'init.xyz'
INPUT_FILE = 'input.txt'
STOP_FILE_SUFFIX = '_stopmessage.dat'
STOP_CHECK_INTERVAL = 1  # sec

USE_SCIPY = True
CHECK_SADDLE2D_GRAD_TOL = 0.001

XTB_SOLVENT_LIST = [
    'Acetone', 'Acetonitrile', 'Aniline', 'Benzaldehyde', 'Benzene', 'CH2Cl2', 'CHCl3', 'CS2',
    'Dioxane', 'DMF', 'DMSO', 'Ether', 'Ethylacetate', 'Furane', 'Hexadecane', 'Hexane',
    'Methanol', 'Nitromethane', 'Octanol', 'Phenol', 'Toluene', 'THF', 'Water'
]

ATOM_LIST = ['bq', 'H', 'He', 'Li', 'Be', 'B', 'C', 'N', 'O', 'F', 'Ne', 'Na', 'Mg', 'Al', 'Si', 'P', 'S', 'Cl', 'Ar',
             'K', 'Ca', 'Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn', 'Ga', 'Ge', 'As', 'Se', 'Br', 'Kr',
             'Rb', 'Sr', 'Y', 'Zr', 'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In', 'Sn', 'Sb', 'Te', 'I', 'Xe',
             'Cs', 'Ba', 'La', 'Ce', 'Pr', 'Nd', 'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu', 'Hf',
             'Ta', 'W', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg', 'Tl', 'Pb', 'Bi', 'Po', 'At', 'Rn', 'Fr', 'Ra', 'Ac', 'Th',
             'Pa', 'U', 'Np', 'Pu', 'Am', 'Cm', 'Bk', 'Cf', 'Es', 'Fm', 'Md', 'No', 'Lr', 'Rf', 'Db', 'Sg', 'Bh', 'Hs',
             'Mt', 'Ds', 'Rg', 'Cn']
