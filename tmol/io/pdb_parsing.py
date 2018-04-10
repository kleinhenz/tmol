# flake8: noqa: E2
"""Utility functions for converting pdb files to/from atom records.

Atom records are DataFrames with the records:

    "model"       : Integer model number
    "model_name"  : String model name
    "record_name" : PDB record name, assumed to be 'ATOM'
    "atomi"       : (Below) As per PDB spec, whitespace trimmed strings and parsed numeric values
    "atomn"
    "location"
    "resn"
    "chain"
    "resi"
    "insert"
    "x"
    "y"
    "z"
    "occupancy"
    "b"

"""
import pandas
import numpy
from os import path

atom_record_dtype = numpy.dtype([
    ("record_name", numpy.str, 6),
    ("modeli",      numpy.int),
    ("chaini",      numpy.int),
    ("resi",        numpy.int),
    ("atomi",       numpy.int),
    ("model",       numpy.str, 64),
    ("chain",       numpy.str, 1),
    ("resn",        numpy.str, 3),
    ("atomn",       numpy.str, 4),
    ("x",           numpy.float),
    ("y",           numpy.float),
    ("z",           numpy.float),
    ("location",    numpy.str, 1),
    ("insert",      numpy.str, 1),
    ("occupancy",   numpy.float),
    ("b",           numpy.float)
])  # yapf: disable


def parse_pdb(pdb_lines):
    """Parses pdb file into atom records.

    pdb_lines : Iterable lines, a string filename, or a string of lines in PDB format.
    """

    if isinstance(pdb_lines, str):
        if path.exists(pdb_lines):
            # Open files by default
            pdb_lines = open(pdb_lines).readlines()
        else:
            # Split single strings by line
            pdb_lines = pdb_lines.split("\n")

    model_name = ""

    atom_lines = []

    chain_breaks = []

    model_breaks = []
    model_names = []

    # Accumulate atom lines, flagging model/chain breaks on the
    # last atom of the model/chain
    for l in pdb_lines:
        if l.startswith("MODEL"):
            if model_breaks:
                model_breaks[-1] = True

            if chain_breaks:
                chain_breaks[-1] = True

            model_name = l[6:].strip()
        elif l.startswith("TER"):
            if chain_breaks:
                chain_breaks[-1] = True
        elif l.startswith("ATOM  "):
            atom_lines.append(l)

            chain_breaks.append(False)

            model_names.append(model_name)
            model_breaks.append(False)

    entries = parse_atom_lines(atom_lines)

    # Mark additional breaks if the chain code changes.
    chain_breaks = numpy.array(chain_breaks, dtype=bool)
    chain_breaks[:-1][entries["chain"][:-1] != entries["chain"][1:]] = True

    model_breaks = numpy.array(model_breaks, dtype=bool)

    def end_flags_to_segment_idx(end_flags):
        starts = numpy.zeros_like(end_flags, dtype=bool)
        starts[1:] = end_flags[:-1]
        return numpy.cumsum(starts)

    entries["model"] = model_names
    entries["modeli"] = end_flags_to_segment_idx(model_breaks)
    entries["chaini"] = end_flags_to_segment_idx(chain_breaks)

    return pandas.DataFrame(entries)


def parse_atom_lines(lines):
    """ Parses an array of pdb ATOM records into a dict of field arrays.

    1 -  6         Record name     "ATOM  "
    7 - 11         Integer         Atom serial number.
    13 - 16        Atom            Atom name.
    17             Character       Alternate location indicator.
    18 - 20        Residue name    Residue name.
    22             Character       Chain identifier.
    23 - 26        Integer         Residue sequence number.
    27             AChar           Code for insertion of residues.
    31 - 38        Real(8.3)       Orthogonal coordinates for X in Angstroms.
    39 - 46        Real(8.3)       Orthogonal coordinates for Y in Angstroms.
    47 - 54        Real(8.3)       Orthogonal coordinates for Z in Angstroms.
    55 - 60        Real(6.2)       Occupancy.
    61 - 66        Real(6.2)       Temperature factor (Default = 0.0).
    73 - 76        LString(4)      Segment identifier, left-justified.
    77 - 78        LString(2)      Element symbol, right-justified.
    79 - 80        LString(2)      Charge on the atom.
    """
    results = numpy.empty(len(lines), dtype=atom_record_dtype)
    #  yapf: disable

    results["record_name"] = numpy.vectorize(lambda s: (s[0:6])           , otypes = [numpy.str])(lines)
    results["atomi"]       = numpy.vectorize(lambda s: int(s[6:11])       , otypes = [numpy.int])(lines)
    # atomn are directly compared in modeling software, specifically rosetta, without
    # stripping whitespace, however most users use whitespace-insensitive comparisons
    #
    # atomn will be reformatted to pdb standard during output
    results["atomn"]       = numpy.vectorize(lambda s: str.strip(s[12:16]), otypes = [numpy.str])(lines)
    results["location"]    = numpy.vectorize(lambda s: str.strip(s[16:17]), otypes = [numpy.str])(lines)
    results["resn"]        = numpy.vectorize(lambda s: str.strip(s[17:20]), otypes = [numpy.str])(lines)
    results["chain"]       = numpy.vectorize(lambda s: str.strip(s[21:22]), otypes = [numpy.str])(lines)
    results["resi"]        = numpy.vectorize(lambda s: int(s[22:26])      , otypes = [numpy.int])(lines)
    results["insert"]      = numpy.vectorize(lambda s: str.strip(s[26:27]), otypes = [numpy.str])(lines)
    results["x"]           = numpy.vectorize(lambda s: float(s[30:38])    , otypes = [numpy.float])(lines)
    results["y"]           = numpy.vectorize(lambda s: float(s[38:46])    , otypes = [numpy.float])(lines)
    results["z"]           = numpy.vectorize(lambda s: float(s[46:54])    , otypes = [numpy.float])(lines)
    results["occupancy"]   = numpy.vectorize(lambda s: float(s[54:60])    , otypes = [numpy.float])(lines)
    results["b"]           = numpy.vectorize(lambda s: float(s[60:66])    , otypes = [numpy.float])(lines)
    # results["segi"]       = numpy.vectorize(lambda s: str.strip(s[72:76]), otypes = [numpy.str])(lines)
    # results["element"]    = numpy.vectorize(lambda s: str.strip(s[76:78]), otypes = [numpy.str])(lines)
    # results["charge"]     = numpy.vectorize(lambda s: float(s[78:80]), otypes     = [numpy.float])(lines)
    #  yapf: enable

    return results


def to_pdb(atom_records):
    """ Atom record DataFrame as pdb text."""
    return "".join(to_pdb_lines(atom_records))


def format_atomn(atomn):
    """ Formats atomn via pdb standard.

    If atomn is a single-letter element (N, C, O, S, H), then printed atomn record of the the format ' {atomn:<3}', else of the format '{atomn:<4}'"""

    if atomn.startswith(("H", "C", "N", "O", "S")) and len(atomn) < 4:
        return " {0:<3}".format(atomn)
    else:
        return "{0:<4}".format(atomn)


def to_pdb_lines(atom_records):
    """ Yields atom record DataFrame as pdb lines."""

    if not isinstance(atom_records, pandas.DataFrame):
        atom_records = pandas.DataFrame(atom_records)

    for model_name, records in atom_records.groupby("model"):
        yield "MODEL {}\n".format(model_name)

        for l in to_atom_lines(r for _, r in records.iterrows()):
            yield l

        yield "TER\n"
        yield "ENDMDL\n"


def to_atom_lines(atom_records):
    """Convert atom records into ATOM lines."""
    for r in atom_records:
        yield _atom_record_format.format(
            atomi=r["atomi"],
            atomn=format_atomn(r["atomn"]),
            location=r["location"],
            resn=r["resn"],
            chain=r["chain"],
            resi=r["resi"],
            insert=r["insert"],
            x=r["x"],
            y=r["y"],
            z=r["z"],
            occupancy=r["occupancy"],
            b=r["b"]
        )


_atom_record_format = (
    "ATOM  {atomi:5d} {atomn:^4}{location:^1}{resn:3s} {chain:1}{resi:4d}{insert:1s}   "
    "{x:8.3f}{y:8.3f}{z:8.3f}{occupancy:6.2f}{b:6.2f}\n"
)
