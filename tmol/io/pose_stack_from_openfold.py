import torch
import numpy
import toolz

from typing import Mapping
from tmol.types.functional import validate_args
from tmol.database import ParameterDatabase
from tmol.io.canonical_ordering import CanonicalOrdering
from tmol.pose.packed_block_types import PackedBlockTypes
from tmol.pose.pose_stack import PoseStack


@validate_args
def pose_stack_from_openfold(openfold_result_dictionary, **kwargs) -> PoseStack:
    """Build a PoseStack from the output generated by openfold

    This function will build a PoseStack using a limited set of
    residue type: only the canonical amino acids with the canonical
    n- and c-termini patches. It begins by constructing a "canonical
    form" and then passes that canonical form to the
    pose_stack_from_canonical_form function. See
    canonical_form_from_openfold (below) for details
    on this intermediate representation and how it might be
    useful to you.

    Additional arguments to pose_stack_from_canonical_form may be
    passed through this function using the kwargs.
    """
    from tmol.io.pose_stack_construction import pose_stack_from_canonical_form

    cf = canonical_form_from_openfold(openfold_result_dictionary)

    co = canonical_ordering_for_openfold()
    pbt = packed_block_types_for_openfold(cf["coords"].device)

    return pose_stack_from_canonical_form(co, pbt, **cf, **kwargs)


@validate_args
def canonical_form_from_openfold(openfold_result_dictionary) -> Mapping:
    """The canonical form is intended to represent a stable, serializable intermediate format
    for a structure so that it can be created today and then be read in years from now
    and be used to construct a PoseStack in tmol. As residue types (aatype) are integers,
    this means that we must guarantee stability of these integer representations, but it also
    means that you the user must build a PoseStack using the carefully-constructed objects
    returned by the canonical_ordering_for_openfold and packed_block_types_for_openfold
    functions.

    E.g.:
        output = openfold_model.infer(sequences)
        cf = tmol.canonical_form_from_openfold(output)
        torch.save(cf, "saved_canonical_form.pt")

        # then later
        cf2 = {x: y.to(device) for x,y in torch.load("saved_canonical_form.pt")}
        co = canonical_ordering_for_openfold()
        pbt = packed_block_types_for_openfold(device)
        pose_stack = tmol.pose_stack_from_canonical_form(co, pbt, **cf2)

    """

    of_aatypes = openfold_result_dictionary["aatype"]
    of_coords = openfold_result_dictionary["positions"][-1]
    of_chain_ind = openfold_result_dictionary["chain_index"]

    assert (
        len(of_aatypes.shape) == 2
    ), 'openfold_result_dictionary["aatype"] must be 2D tensor'
    assert (
        len(of_coords.shape) == 4
    ), 'openfold_result_dictionary["positions"][-1] must be 4D tensor'
    assert (
        len(of_chain_ind.shape) == 2
    ), 'openfold_result_dictionary["chain_index"] must be 2D tensor'

    device = of_aatypes.device
    n_poses = of_coords.shape[0]
    max_n_res = of_coords.shape[1]
    max_n_ats = of_coords.shape[2]

    of_pose_ind_for_atom = (
        torch.arange(n_poses, dtype=torch.int64, device=device)
        .reshape(-1, 1, 1)
        .expand(-1, max_n_res, max_n_ats)
    )
    of_res_ind_for_atom = (
        torch.arange(max_n_res, dtype=torch.int64, device=device)
        .reshape(1, -1, 1)
        .expand(n_poses, -1, max_n_ats)
    )

    assert device == of_coords.device
    assert device == of_chain_ind.device

    co = canonical_ordering_for_openfold()
    of2t_rtmap, of2t_atmap, of_at_is_real_map = _get_of_2_tmol_mappings(device)

    tmol_restypes = of2t_rtmap[of_aatypes]
    atom_mapping = of2t_atmap[of_aatypes]
    of_at_is_real = of_at_is_real_map[of_aatypes]

    tmol_coords = torch.full(
        (n_poses, max_n_res, co.max_n_canonical_atoms, 3),
        numpy.NaN,
        dtype=torch.float32,
        device=device,
    )
    tmol_coords[
        of_pose_ind_for_atom[of_at_is_real],
        of_res_ind_for_atom[of_at_is_real],
        atom_mapping[of_at_is_real],
    ] = of_coords[of_at_is_real]

    return dict(
        chain_id=of_chain_ind.to(torch.int32),
        res_types=tmol_restypes.to(torch.int32),
        coords=tmol_coords,
    )


@toolz.functoolz.memoize
def _paramdb_for_openfold() -> ParameterDatabase:
    """Construct the paramdb representing the subset of residues that
    are "used" in OpenFold: the canonical amino acids (including the
    two histidine tautomers and the disulfid-bonded cysteine) and
    the canonical n- and c-termini patches.
    """

    from tmol.chemical.restypes import one2three
    from tmol.extern.openfold.residue_constants import restypes

    desired_rt_names = [one2three(aa1lc) for aa1lc in restypes] + ["HIS_D", "CYD"]
    # hard coding
    desired_variants_display_names = ["nterm", "cterm"]

    return ParameterDatabase.get_default().create_stable_subset(
        desired_rt_names, desired_variants_display_names
    )


@validate_args
@toolz.functoolz.memoize
def canonical_ordering_for_openfold() -> CanonicalOrdering:
    """Construct the CanonicalOrdering object that will be used for the
    subset of residue types that are used by OpenFold; this will be
    stable so that the entries in "coords" tensor member of the canonical
    form dictionary will be interpretable indefinitely and thus a
    canonical form dictionary can be serialized to disk and read again
    after an arbitrary amount of time
    """

    paramdb = _paramdb_for_openfold()
    return CanonicalOrdering.from_chemdb(paramdb.chemical)


@validate_args
@toolz.functoolz.memoize
def packed_block_types_for_openfold(device: torch.device) -> PackedBlockTypes:
    """Construct the PackedBlockTypes (PBT) object that will be used for
    the subset of residue types that are used by OpenFold. For efficiency
    we use the same PBT in the creation of multiple PoseStacks. Thus
    we memoize this function. The user will only interact with this
    function if they are constructing PoseStacks from deserialized
    canonical form objects. See canonical_form_from_openfold for details.
    """

    import cattr
    from tmol.chemical.restypes import RefinedResidueType

    paramdb = _paramdb_for_openfold()

    # TO DO: at some point, one has to wonder whether the ResidueTypeSet
    # is ever gonna see any action. When the packer comes online, we should
    # start using one during the PBT construction
    restype_list = [
        cattr.structure(
            cattr.unstructure(r),
            RefinedResidueType,
        )
        for r in paramdb.chemical.residues
    ]

    return PackedBlockTypes.from_restype_list(paramdb.chemical, restype_list, device)


@toolz.functoolz.memoize
def _get_of_2_tmol_mappings(device: torch.device):
    # TO DO: refactor this for general usage
    from tmol.chemical.restypes import one2three

    co = canonical_ordering_for_openfold()
    from tmol.extern.openfold.residue_constants import (
        restype_name_to_atom14_names,
        restypes,
    )

    of_name3s = [one2three(x) for x in restypes] + ["XXX"]
    return co.create_src_2_tmol_mappings(
        of_name3s, restype_name_to_atom14_names, device
    )
