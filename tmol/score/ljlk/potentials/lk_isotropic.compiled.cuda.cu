#include <tmol/score/common/simple_dispatch.cuda.impl.cuh>

#include "lk_isotropic.dispatch.impl.hh"

namespace tmol {
namespace score {
namespace ljlk {
namespace potentials {

#define declare_dispatch(Real, Int)    \
                                       \
  template struct LKIsotropicDispatch< \
      AABBDispatch,                    \
      tmol::Device::CUDA,              \
      Real,                            \
      Int>;                            \
  template struct LKIsotropicDispatch< \
      AABBTriuDispatch,                \
      tmol::Device::CUDA,              \
      Real,                            \
      Int>;

declare_dispatch(float, int64_t);
declare_dispatch(double, int64_t);

#undef declare_dispatch

}  // namespace potentials
}  // namespace ljlk
}  // namespace score
}  // namespace tmol
