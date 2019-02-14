#pragma once

#include <ATen/Device.h>
#include <stdint.h>
#include <algorithm>
#include <cstddef>
#include <iterator>

#include <ATen/Functions.h>
#include <ATen/Tensor.h>
#include <torch/torch.h>

#include <tmol/utility/tensor/TensorAccessor.h>
#include <tmol/utility/tensor/TensorUtil.h>

namespace tmol {

template <typename T, size_t N, Device D, PtrTag P = PtrTag::Restricted>
struct TPack {
  at::Tensor tensor;
  tmol::TView<T, N, D, P> view;

  TPack(at::Tensor tensor, tmol::TView<T, N, D, P> view)
      : tensor(tensor), view(view){};

  TPack(at::Tensor tensor)
      : tensor(tensor), view(tmol::view_tensor<T, N, D, P>(tensor)){};

  TPack() : tensor(), view(){};

  int64_t dim() { return view.dim(); }
  int64_t size(int64_t d) { return view.size(d); }
  int64_t stride(int64_t d) { return view.stride(d); }

  // Empty
  template <
      typename std::enable_if<enable_tensor_view<T>::enabled>::type* = nullptr>
  static auto empty(at::IntList size) -> TPack<T, N, D, P> {
    return _allocate(
        [](at::IntList size, const at::TensorOptions& options) {
          return at::empty(size, options);
        },
        size);
  }

  template <
      typename Target,
      typename std::enable_if<enable_tensor_view<T>::enabled>::type* = nullptr>
  static auto empty_like(Target& other) -> TPack<T, N, D, P> {
    return _allocate_like(
        [](at::IntList size, const at::TensorOptions& options) {
          return at::empty(size, options);
        },
        other);
  }

  // Ones
  template <
      typename std::enable_if<enable_tensor_view<T>::enabled>::type* = nullptr>
  static auto ones(at::IntList size) -> TPack<T, N, D, P> {
    return _allocate(
        [](at::IntList size, const at::TensorOptions& options) {
          return at::ones(size, options);
        },
        size);
  }

  template <
      typename Target,
      typename std::enable_if<enable_tensor_view<T>::enabled>::type* = nullptr>
  static auto ones_like(Target& other) -> TPack<T, N, D, P> {
    return _allocate_like(
        [](at::IntList size, const at::TensorOptions& options) {
          return at::ones(size, options);
        },
        other);
  }

  // Zeros
  template <
      typename std::enable_if<enable_tensor_view<T>::enabled>::type* = nullptr>
  static auto zeros(at::IntList size) -> TPack<T, N, D, P> {
    return _allocate(
        [](at::IntList size, const at::TensorOptions& options) {
          return at::zeros(size, options);
        },
        size);
  }

  template <
      typename Target,
      typename std::enable_if<enable_tensor_view<T>::enabled>::type* = nullptr>
  static auto zeros_like(Target& other) -> TPack<T, N, D, P> {
    return _allocate_like(
        [](at::IntList size, const at::TensorOptions& options) {
          return at::zeros(size, options);
        },
        other);
  }

  // Full
  template <
      typename Scalar,
      typename std::enable_if<enable_tensor_view<T>::enabled>::type* = nullptr>
  static auto full(at::IntList size, Scalar value) -> TPack<T, N, D, P> {
    return _allocate(
        [value = value](at::IntList size, const at::TensorOptions& options) {
          return at::full(size, value, options);
        },
        size);
  }

  template <
      typename Scalar,
      typename Target,
      typename std::enable_if<enable_tensor_view<T>::enabled>::type* = nullptr>
  static auto full_like(Target& other, Scalar value) -> TPack<T, N, D, P> {
    return _allocate_like(
        [value = value](at::IntList size, const at::TensorOptions& options) {
          return at::full(size, value, options);
        },
        other);
  }

  // Tensor allocation interface
  template <
      typename AllocFun,
      typename std::enable_if<enable_tensor_view<T>::enabled>::type* = nullptr>
  static auto _allocate(AllocFun aten_alloc, at::IntList size)
      -> TPack<T, N, D, P> {
    typedef typename enable_tensor_view<T>::PrimitiveType BaseT;

    at::Type& target_type =
        (D == Device::CPU) ? torch::CPU(enable_tensor_view<T>::scalar_type)
                           : torch::CUDA(enable_tensor_view<T>::scalar_type);

    at::Tensor tensor;

    int64_t stride_factor = sizeof(T) / sizeof(BaseT);
    if (stride_factor == 1) {
      // The target type has a primitive layout, construct size N tensor.
      tensor = aten_alloc(size, target_type);
    } else {
      // The target type is composite, construct size N + 1 tensor with implicit
      // minor dimension for the composite type.
      std::array<int64_t, N + 1> composite_size;
      for (int i = 0; i < N; i++) {
        composite_size.at(i) = size.at(i);
      }
      composite_size.at(N) = stride_factor;

      tensor = aten_alloc(composite_size, target_type);
    }

    return TPack<T, N, D, P>(tensor);
  }

  template <
      typename AllocFun,
      typename Target,
      typename std::enable_if<enable_tensor_view<T>::enabled>::type* = nullptr>
  static auto _allocate_like(AllocFun aten_alloc, Target& other)
      -> TPack<T, N, D, P> {
    AT_ASSERTM(
        other.dim() == N, "TPack:::_allocate_like mismatched dimensionality.");

    // Via individual access to dims to support TView. (Does not exposes
    // "sizes", only dim & size.)
    int64_t dims[N];
    for (int i = 0; i < N; i++) {
      dims[i] = other.size(i);
    };

    return _allocate(aten_alloc, dims);
  }
};

}  // namespace tmol
