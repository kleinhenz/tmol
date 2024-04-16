import pytest
from pytest import approx

from tmol.score.modules.bases import ScoreSystem
from tmol.score.modules.ljlk import LJScore, LKScore
from tmol.score.modules.coords import coords_for


module_comparisons = {
    "lj_regression": (LJScore, {"lj": -177.242}),
    "lk_regression": (LKScore, {"lk": 298.275}),
}


@pytest.mark.parametrize(
    "score_method,expected_scores",
    list(module_comparisons.values()),
    ids=list(module_comparisons.keys()),
)
def test_baseline_comparison_modules(
    ubq_system, torch_device, score_method, expected_scores
):
    weight_factor = 10.0
    weights = {t: weight_factor for t in expected_scores}

    score_system: ScoreSystem = ScoreSystem.build_for(
        ubq_system,
        {score_method},
        weights=weights,
        device=torch_device,
        drop_missing_atoms=False,
    )

    coords = coords_for(ubq_system, score_system, requires_grad=False)

    scores = score_system.intra_forward(coords)

    assert {k: float(v) for k, v in scores.items()} == approx(expected_scores, rel=1e-3)

    total_score = score_system.intra_total(coords)
    assert float(total_score) == approx(
        sum(expected_scores.values()) * weight_factor, rel=1e-3
    )
