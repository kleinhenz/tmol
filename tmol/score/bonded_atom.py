import torch
import numpy

import scipy.sparse

from tmol.utility.reactive import reactive_attrs, reactive_property

from tmol.types.array import NDArray
from tmol.types.torch import Tensor


@reactive_attrs(auto_attribs=True)
class BondedAtomScoreGraph:
    # Number of atoms in the system
    system_size: int

    # String atom types
    atom_types: NDArray(object)[:]

    # Inter-atomic bond indices
    bonds: NDArray(int)[:, 2]

    @reactive_property
    def real_atoms(atom_types: NDArray(object)[:], ) -> Tensor(bool)[:]:
        """Mask of 'real' atomic indices in the system."""
        return (torch.ByteTensor((atom_types != None).astype(numpy.ubyte))
                )  # noqa: E711 - None != is a vectorized check for None.

    @reactive_property
    def bonded_path_length(
            bonds: NDArray(int)[:, 2],
            system_size: int,
    ) -> NDArray("f4")[:, :]:
        """Dense inter-atomic bonded path length distance matrix."""
        return scipy.sparse.csgraph.shortest_path(
            scipy.sparse.coo_matrix(
                (
                    numpy.ones(bonds.shape[0], dtype=bool),
                    (bonds[:, 0], bonds[:, 1])
                ),
                shape=(system_size, system_size),
            ),
            directed=False,
            unweighted=True
        ).astype("f4")
