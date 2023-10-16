import numpy
import torch

from .pdb_parsing import parse_pdb

ordered_canonical_aa_types = (
    "ALA",
    "CYS",
    "ASP",
    "GLU",
    "PHE",
    "GLY",
    "HIS",
    "ILE",
    "LYS",
    "LEU",
    "MET",
    "ASN",
    "PRO",
    "GLN",
    "ARG",
    "SER",
    "THR",
    "VAL",
    "TRP",
    "TYR",
)

# PDB v3 naming convention
ordered_canonical_aa_atoms = {
    "ALA": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "H",
        "H1",
        "H2",
        "H3",
        "HA",
        "HB1",
        "HB2",
        "HB3",
    ),
    "CYS": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "SG",
        "H",
        "H1",
        "H2",
        "H3",
        "HA",
        "HB2",
        "HB3",
        "HG",
    ),
    "ASP": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "CG",
        "OD1",
        "OD2",
        "H",
        "H1",
        "H2",
        "H3",
        "HA",
        "HB2",
        "HB3",
    ),
    "GLU": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "CG",
        "CD",
        "OE1",
        "OE2",
        "H",
        "H1",
        "H2",
        "H3",
        "HA",
        "HB2",
        "HB3",
        "HG2",
        "HG3",
    ),
    "PHE": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "CG",
        "CD1",
        "CD2",
        "CE1",
        "CE2",
        "CZ",
        "H",
        "H1",
        "H2",
        "H3",
        "HA",
        "HB2",
        "HB3",
        "HD1",
        "HD2",
        "HE1",
        "HE2",
        "HZ",
    ),
    "GLY": ("N", "CA", "C", "O", "OXT", "H", "H1", "H2", "H3", "HA1", "HA2"),
    "HIS": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "CG",
        "ND1",
        "CD2",
        "CE1",
        "NE2",
        "NH",
        "NN",
        "H",
        "H1",
        "H2",
        "H3",
        "HA",
        "HB2",
        "HB3",
        "HD1",
        "HD2",
        "HE1",
        "HE2",
        "HN",
    ),
    "ILE": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "CG1",
        "CG2",
        "CD1",
        "H",
        "H1",
        "H2",
        "H3",
        "HA",
        "HB",
        "HG12",
        "HG13",
        "HG21",
        "HG22",
        "HG23",
        "HD11",
        "HD12",
        "HD13",
    ),
    "LYS": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "CG",
        "CD",
        "CE",
        "NZ",
        "H",
        "H1",
        "H2",
        "H3",
        "HA",
        "HB2",
        "HB3",
        "HG2",
        "HG3",
        "HD2",
        "HD3",
        "HE2",
        "HE3",
        "HZ1",
        "HZ2",
        "HZ3",
    ),
    "LEU": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "CG",
        "CD1",
        "CD2",
        "H",
        "H1",
        "H2",
        "H3",
        "HA",
        "HB2",
        "HB3",
        "HG",
        "HD11",
        "HD12",
        "HD13",
        "HD21",
        "HD22",
        "HD23",
    ),
    "MET": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "CG",
        "SD",
        "CE",
        "H",
        "H1",
        "H2",
        "H3",
        "HA",
        "HB2",
        "HB3",
        "HG2",
        "HG3",
        "HE1",
        "HE2",
        "HE3",
    ),
    "ASN": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "CG",
        "OD1",
        "ND2",
        "H",
        "H1",
        "H2",
        "H3",
        "HA",
        "HB2",
        "HB3",
        "HD21",
        "HD22",
    ),
    "PRO": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "CG",
        "CD",
        "H",
        "H1",
        "H2",
        "HA",
        "HB2",
        "HB3",
        "HG2",
        "HG3",
        "HD2",
        "HD3",
    ),
    "GLN": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "CG",
        "CD",
        "OE1",
        "NE2",
        "H",
        "H1",
        "H2",
        "H3",
        "HA",
        "HB2",
        "HB3",
        "HG2",
        "HG3",
        "HE21",
        "HE22",
    ),
    "ARG": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "CG",
        "CD",
        "NE",
        "CZ",
        "NH1",
        "NH2",
        "H",
        "H1",
        "H2",
        "H3",
        "HA",
        "HB2",
        "HB3",
        "HG2",
        "HG3",
        "HD2",
        "HD3",
        "HE",
        "HH11",
        "HH12",
        "HH21",
        "HH22",
    ),
    "SER": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "OG",
        "H",
        "H1",
        "H2",
        "H3",
        "HA",
        "HB2",
        "HB3",
        "HG",
    ),
    "THR": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "OG1",
        "CG2",
        "H",
        "H1",
        "H2",
        "H3",
        "HA",
        "HB",
        "HG1",
        "HG21",
        "HG22",
        "HG23",
    ),
    "VAL": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "CG1",
        "CG2",
        "H",
        "H1",
        "H2",
        "H3",
        "HA",
        "HB",
        "HG11",
        "HG12",
        "HG13",
        "HG21",
        "HG22",
        "HG23",
    ),
    "TRP": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "CG",
        "CD1",
        "CD2",
        "NE1",
        "CE2",
        "CE3",
        "CZ2",
        "CZ3",
        "CH2",
        "H",
        "H1",
        "H2",
        "H3",
        "HA",
        "HB2",
        "HB3",
        "HD1",
        "HE1",
        "HE3",
        "HZ2",
        "HZ3",
        "HH2",
    ),
    "TYR": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "CG",
        "CD1",
        "CD2",
        "CE1",
        "CE2",
        "CZ",
        "OH",
        "H",
        "H1",
        "H2",
        "H3",
        "HA",
        "HB2",
        "HB3",
        "HD1",
        "HD2",
        "HE1",
        "HE2",
        "HH",
    ),
}

# The "old" PDB atom ordering, listed in the same order as V3 so
# that if you want to read in a PDB that has hydrogens in V2 you
# can put them into the canonical ordering that assumes V3 naming
# and and everything downstream will work just fine
ordered_canonical_aa_atoms_v2 = {
    "ALA": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "H",
        "1H",
        "2H",
        "3H",
        "HA",
        "1HB",
        "2HB",
        "3HB",
    ),
    "CYS": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "SG",
        "H",
        "1H",
        "2H",
        "3H",
        "HA",
        "1HB",
        "2HB",
        "HG",
    ),
    "ASP": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "CG",
        "OD1",
        "OD2",
        "H",
        "1H",
        "2H",
        "3H",
        "HA",
        "1HB",
        "2HB",
    ),
    "GLU": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "CG",
        "CD",
        "OE1",
        "OE2",
        "H",
        "1H",
        "2H",
        "3H",
        "HA",
        "1HB",
        "2HB",
        "1HG",
        "2HG",
    ),
    "PHE": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "CG",
        "CD1",
        "CD2",
        "CE1",
        "CE2",
        "CZ",
        "H",
        "1H",
        "2H",
        "3H",
        "HA",
        "1HB",
        "2HB",
        "HD1",
        "HD2",
        "HE1",
        "HE2",
        "HZ",
    ),
    "GLY": ("N", "CA", "C", "O", "OXT", "H", "1H", "2H", "3H", "1HA", "2HA"),
    "HIS": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "CG",
        "ND1",
        "CD2",
        "CE1",
        "NE2",
        "NH",
        "NN",
        "H",
        "1H",
        "2H",
        "3H",
        "HA",
        "1HB",
        "2HB",
        "HD1",
        "HD2",
        "HE1",
        "HE2",
        "HN",
    ),
    "ILE": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "CG1",
        "CG2",
        "CD1",
        "H",
        "1H",
        "2H",
        "3H",
        "HA",
        "HB",
        "1HG1",
        "2HG1",
        "1HG2",
        "2HG2",
        "3HG2",
        "1HD1",
        "2HD1",
        "3HD1",
    ),
    "LYS": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "CG",
        "CD",
        "CE",
        "NZ",
        "H",
        "1H",
        "2H",
        "3H",
        "HA",
        "1HB",
        "2HB",
        "1HG",
        "2HG",
        "1HD",
        "2HD",
        "1HE",
        "2HE",
        "1HZ",
        "2HZ",
        "3HZ",
    ),
    "LEU": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "CG",
        "CD1",
        "CD2",
        "H",
        "1H",
        "2H",
        "3H",
        "HA",
        "1HB",
        "2HB",
        "HG",
        "1HD1",
        "2HD1",
        "3HD1",
        "1HD2",
        "2HD2",
        "3HD2",
    ),
    "MET": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "CG",
        "SD",
        "CE",
        "H",
        "1H",
        "2H",
        "3H",
        "HA",
        "1HB",
        "2HB",
        "1HG",
        "2HG",
        "1HE",
        "2HE",
        "3HE",
    ),
    "ASN": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "CG",
        "OD1",
        "ND2",
        "H",
        "1H",
        "2H",
        "3H",
        "HA",
        "1HB",
        "2HB",
        "1HD2",
        "2HD2",
    ),
    "PRO": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "CG",
        "CD",
        "H",
        "1H",
        "2H",
        "HA",
        "1HB",
        "2HB",
        "1HG",
        "2HG",
        "1HD",
        "2HD",
    ),
    "GLN": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "CG",
        "CD",
        "OE1",
        "NE2",
        "H",
        "1H",
        "2H",
        "3H",
        "HA",
        "1HB",
        "2HB",
        "1HG",
        "2HG",
        "1HE2",
        "2HE2",
    ),
    "ARG": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "CG",
        "CD",
        "NE",
        "CZ",
        "NH1",
        "NH2",
        "H",
        "1H",
        "2H",
        "3H",
        "HA",
        "1HB",
        "2HB",
        "1HG",
        "2HG",
        "1HD",
        "2HD",
        "HE",
        "1HH1",
        "2HH1",
        "1HH2",
        "2HH2",
    ),
    "SER": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "OG",
        "H",
        "1H",
        "2H",
        "3H",
        "HA",
        "1HB",
        "2HB",
        "HG",
    ),
    "THR": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "OG1",
        "CG2",
        "H",
        "1H",
        "2H",
        "3H",
        "HA",
        "HB",
        "HG1",
        "1HG2",
        "2HG2",
        "3HG2",
    ),
    "VAL": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "CG1",
        "CG2",
        "H",
        "1H",
        "2H",
        "3H",
        "HA",
        "HB",
        "1HG1",
        "2HG1",
        "3HG1",
        "1HG2",
        "2HG2",
        "3HG2",
    ),
    "TRP": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "CG",
        "CD1",
        "CD2",
        "NE1",
        "CE2",
        "CE3",
        "CZ2",
        "CZ3",
        "CH2",
        "H",
        "1H",
        "2H",
        "3H",
        "HA",
        "1HB",
        "2HB",
        "HD1",
        "HE1",
        "HE3",
        "HZ2",
        "HZ3",
        "HH2",
    ),
    "TYR": (
        "N",
        "CA",
        "C",
        "O",
        "OXT",
        "CB",
        "CG",
        "CD1",
        "CD2",
        "CE1",
        "CE2",
        "CZ",
        "OH",
        "H",
        "1H",
        "2H",
        "3H",
        "HA",
        "1HB",
        "2HB",
        "HD1",
        "HD2",
        "HE1",
        "HE2",
        "HH",
    ),
}


max_n_canonical_atoms = max(
    len(atlist) for _, atlist in ordered_canonical_aa_atoms.items()
)


def canonical_form_from_pdb_lines(pdb_lines, device):
    ##### TEMP!!!! #####
    # USE PDB V2 FOR NOW!
    atom_records = parse_pdb(pdb_lines)
    uniq_res_ind = {}
    uniq_res_list = []
    count_uniq = -1
    for i, row in atom_records.iterrows():
        resid = (row["chain"], row["resi"], row["insert"])
        if resid not in uniq_res_ind:
            count_uniq += 1
            uniq_res_ind[resid] = count_uniq
            uniq_res_list.append(resid)
    n_res = len(uniq_res_list)

    chain_id = numpy.zeros((1, n_res), dtype=numpy.int32)
    res_types = numpy.full((1, n_res), -2, dtype=numpy.int32)
    coords = numpy.full(
        (1, n_res, max_n_canonical_atoms, 3), numpy.NAN, dtype=numpy.float32
    )
    atom_is_present = numpy.zeros((1, n_res, max_n_canonical_atoms), dtype=numpy.int32)

    chains_seen = {}
    chain_id_counter = 0  # TO DO: determine if this is wholly redundant w/ "chaini"
    for i, row in atom_records.iterrows():
        resid = (row["chain"], row["resi"], row["insert"])
        res_ind = uniq_res_ind[resid]
        if row["chaini"] not in chains_seen:
            chains_seen[row["chaini"]] = chain_id_counter
            chain_id_counter += 1
        chain_id[0, res_ind] = chains_seen[row["chaini"]]
        if res_types[0, res_ind] == -2:
            try:
                aa_ind = ordered_canonical_aa_types.index(row["resn"])
                res_types[0, res_ind] = aa_ind
            except KeyError:
                res_types[0, res_ind] = -1
        if res_types[0, res_ind] >= 0:
            # TEMP!!!!! We should probably either read v3 by default or detect v2 vs v3 automatically #
            res_at_list = ordered_canonical_aa_atoms_v2[row["resn"]]

            atname = row["atomn"].strip()
            try:
                atind = res_at_list.index(atname)
                atom_is_present[0, res_ind, atind] = 1
                coords[0, res_ind, atind, 0] = row["x"]
                coords[0, res_ind, atind, 1] = row["y"]
                coords[0, res_ind, atind, 2] = row["z"]
            except KeyError:
                # ignore atoms that are not in the canonical form
                # TO DO: warn the user that some atoms are not being processed?
                pass

    def _ti32(x):
        return torch.tensor(x, dtype=torch.int32, device=device)

    def _tf32(x):
        return torch.tensor(x, dtype=torch.float32, device=device)

    return _ti32(chain_id), _ti32(res_types), _tf32(coords), _ti32(atom_is_present)