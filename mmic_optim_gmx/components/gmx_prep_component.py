# Import models
from mmic_optim.models.input import InputOptim
from mmic_optim_gmx.models import InputComputeGmx
from cmselemental.util.decorators import classproperty

# Import components
from mmic_cmd.components import CmdComponent
from mmic.components.blueprints import GenericComponent

from typing import Any, Dict, List, Tuple, Optional
from pathlib import Path
import os
import tempfile

__all__ = ["PrepGmxComponent"]
_supported_solvents = ("spc", "tip3p", "tip4p")


class PrepGmxComponent(GenericComponent):
    """
    Prepares input for running gmx energy minimization.
    The Molecule object from MMIC schema will be
    converted to a .pdb file here.
    .mdp and .top files will also be constructed
    according to the info in MMIC schema.
    """

    @classproperty
    def input(cls):
        return InputOptim

    @classproperty
    def output(cls):
        return InputComputeGmx

    @classproperty
    def version(cls) -> str:
        """Finds program, extracts version, returns normalized version string.
        Returns
        -------
        str
            Return a valid, safe python version string.
        """
        return ""

    def execute(
        self,
        inputs: InputOptim,
        extra_outfiles: Optional[List[str]] = None,
        extra_commands: Optional[List[str]] = None,
        scratch_name: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Tuple[bool, InputComputeGmx]:

        if isinstance(inputs, dict):
            inputs = self.input(**inputs)

        mdp_inputs = {
            "integrator": inputs.method,
            "emtol": inputs.tol,
            "emstep": inputs.step_size,
            "nsteps": inputs.max_steps,
            "pbc": inputs.boundary,
            "vdwtype": inputs.short_forces.method,
            "coulombtype": inputs.long_forces.method,
        }

        # The following part is ugly and may be
        # improved in the future
        # Translate the method
        if "steep" in mdp_inputs["integrator"]:
            mdp_inputs["integrator"] = "steep"
        if "conjugate" in mdp_inputs["integrator"]:
            mdp_inputs["integrator"] = "cg"

        if mdp_inputs["integrator"] is None:
            mdp_inputs["integrator"] = "steep"
        if mdp_inputs["emtol"] is None:
            mdp_inputs["emtol"] = "1000"
        if mdp_inputs["emstep"] is None:
            mdp_inputs["emstep"] = "0.01"  # The unit here is nm
        if mdp_inputs["emstep"] is None:
            mdp_inputs["emstep"] = "0.01"
        # if mdp_inputs["cutoff-scheme"] is None:
        #    mdp_inputs["cutoff-scheme"] = "Verlet"
        if mdp_inputs["coulombtype"] is None:
            mdp_inputs["coulombtype"] = "PME"

        # Translate boundary str tuple (perodic,perodic,perodic) to a string e.g. xyz
        pbc_dict = dict(zip(["x", "y", "z"], list(mdp_inputs["pbc"])))
        pbc = ""
        for dim in list(pbc_dict.keys()):
            if pbc_dict[dim] != "periodic":
                continue
            else:
                pbc = pbc + dim  # pbc is a str, may need to be initiated elsewhere
        mdp_inputs["pbc"] = pbc

        # Write .mdp file
        mdp_file = tempfile.NamedTemporaryFile(suffix=".mdp", delete=False).name
        with open(mdp_file, "w") as inp:
            for key, val in mdp_inputs.items():
                inp.write(f"{key} = {val}\n")

        mol, ff = list(inputs.system.items()).pop()

        gro_file = tempfile.NamedTemporaryFile(suffix=".gro").name  # output gro
        top_file = tempfile.NamedTemporaryFile(suffix=".top").name
        boxed_gro_file = tempfile.NamedTemporaryFile(suffix=".gro").name

        mol.to_file(gro_file, translator="mmic_parmed")
        ff.to_file(top_file, translator="mmic_parmed")

        input_model = {
            "gro_file": gro_file,
            "proc_input": inputs,
            "boxed_gro_file": boxed_gro_file,
        }
        cmd_input = self.build_input(input_model)
        rvalue = CmdComponent.compute(cmd_input)

        scratch_dir = str(rvalue.scratch_directory)
        self.cleanup(
            [gro_file]
        )  # Del the gro in the working dir; !!!!!!!MUST INPUT A LIST HERE!!!!!!

        gmx_compute = InputComputeGmx(
            proc_input=inputs,
            schema_name=inputs.schema_name,
            schema_version=inputs.schema_version,
            mdp_file=mdp_file,
            forcefield=top_file,
            molecule=boxed_gro_file,
            scratch_dir=scratch_dir,
        )

        return True, gmx_compute

    @staticmethod
    def cleanup(remove: List[str]):
        for item in remove:
            if os.path.isdir(item):
                shutil.rmtree(item)
            elif os.path.isfile(item):
                os.remove(item)

    def build_input(
        self,
        inputs: Dict[str, Any],
        config: Optional["TaskConfig"] = None,
        template: Optional[str] = None,
    ) -> Dict[str, Any]:

        assert inputs["proc_input"].engine == "gmx", "Engine must be gmx (Gromacs)!"

        boxed_gro_file = inputs["boxed_gro_file"]

        env = os.environ.copy()

        if config:
            env["MKL_NUM_THREADS"] = str(config.ncores)
            env["OMP_NUM_THREADS"] = str(config.ncores)

        scratch_directory = config.scratch_directory if config else None

        cmd = [
            inputs["proc_input"].engine,
            "editconf",
            "-f",
            inputs["gro_file"],
            "-d",
            "2",
            "-o",
            boxed_gro_file,
        ]
        outfiles = [boxed_gro_file]

        # Here boxed_gro_file is just an str
        return {
            "command": cmd,
            "infiles": [inputs["gro_file"]],
            "outfiles": outfiles,  # [Path(file) for file in outfiles],
            "outfiles_track": outfiles,  # [Path(file) for file in outfiles],
            "scratch_directory": scratch_directory,
            "environment": env,
            "scratch_messy": True,
        }
