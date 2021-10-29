# Energy Minimization Component

[//]: # (Badges)
[![GitHub Actions Build Status](https://github.com/MolSSI/mmic_optim_gmx/workflows/CI/badge.svg)](https://github.com/MolSSI/mmic_optim_gmx/actions?query=workflow%3ACI)
[![codecov](https://codecov.io/gh/MolSSI/mmic_optim_gmx/branch/main/graph/badge.svg)](https://codecov.io/gh/MolSSI/mmic_optim_gmx/branch/main)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/MolSSI/mmic_optim_gmx.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/MolSSI/mmic_optim_gmx/context:python)


This is part of the [MolSSI](https://molssi.org) Molecular Mechanics Interoperable Components ([MMIC](https://github.com/MolSSI/mmic)) project. This package provides a tactic component for [mmic_optim](https://github.com/MolSSI/mmic_optim) using the [Gromacs](http://www.gromacs.org) software suite.

## Preparing Input
```python
# Import moleucule and forcefield models
from mmelemental.models import Molecule, ForceField

# Import Strategy MD component
import mmic_optim
# Import Tactic MD component 
import mmic_optim_gmx

# Construct molecule and forcefield objects
# If a specific translator is impoted, it can be used with  
# mol = Molecule.from_file(path_to_file, TRANSLATOR_NAME)
mol = Molecule.from_file(path_to_file)
ff = ForceField.from_file(path_to_file)

# Construct input data model from molecule and forcefield objects
inp = mmic_optim.InputMD(
	engine="gmx", # Engine must be gmx and must be specified
    schema_name=SCHEMA_NAME,
    schema_version=SCHEMA_VERSION,
    system={mol: ff},
    boundary=(
        "periodic",
        "periodic",
        "periodic",
        "periodic",
        "periodic",
        "periodic",
    ),
    max_steps=MAX_STEP_NUMBER,
    step_size=STEP_SIZE,
    tol=TOLERENCE,
    method=EM_ALGORITHM,
    long_forces={"method": METHOD_FOR_LONGRANGE_INTERACTION},
    short_forces={"method": METHOD_FOR_SHORT_INTERACTION},
 )

```
Examples for the Parameters:

The unit for *TORLERANCE* is kJ/(mol $\times$ nm)

*EM_ALGORITHM*  "cg"

*METHOD_FOR_LONGRANGE_INTERACTION*  "PME"

*METHOD_FOR_SHORT_INTERACTION*  "cut-off"

## Runing MD Simulation
```python
# Import strategy compoent for runing MD simulation
from mmic_optim_gmx.components import OptimGMXComponent

# Run MD Simulation
outp = OptimGMXComponent.compute(inp)
```

## Extracting Output
```python
# Extract the potential energy 
pot_energy = outp.observables["pot_energy"]
...
```

### Copyright

Copyright (c) 2021, Xu Guo, Andrew Abi-Mansour


#### Acknowledgements
 
Project based on the 
[Computational Molecular Science Python Cookiecutter](https://github.com/molssi/cookiecutter-cms) version 1.5.
