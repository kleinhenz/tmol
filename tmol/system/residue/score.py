from typing import Mapping

import numpy
import torch

from tmol.types.functional import validate_args

from tmol.kinematics.torch_op import KinematicOp
from tmol.kinematics.metadata import DOFTypes

from .packed import PackedResidueSystem
from .kinematics import KinematicDescription


@validate_args
def system_cartesian_space_graph_params(
        system: PackedResidueSystem,
        drop_missing_atoms: bool = False,
        requires_grad: bool = True,
        device: torch.device = torch.device("cpu"),
) -> Mapping:
    """Constructor parameters for cartesian space scoring.

    Extract constructor kwargs to initialize a `CartesianAtomicCoordinateProvider`
    and `BondedAtomScoreGraph` subclass.
    """
    bonds = system.bonds
    coords = (
        torch.tensor(
            system.coords,
            dtype=torch.float,
            device=device,
        ).requires_grad_(requires_grad)
    )

    atom_types = system.atom_metadata["atom_type"].copy()

    if drop_missing_atoms:
        atom_types[numpy.any(numpy.isnan(system.coords), axis=-1)] = None

    return dict(
        system_size=len(coords),
        bonds=bonds,
        coords=coords,
        atom_types=atom_types,
        device=device,
    )


@validate_args
def system_torsion_space_graph_params(
        system: PackedResidueSystem,
        drop_missing_atoms: bool = False,
        requires_grad: bool = True,
        device: torch.device = torch.device("cpu"),
):
    """Constructor parameters for torsion space scoring.

    Extract constructor kwargs to initialize a `KinematicAtomicCoordinateProvider` and
    `BondedAtomScoreGraph` subclass supporting torsion-space scoring. This
    includes only `bond_torsion` dofs, a subset of valid kinematic dofs for the
    system.
    """

    # Initialize kinematic tree for the system
    sys_kin = KinematicDescription.for_system(
        system.bonds, system.torsion_metadata
    )

    # Select torsion dofs
    torsion_dofs = sys_kin.dof_metadata[
        (sys_kin.dof_metadata.dof_type == DOFTypes.bond_torsion)
    ]

    # Extract kinematic-derived coordinates
    kincoords = sys_kin.extract_kincoords(system.coords).to(device)

    # Initialize op for torsion-space kinematics
    kop = KinematicOp.from_coords(
        sys_kin.kintree,
        torsion_dofs,
        kincoords,
    )

    # Bond/type data
    bonds = system.bonds
    atom_types = system.atom_metadata["atom_type"].copy()

    if drop_missing_atoms:
        atom_types[numpy.any(numpy.isnan(system.coords), axis=-1)] = None

    return dict(
        system_size=len(system.coords),
        dofs=kop.src_mobile_dofs.clone().requires_grad_(requires_grad),
        kinop=kop,
        bonds=bonds,
        atom_types=atom_types,
        device=device,
    )
