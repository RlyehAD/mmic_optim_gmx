# Import models
from ..models import InputComputeGmx, OutputComputeGmx
from cmselemental.util.decorators import classproperty

# Import components
from mmic_cmd.components import CmdComponent
from mmic.components.blueprints import GenericComponent

from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import os
import shutil
import tempfile
import ntpath


__all__ = ["ComputeGmxComponent"]


class ComputeGmxComponent(GenericComponent):
    @classproperty
    def input(cls):
        return InputComputeGmx

    @classproperty
    def output(cls):
        return OutputComputeGmx

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
        inputs: InputComputeGmx,
        extra_outfiles: Optional[List[str]] = None,
        extra_commands: Optional[List[str]] = None,
        scratch_name: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Tuple[bool, OutputComputeGmx]:

        # Call gmx pdb2gmx, mdrun, etc. here
        if isinstance(inputs, dict):
            inputs = self.input(**inputs)

        proc_input, mdp_file, gro_file, top_file = (
            inputs.proc_input,
            inputs.mdp_file,
            inputs.molecule,
            inputs.forcefield,
        )  # The parameters here are all str

        tpr_file = tempfile.NamedTemporaryFile(suffix=".tpr", delete=False)

        input_model = {
            "proc_input": proc_input,
            "mdp_file": mdp_file,
            "gro_file": gro_file,
            "top_file": top_file,
            "tpr_file": tpr_file.name,
        }

        clean_files, cmd_input_grompp = self.build_input_grompp(input_model)
        rvalue = CmdComponent.compute(cmd_input_grompp)
        self.cleanup(clean_files)  # Del mdp and top file in the working dir
        self.cleanup([inputs.scratch_dir])
        tpr_dir = str(rvalue.scratch_directory)

        input_model = {"proc_input": proc_input, "tpr_file": tpr_file.name}
        cmd_input_mdrun = self.build_input_mdrun(input_model)
        rvalue = CmdComponent.compute(cmd_input_mdrun)
        self.cleanup([tpr_file.name, gro_file])
        self.cleanup([tpr_dir])

        return True, self.parse_output(rvalue.dict(), proc_input)

    @staticmethod
    def cleanup(remove: List[str]):
        for item in remove:
            if os.path.isdir(item):
                shutil.rmtree(item)
            elif os.path.isfile(item):
                os.remove(item)

    def build_input_grompp(
        self,
        inputs: Dict[str, Any],
        config: Optional["TaskConfig"] = None,
        template: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build the input for grompp
        """
        assert inputs["proc_input"].engine == "gmx", "Engine must be gmx (Gromacs)!"

        env = os.environ.copy()

        if config:
            env["MKL_NUM_THREADS"] = str(config.ncores)
            env["OMP_NUM_THREADS"] = str(config.ncores)

        scratch_directory = config.scratch_directory if config else None

        tpr_file = inputs["tpr_file"]

        clean_files = []
        clean_files.append(inputs["mdp_file"])
        clean_files.append(inputs["top_file"])

        cmd = [
            inputs["proc_input"].engine,
            "grompp",
            "-f",
            inputs["mdp_file"],
            "-c",
            inputs["gro_file"],
            "-p",
            inputs["top_file"],
            "-o",
            tpr_file,
            "-maxwarn",
            "-1",
        ]
        outfiles = [tpr_file]
        print(tpr_file)

        return (
            clean_files,
            {
                "command": cmd,
                "as_binary": [tpr_file],
                "infiles": [inputs["mdp_file"], inputs["gro_file"], inputs["top_file"]],
                "outfiles": outfiles,  # [Path(file).name for file in outfiles],
                # "outfiles_track": outfiles,#[Path(file).name for file in outfiles],
                "scratch_directory": scratch_directory,
                "environment": env,
                "scratch_messy": True,
            },
        )

    def build_input_mdrun(
        self,
        inputs: Dict[str, Any],
        config: Optional["TaskConfig"] = None,
        template: Optional[str] = None,
    ) -> Dict[str, Any]:

        env = os.environ.copy()

        if config:
            env["MKL_NUM_THREADS"] = str(config.ncores)
            env["OMP_NUM_THREADS"] = str(config.ncores)

        scratch_directory = config.scratch_directory if config else None

        log_file = tempfile.NamedTemporaryFile(suffix=".log", delete=False)
        trr_file = tempfile.NamedTemporaryFile(suffix=".trr", delete=False)
        edr_file = tempfile.NamedTemporaryFile(suffix=".edr", delete=False)
        gro_file = tempfile.NamedTemporaryFile(suffix=".gro", delete=False)

        tpr_file = inputs["tpr_file"]
        tpr_fname = ntpath.basename(tpr_file)

        cmd = [
            inputs["proc_input"].engine,  # Should here be gmx_mpi?
            "mdrun",
            "-s",
            tpr_file,
            "-o",
            trr_file.name,
            "-c",
            gro_file.name,
            "-e",
            edr_file.name,
            "-g",
            log_file.name,
        ]

        outfiles = [trr_file.name, gro_file.name, edr_file.name, log_file.name]
        print(tpr_file)

        # For extra args
        if inputs["proc_input"].keywords:
            for key, val in inputs["proc_input"].keywords.items():
                if val:
                    cmd.extend([key, val])
                else:
                    cmd.extend([key])

        return {
            "command": cmd,
            "as_binary": [
                tpr_fname,
                trr_file.name,
                edr_file.name,
            ],  # For outfiles, mmic_cmd does not use ntpath.basename to obtain the basic name
            "infiles": [tpr_file],
            "outfiles": outfiles,
            # "outfiles_track": outfiles,
            "scratch_directory": scratch_directory,
            "environment": env,
            "scratch_messy": True,
        }

    def parse_output(
        self, output: Dict[str, str], inputs: Dict[str, Any]
    ) -> OutputComputeGmx:
        # stdout = output["stdout"]
        # stderr = output["stderr"]
        outfiles = output["outfiles"]
        scratch_dir = str(output["scratch_directory"])

        traj, conf, energy, log = outfiles.keys()
        print(conf)
        print(traj)

        return self.output(
            proc_input=inputs,
            molecule=conf,
            trajectory=str(traj),
            scratch_dir=scratch_dir,
            # stdout=stdout,
            # stderr=stderr,
        )
