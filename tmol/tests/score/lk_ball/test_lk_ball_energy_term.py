import numpy
import torch

from tmol.score.lk_ball.lk_ball_energy_term import LKBallEnergyTerm

from tmol.pose.pose_stack_builder import PoseStackBuilder

from tmol.tests.autograd import gradcheck


def test_smoke(default_database, torch_device):
    lk_ball_energy = LKBallEnergyTerm(param_db=default_database, device=torch_device)

    assert lk_ball_energy.device == torch_device


def test_annotate_restypes(
    fresh_default_packed_block_types, default_database, torch_device
):
    lk_ball_energy = LKBallEnergyTerm(param_db=default_database, device=torch_device)

    pbt = fresh_default_packed_block_types

    first_params = {}
    for bt in pbt.active_block_types:
        lk_ball_energy.setup_block_type(bt)
        assert hasattr(bt, "hbbt_params")
        first_params[bt.name] = bt.hbbt_params

    for bt in pbt.active_block_types:
        # test that block-type annotation is not repeated;
        # original annotation is still present in the bt
        lk_ball_energy.setup_block_type(bt)
        assert first_params[bt.name] is bt.hbbt_params

    lk_ball_energy.setup_packed_block_types(pbt)
    assert hasattr(pbt, "lk_ball_params")

    init_pbt_lk_ball_params = pbt.lk_ball_params
    lk_ball_energy.setup_packed_block_types(pbt)
    # test that the initial packed-block-types annotation
    # has not been repeated; initial annotation is still
    # present in the pbt
    assert init_pbt_lk_ball_params is pbt.lk_ball_params

    assert pbt.lk_ball_params.tile_n_polar_atoms.device == torch_device
    assert pbt.lk_ball_params.tile_n_occluder_atoms.device == torch_device
    assert pbt.lk_ball_params.tile_pol_occ_inds.device == torch_device
    assert pbt.lk_ball_params.tile_lk_ball_params.device == torch_device


def test_whole_pose_scoring_module_smoke(rts_ubq_res, default_database, torch_device):
    gold_vals = numpy.array(
        [[421.00595092], [171.192932], [1.57858872], [10.99459934]], dtype=numpy.float32
    )
    lk_ball_energy = LKBallEnergyTerm(param_db=default_database, device=torch_device)
    p1 = PoseStackBuilder.one_structure_from_polymeric_residues(
        res=rts_ubq_res, device=torch_device
    )
    for bt in p1.packed_block_types.active_block_types:
        lk_ball_energy.setup_block_type(bt)
    lk_ball_energy.setup_packed_block_types(p1.packed_block_types)
    lk_ball_energy.setup_poses(p1)

    lk_ball_pose_scorer = lk_ball_energy.render_whole_pose_scoring_module(p1)

    coords = torch.nn.Parameter(p1.coords.clone())
    scores = lk_ball_pose_scorer(coords)

    # make sure we're still good
    torch.arange(100, device=torch_device)
    numpy.testing.assert_allclose(
        gold_vals, scores.cpu().detach().numpy(), atol=1e-3, rtol=1e-3
    )


def test_whole_pose_scoring_module_gradcheck_partial_pose(
    rts_ubq_res, default_database, torch_device
):
    lk_ball_energy = LKBallEnergyTerm(param_db=default_database, device=torch_device)
    p1 = PoseStackBuilder.one_structure_from_polymeric_residues(
        res=rts_ubq_res[6:12], device=torch_device
    )
    for bt in p1.packed_block_types.active_block_types:
        lk_ball_energy.setup_block_type(bt)
    lk_ball_energy.setup_packed_block_types(p1.packed_block_types)
    lk_ball_energy.setup_poses(p1)

    lk_ball_pose_scorer = lk_ball_energy.render_whole_pose_scoring_module(p1)

    weights = torch.tensor(
        [[0.75], [1.25], [0.625], [0.8125]], dtype=torch.float32, device=torch_device
    )

    def score(coords):
        scores = lk_ball_pose_scorer(coords)

        wtd_score = torch.sum(weights * scores)
        return wtd_score

    gradcheck(
        score,
        (p1.coords.requires_grad_(True),),
        eps=1e-3,
        atol=1e-2,
        rtol=1e-2,
        nondet_tol=1e-3,
    )


def test_whole_pose_scoring_module_10(rts_ubq_res, default_database, torch_device):
    n_poses = 10
    gold_vals = numpy.tile(
        numpy.array(
            [[421.00595092], [171.192932], [1.57858872], [10.99459934]],
            dtype=numpy.float32,
        ),
        (n_poses),
    )
    lk_ball_energy = LKBallEnergyTerm(param_db=default_database, device=torch_device)
    p1 = PoseStackBuilder.one_structure_from_polymeric_residues(
        res=rts_ubq_res, device=torch_device
    )
    pn = PoseStackBuilder.from_poses([p1] * n_poses, device=torch_device)

    for bt in pn.packed_block_types.active_block_types:
        lk_ball_energy.setup_block_type(bt)
    lk_ball_energy.setup_packed_block_types(pn.packed_block_types)
    lk_ball_energy.setup_poses(pn)

    lk_ball_pose_scorer = lk_ball_energy.render_whole_pose_scoring_module(pn)

    coords = torch.nn.Parameter(pn.coords.clone())
    scores = lk_ball_pose_scorer(coords)

    # make sure we're still good
    torch.arange(100, device=torch_device)

    numpy.testing.assert_allclose(
        gold_vals, scores.cpu().detach().numpy(), atol=1e-5, rtol=1e-5
    )
