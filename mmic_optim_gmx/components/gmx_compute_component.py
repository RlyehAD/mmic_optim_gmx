# Import models
from mmelemental.models.util.output import FileOutput
from mmelemental.models import Molecule, Trajectory
from ..models import GmxComputeInput, GmxComputeOutput

# Import components
from mmic.components.blueprints import SpecificComponent

from typing import Dict, Any, List, Tuple, Optional
import os


class PostComponent(SpecificComponent):
    @classmethod
    def input(cls):
        return GmxComputeInput

    @classmethod
    def output(cls):
        return GmxComputeOutput

    def execute(
        self,
        inputs: GmxComputeOutput,
        extra_outfiles: Optional[List[str]] = None,
        extra_commands: Optional[List[str]] = None,
        scratch_name: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Tuple[bool, GmxComputeOutput]:

        # Call gmx pdb2gmx, mdrun, etc. here
        if isinstance(inputs, dict):
            inputs = self.input()(**inputs)
        
        mdp_fname, gro_fname, top_fname = inputs.mdp_file, inputs.coord_file, inputs.struct_file
        
        assert os.path.exists('./mdp_fname'), "No mdp file found"
        assert os.path.exists('./gro_fname'), "No gro file found"
        assert os.path.exists('./top_fname'), "No top file found"
        
        mol = ...  # path to output structure file, minimized
        traj = ...  # path to output traj file

        return True, GmxComputeOutput(
            proc_input=inputs.proc_input,
            molecule=mol,
            trajectory=traj,
        )
    
    def build_input(
        self,
        inputs: Dict[str, Any],
        config: Optional["TaskConfig"] = None,
        template: Optional[str] = None,
    ) -> Dict[str, Any]:
        
