import attr
import cattr

from tmol.types.functional import validate_args
from tmol.types.attrs import ValidateAttrs
from tmol.types.array import NDArray

import numpy
import pandas

from tmol.database.scoring import HBondDatabase

acceptor_dtype = numpy.dtype([
    ("a", int),
    ("b", int),
    ("b0", int),
    ("acceptor_type", object),
])

donor_dtype = numpy.dtype([
    ("d", int),
    ("h", int),
    ("donor_type", object),
])


@attr.s(frozen=True, slots=True, auto_attribs=True)
class HBondElementAnalysis(ValidateAttrs):
    donors: NDArray(donor_dtype)[:]
    sp2_acceptors: NDArray(acceptor_dtype)[:]
    sp3_acceptors: NDArray(acceptor_dtype)[:]
    ring_acceptors: NDArray(acceptor_dtype)[:]

    @classmethod
    @validate_args
    def setup(
            cls,
            hbond_database: HBondDatabase,
            atom_types: NDArray(object)[:],
            bonds: NDArray(int)[:, 2],
    ):
        bond_types = atom_types[bonds]

        bond_table = pandas.DataFrame.from_dict({
            "i_i": bonds[:, 0],
            "i_t": bond_types[:, 0],
            "j_i": bonds[:, 1],
            "j_t": bond_types[:, 1],
        })

        def inc_cols(*args):
            order = {"i": "j", "j": "k"}
            res = []
            for n in args:
                nn = order[n]
                res.append((n + "_i", nn + "_i"))
                res.append((n + "_t", nn + "_t"))
            return dict(res)

        def df_to_struct(df):
            rec = df.to_records(index=False)
            return rec.view(rec.dtype.fields)

        if hbond_database.atom_groups.donors:
            donor_types = pandas.DataFrame.from_records(
                cattr.unstructure(hbond_database.atom_groups.donors)
            )
            donor_table = pandas.merge(
                donor_types,
                bond_table,
                how="inner",
                left_on=["d", "h"],
                right_on=["i_t", "j_t"]
            )
            donor_pairs = {"i_i": "d", "j_i": "h", "donor_type": "donor_type"}
            donors = df_to_struct(
                donor_table[list(donor_pairs)].rename(columns=donor_pairs)
            )
        else:
            donors = numpy.empty(0, donor_dtype)

        if hbond_database.atom_groups.sp2_acceptors:
            sp2_acceptor_types = pandas.DataFrame.from_records(
                cattr.unstructure(hbond_database.atom_groups.sp2_acceptors)
            )
            sp2_ab_table = pandas.merge(
                sp2_acceptor_types,
                bond_table,
                how="inner",
                left_on=["a", "b"],
                right_on=["i_t", "j_t"]
            )
            sp2_bb0_table = pandas.merge(
                sp2_acceptor_types,
                bond_table.rename(columns=inc_cols("i", "j")),
                how="inner",
                left_on=["b", "b0"],
                right_on=["j_t", "k_t"]
            )
            sp2_acceptor_table = pandas.merge(sp2_ab_table, sp2_bb0_table)
            sp2_pairs = {
                "i_i": "a",
                "j_i": "b",
                "k_i": "b0",
                "acceptor_type": "acceptor_type"
            }
            sp2_acceptors = df_to_struct(
                sp2_acceptor_table[list(sp2_pairs)].rename(columns=sp2_pairs)
            )
        else:
            sp2_acceptors = numpy.empty(0, acceptor_dtype)

        if hbond_database.atom_groups.sp3_acceptors:
            sp3_acceptor_types = pandas.DataFrame.from_records(
                cattr.unstructure(hbond_database.atom_groups.sp3_acceptors)
            )
            sp3_ab_table = pandas.merge(
                sp3_acceptor_types,
                bond_table,
                how="inner",
                left_on=["a", "b"],
                right_on=["i_t", "j_t"]
            )
            sp3_ab0_table = pandas.merge(
                sp3_acceptor_types,
                bond_table.rename(columns=inc_cols("j")),
                how="inner",
                left_on=["a", "b0"],
                right_on=["i_t", "k_t"]
            )
            sp3_acceptor_table = pandas.merge(sp3_ab_table, sp3_ab0_table)
            sp3_pairs = {
                "i_i": "a",
                "j_i": "b",
                "k_i": "b0",
                "acceptor_type": "acceptor_type"
            }
            sp3_acceptors = df_to_struct(
                sp3_acceptor_table[list(sp3_pairs)].rename(columns=sp3_pairs)
            )
        else:
            sp3_acceptors = numpy.empty(0, acceptor_dtype)

        if hbond_database.atom_groups.ring_acceptors:
            ring_acceptor_types = pandas.DataFrame.from_records(
                cattr.unstructure(hbond_database.atom_groups.ring_acceptors)
            ).rename(columns={"bp": "b0"})
            ring_ab_table = pandas.merge(
                ring_acceptor_types,
                bond_table,
                how="inner",
                left_on=["a", "b"],
                right_on=["i_t", "j_t"]
            )
            ring_ab0_table = pandas.merge(
                ring_acceptor_types,
                bond_table.rename(columns=inc_cols("j")),
                how="inner",
                left_on=["a", "b0"],
                right_on=["i_t", "k_t"]
            )
            ring_acceptor_table = pandas.merge(ring_ab_table, ring_ab0_table)
            ring_pairs = {
                "i_i": "a",
                "j_i": "b",
                "k_i": "b0",
                "acceptor_type": "acceptor_type"
            }
            ring_acceptors = df_to_struct(
                ring_acceptor_table[list(ring_pairs)].rename(
                    columns=ring_pairs
                )
            )
        else:
            ring_acceptors = numpy.empty(0, acceptor_dtype)

        return cls(
            donors=donors,
            sp2_acceptors=sp2_acceptors,
            sp3_acceptors=sp3_acceptors,
            ring_acceptors=ring_acceptors,
        )
