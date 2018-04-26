import toolz
import pandas
import pytest

import tmol.database

import tmol.tests.data.rosetta_baseline as rosetta_baseline

from tmol.score.hbond import HBondScoreGraph


@pytest.mark.xfail
def test_pyrosetta_hbond_comparison(bb_hbond_database, pyrosetta):
    rosetta_system = rosetta_baseline.data["1ubq"]

    test_system = (
        tmol.system.residue.packed.PackedResidueSystem()
        .from_residues(rosetta_system.tmol_residues)
    )  # yapf: disable
    hbond_graph = HBondScoreGraph(
        **tmol.score.system_graph_params(test_system, requires_grad=False)
    )

    # Extract list of hbonds from packed system into summary table
    # via atom metadata
    h_i = hbond_graph.hbond_h_ind
    a_i = hbond_graph.hbond_acceptor_ind
    tmol_candidate_hbonds = pandas.DataFrame.from_dict({
        "h": h_i,
        "a": a_i,
        "h_res": test_system.atom_metadata["residue_index"][h_i],
        "h_atom": test_system.atom_metadata["atom_name"][h_i],
        "a_res": test_system.atom_metadata["residue_index"][a_i],
        "a_atom": test_system.atom_metadata["atom_name"][a_i],
        "score": hbond_graph.hbond_scores,
    }).set_index(["a", "h"])
    tmol_hbonds = tmol_candidate_hbonds.query("score != 0")

    del h_i, a_i

    # Merge with named atom index to get atom indicies in packed system
    # hbonds columns: ["a_atom", "a_res", "h_atom", "h_res", "energy"]
    named_atom_index = (
        pandas.DataFrame(test_system.atom_metadata)
        .set_index(["residue_index", "atom_name"])["atom_index"]
    )
    rosetta_hbonds = toolz.curried.reduce(pandas.merge)((
        rosetta_system.hbonds,
        (
            named_atom_index.rename_axis(["a_res", "a_atom"])
            .to_frame("a").reset_index()
        ),
        (
            named_atom_index.rename_axis(["h_res", "h_atom"])
            .to_frame("h").reset_index()
        ),
    )).set_index(["a", "h"])

    # Extract subsets via index operations.
    rosetta_not_tmol = rosetta_hbonds.loc[
        (rosetta_hbonds.index.difference(tmol_hbonds.index))
    ]
    rosetta_not_tmol_candidate = rosetta_hbonds.loc[
        (rosetta_hbonds.index.difference(tmol_candidate_hbonds.index))
    ]
    tmol_not_rosetta = tmol_hbonds.loc[
        (tmol_hbonds.index.difference(rosetta_hbonds.index))
    ]

    # Report difference via set operator.
    assert set(rosetta_hbonds.index.tolist()) == set(
        tmol_hbonds.index.tolist()
    ), (
        f"Mismatched bb hbond identification:\n"
        f"rosetta but no tmol score:\n{rosetta_not_tmol}\n\n"
        f"rosetta but no tmol candidate:\n{rosetta_not_tmol_candidate}\n\n"
        f"tmol but no rosetta hbond:\n{tmol_not_rosetta}\n\n"
    )
