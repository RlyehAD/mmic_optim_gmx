from cmselemental.models.procedures import InputProc
from mmic_optim.models import InputOptim
from pydantic import Field


__all__ = ["InputComputeGmx"]


class InputComputeGmx(InputProc):
    proc_input: InputOptim = Field(..., description="Procedure input schema.")
    mdp_file: str = Field(
        ...,
        description="The file used for specifying the parameters. Should be a .mdp file.",
    )
    forcefield: str = Field(
        ..., description="The file of the system structure. Should be a .top file."
    )
    molecule: str = Field(
        ...,
        description="The file of the coordinates of the atoms in the system. Should be a .gro file.",
    )

    scratch_dir: str = Field(
        ...,
        description="The path to the directory where the temporary files are written. Generally it's a directory in /tmp",
    )
