#pragma once

#include <Eigen/Core>

#include <tmol/utility/tensor/TensorAccessor.h>

namespace tmol {
namespace score {
namespace common {

template <tmol::Device D>
struct AABBDispatch {
  template <typename Real, typename Func>
  void forall_pairs(
      Real threshold_distance,
      TView<Eigen::Matrix<Real, 3, 1>, 1, D> coords_i,
      TView<Eigen::Matrix<Real, 3, 1>, 1, D> coords_j,
      Func f);
};

template <tmol::Device D>
struct AABBTriuDispatch {
  template <typename Real, typename Func>
  int forall_pairs(
      Real threshold_distance,
      TView<Eigen::Matrix<Real, 3, 1>, 1, D> coords_i,
      TView<Eigen::Matrix<Real, 3, 1>, 1, D> coords_j,
      Func f);
};

}  // namespace common
}  // namespace score
}  // namespace tmol
