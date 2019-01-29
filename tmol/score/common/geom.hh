#pragma once

#include <Eigen/Core>
#include <Eigen/Geometry>

#include <tmol/score/common/tuple.hh>

namespace tmol {
namespace score {
namespace common {

template <typename Real, int N>
using Vec = Eigen::Matrix<Real, N, 1>;

#define def                \
  template <typename Real> \
  auto EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE

#define Real3 Vec<Real, 3>

def distance_V(Real3 A, Real3 B)->Real { return (A - B).norm(); }

def distance_V_dV(Real3 A, Real3 B)->tuple<Real, Real3, Real3> {
  Real3 delta = (A - B);
  Real V = delta.norm();

  if (V != 0) {
    return {V, delta / V, -delta / V};
  } else {
    // Correct for nan, gradient is discontinuous across dist = 0
    return {V, Real3({0.0, 0.0, 0.0}), Real3({0.0, 0.0, 0.0})};
  }
}

def interior_angle_V(Real3 A, Real3 B)->Real {
  auto CR = A.cross(B);
  auto z_unit = CR.normalized();

  auto A_norm = A.norm();
  auto B_norm = B.norm();

  return 2 * std::atan2(CR.dot(z_unit), A_norm * B_norm + A.dot(B));
}

def interior_angle_V_dV(Real3 A, Real3 B)->tuple<Real, Real3, Real3> {
  auto CR = A.cross(B);
  auto z_unit = CR.normalized();

  auto A_norm = A.norm();
  auto B_norm = B.norm();

  return {2 * std::atan2(CR.dot(z_unit), A_norm * B_norm + A.dot(B)),
          (A / A_norm).cross(z_unit) / A_norm,
          -(B / B_norm).cross(z_unit) / B_norm};
}

def pt_interior_angle_V(Real3 A, Real3 B, Real3 C)->Real {
  Real3 BA = A - B;
  Real3 BC = C - B;
  return interior_angle_V(BA, BC);
}

def pt_interior_angle_V_dV(Real3 A, Real3 B, Real3 C)
    ->tuple<Real, Real3, Real3, Real3> {
  Real3 BA = A - B;
  Real3 BC = C - B;
  Real V;
  Real3 dV_dBA, dV_dBC;
  tie(V, dV_dBA, dV_dBC) = interior_angle_V_dV(BA, BC);
  return {V, dV_dBA, -(dV_dBA + dV_dBC), dV_dBC};
}

def cos_interior_angle_V(Real3 A, Real3 B)->Real {
  return A.dot(B) / (A.norm() * B.norm());
}

def cos_interior_angle_V_dV(Real3 A, Real3 B)->tuple<Real, Real3, Real3> {
  auto A_norm = A.norm();
  auto B_norm = B.norm();
  auto AB_norm = A.norm() * B.norm();

  auto cosAB = (A.dot(B) / AB_norm);

  return {cosAB,
          -cosAB * A / (A_norm * A_norm) + B / AB_norm,
          -cosAB * B / (B_norm * B_norm) + A / AB_norm};
}

def pt_cos_interior_angle_V(Real3 A, Real3 B, Real3 C)->Real {
  Real3 BA = A - B;
  Real3 BC = C - B;
  return cos_interior_angle_V(BA, BC);
}

def pt_cos_interior_angle_V_dV(Real3 A, Real3 B, Real3 C)
    ->tuple<Real, Real3, Real3, Real3> {
  Real3 BA = A - B;
  Real3 BC = C - B;
  Real V;
  Real3 dV_dBA, dV_dBC;
  tie(V, dV_dBA, dV_dBC) = cos_interior_angle_V_dV(BA, BC);
  return {V, dV_dBA, -(dV_dBA + dV_dBC), dV_dBC};
}

def dihedral_angle_V(Real3 I, Real3 J, Real3 K, Real3 L)->Real {
  // Blondel A, Karplus M. New formulation for derivatives of torsion angles and
  // improper torsion angles in molecular mechanics: Elimination of
  // singularities. J Comput Chem. 1996;17: 1132–1141.
  auto F = I - J;
  auto G = J - K;
  auto H = L - K;

  auto A = F.cross(G);
  auto B = H.cross(G);

  Real sign = G.dot(A.cross(B)) >= 0 ? -1.0 : 1.0;

  return sign * std::acos(A.dot(B) / (A.norm() * B.norm()));
}

def dihedral_angle_V_dV(Real3 I, Real3 J, Real3 K, Real3 L)
    ->tuple<Real, Real3, Real3, Real3, Real3> {
  // Blondel A, Karplus M. New formulation for derivatives of torsion angles and
  // improper torsion angles in molecular mechanics: Elimination of
  // singularities. J Comput Chem. 1996;17: 1132–1141.
  auto F = I - J;
  auto G = J - K;
  auto H = L - K;

  auto A = F.cross(G);
  auto B = H.cross(G);

  Real sign = G.dot(A.cross(B)) >= 0 ? -1.0 : 1.0;
  auto V = sign * std::acos(A.dot(B) / (A.norm() * B.norm()));

  return {V,
          -(G.norm() / A.dot(A)) * A,
          G.norm() / A.dot(A) * A + F.dot(G) / (A.dot(A) * G.norm()) * A
              - (H.dot(G) / (B.dot(B) * G.norm())) * B,
          -G.norm() / B.dot(B) * B - F.dot(G) / (A.dot(A) * G.norm()) * A
              + (H.dot(G) / (B.dot(B) * G.norm())) * B,
          G.norm() / B.dot(B) * B};
}

#undef Real3
#undef def

}  // namespace common
}  // namespace score
}  // namespace tmol
