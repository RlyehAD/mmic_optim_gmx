# Import models
from mmic_optim.models.output import OutputOptim
from mmelemental.models import Molecule, Trajectory
from ..models import OutputComputeGmx
from cmselemental.util.decorators import classproperty

# Import components
from mmic.components.blueprints import GenericComponent

from typing import List, Tuple, Optional
import os
import shutil


__all__ = ["PostGmxComponent"]


class PostGmxComponent(GenericComponent):
    @classproperty
    def input(cls):
        return OutputComputeGmx

    @classproperty
    def output(cls):
        return OutputOptim

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
        inputs: OutputComputeGmx,
        extra_outfiles: Optional[List[str]] = None,
        extra_commands: Optional[List[str]] = None,
        scratch_name: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Tuple[bool, OutputOptim]:

        """
        This method translate the output of em
        to mmic schema. But right now it can only
        be applied to single molecule conditions
        """
        if isinstance(inputs, dict):
            inputs = self.input(**inputs)

        traj_names = []
        traj = {}

        for key in list(inputs.proc_input.system):
            traj_names.append(key.name)

        traj_file = [inputs.trajectory]
        # In the future, inputs.trajectory should be inherently a list
        # Since the code only deals with one molecule at a time right now
        # it's necessary to make it a list manually

        if inputs.proc_input.trajectory is None:
            for key in traj_names:
                for val in traj_file:
                    traj[key]: Trajectory.from_file(
                        val
                    )  # Use names in Molecule to name trajectories
                    traj_file.remove(val)
                    break
        else:
            traj = {
                key: Trajectory.from_file(inputs.trajectory)
                for key in inputs.proc_input.trajectory
            }

        mol_file = inputs.molecule
        mol = Molecule.from_file(mol_file)
        mols = [mol]
        self.cleanup([inputs.scratch_dir])
        self.cleanup([inputs.trajectory])
        self.cleanup([mol_file])

        return (
            True,
            OutputOptim(
                proc_input=inputs.proc_input,
                molecule=mols,
                trajectory=traj,
                schema_name=inputs.proc_input.schema_name,
                schema_version=inputs.proc_input.schema_version,
                success=True,
            ),
        )

    @staticmethod
    def cleanup(remove: List[str]):
        for item in remove:
            if os.path.isdir(item):
                shutil.rmtree(item)
            elif os.path.isfile(item):
                os.remove(item)
