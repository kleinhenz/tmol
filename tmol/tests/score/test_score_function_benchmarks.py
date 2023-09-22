import pytest
import torch
from tmol.tests.torch import zero_padded_counts

from tmol.score.score_function import ScoreFunction

# from tmol.pose.pose_stack import PoseStack
from tmol.pose.pose_stack_builder import PoseStackBuilder

from tmol.score.cartbonded.cartbonded_energy_term import CartBondedEnergyTerm
from tmol.score.disulfide.disulfide_energy_term import DisulfideEnergyTerm
from tmol.score.elec.elec_energy_term import ElecEnergyTerm
from tmol.score.hbond.hbond_energy_term import HBondEnergyTerm
from tmol.score.ljlk.ljlk_energy_term import LJLKEnergyTerm
from tmol.score.lk_ball.lk_ball_energy_term import LKBallEnergyTerm
from tmol.score.backbone_torsion.bb_torsion_energy_term import BackboneTorsionEnergyTerm


@pytest.mark.parametrize("energy_term", [LJLKEnergyTerm], ids=["ljlk"])
@pytest.mark.parametrize("n_poses", zero_padded_counts([1, 3, 10, 30, 100]))
@pytest.mark.benchmark(group="setup_res_centric_scoring")
def dont_test_res_centric_score_benchmark_setup(
    benchmark, energy_term, n_poses, rts_ubq_res, default_database, torch_device
):
    n_poses = int(n_poses)
    pose_stack1 = PoseStackBuilder.one_structure_from_polymeric_residues(
        rts_ubq_res, torch_device
    )

    pose_stack_n = PoseStackBuilder.from_poses([pose_stack1] * n_poses, torch_device)
    sfxn = ScoreFunction(default_database, torch_device)

    for st in energy_term.score_types():
        sfxn.set_weight(st, 1.0)

    @benchmark
    def render_whole_pose_scoring_module():
        scorer = sfxn.render_whole_pose_scoring_module(pose_stack_n)
        return scorer

    render_whole_pose_scoring_module


@pytest.mark.parametrize("n_poses", zero_padded_counts([1, 3, 10, 30, 100]))
@pytest.mark.parametrize("benchmark_pass", ["forward", "full", "backward"])
@pytest.mark.parametrize(
    "energy_term",
    [
        CartBondedEnergyTerm,
        DisulfideEnergyTerm,
        ElecEnergyTerm,
        HBondEnergyTerm,
        LJLKEnergyTerm,
        LKBallEnergyTerm,
        BackboneTorsionEnergyTerm,
    ],
    ids=[
        "cartbonded",
        "disulfide",
        "elec",
        "hbond",
        "ljlk",
        "lk_ball",
        "backbone_torsion",
    ],
)
@pytest.mark.benchmark(group="res_centric_score_components")
def test_res_centric_score_benchmark(
    benchmark,
    benchmark_pass,
    energy_term,
    n_poses,
    rts_ubq_res,
    default_database,
    torch_device,
):
    n_poses = int(n_poses)
    pose_stack1 = PoseStackBuilder.one_structure_from_polymeric_residues(
        rts_ubq_res, torch_device
    )
    pose_stack_n = PoseStackBuilder.from_poses([pose_stack1] * n_poses, torch_device)

    sfxn = ScoreFunction(default_database, torch_device)

    for st in energy_term.score_types():
        sfxn.set_weight(st, 1.0)

    scorer = sfxn.render_whole_pose_scoring_module(pose_stack_n)

    if benchmark_pass == "full":
        pose_stack_n.coords.requires_grad_(True)

        @benchmark
        def score_pass():
            scores = torch.sum(scorer(pose_stack_n.coords))
            scores.backward(retain_graph=True)
            return scores.cpu()

    elif benchmark_pass == "forward":

        @benchmark
        def score_pass():
            scores = torch.sum(scorer(pose_stack_n.coords))
            scores.cpu()
            return scores

    elif benchmark_pass == "backward":
        pose_stack_n.coords.requires_grad_(True)
        scores = torch.sum(scorer(pose_stack_n.coords))

        @benchmark
        def score_pass():
            scores.backward(retain_graph=True)
            return scores.cpu()

    else:
        raise NotImplementedError


@pytest.mark.parametrize("n_poses", zero_padded_counts([1, 3, 10, 30, 100]))
@pytest.mark.parametrize("benchmark_pass", ["forward", "full", "backward"])
@pytest.mark.parametrize(
    "energy_terms",
    [
        [
            CartBondedEnergyTerm,
            DisulfideEnergyTerm,
            ElecEnergyTerm,
            HBondEnergyTerm,
            LJLKEnergyTerm,
            LKBallEnergyTerm,
            BackboneTorsionEnergyTerm,
        ]
    ],
    ids=["cartbonded_disulfide_elec_hbond_ljlk_lkb_bbtorsion"],
)
@pytest.mark.benchmark(group="res_centric_combined_score_components")
def test_combined_res_centric_score_benchmark(
    benchmark,
    benchmark_pass,
    energy_terms,
    n_poses,
    rts_ubq_res,
    default_database,
    torch_device,
):
    n_poses = int(n_poses)
    pose_stack1 = PoseStackBuilder.one_structure_from_polymeric_residues(
        rts_ubq_res, torch_device
    )
    pose_stack_n = PoseStackBuilder.from_poses([pose_stack1] * n_poses, torch_device)

    sfxn = ScoreFunction(default_database, torch_device)

    for energy_term in energy_terms:
        for st in energy_term.score_types():
            sfxn.set_weight(st, 1.0)

    scorer = sfxn.render_whole_pose_scoring_module(pose_stack_n)

    if benchmark_pass == "full":
        pose_stack_n.coords.requires_grad_(True)

        @benchmark
        def score_pass():
            scores = torch.sum(scorer(pose_stack_n.coords))
            scores.backward(retain_graph=True)
            return scores.cpu()

    elif benchmark_pass == "forward":

        @benchmark
        def score_pass():
            scores = torch.sum(scorer(pose_stack_n.coords))
            scores.cpu()
            return scores

    elif benchmark_pass == "backward":
        pose_stack_n.coords.requires_grad_(True)
        scores = torch.sum(scorer(pose_stack_n.coords))

        @benchmark
        def score_pass():
            scores.backward(retain_graph=True)
            return scores.cpu()

    else:
        raise NotImplementedError
