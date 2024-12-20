from __future__ import annotations

import os

import pytest

import scitbx
from cctbx import uctbx
from dxtbx.serialize import load

from dials.command_line import search_beam_position

from ..algorithms.indexing.test_index import run_indexing


def test_search_i04_weak_data_image_range(mocker, run_in_tmp_path, dials_data):
    """Perform a beam-centre search and check that the output is sane."""

    data_dir = dials_data("i04_weak_data")
    reflection_file = data_dir / "full.pickle"
    experiments_file = data_dir / "experiments_import.json"

    args = [
        str(experiments_file),
        str(reflection_file),
        "image_range=1,10",
        "image_range=251,260",
        "image_range=531,540",
        "n_macro_cycles=4",
    ]
    from rstbx.indexing_api import dps_extended

    mocker.spy(dps_extended, "get_new_detector")
    search_beam_position.run(args)
    # Check that the last call to get_new_detector was with an offset of close to zero.
    # The final call was to apply the "best" shift to the detector model before
    # returning the updated experiments.
    assert dps_extended.get_new_detector.call_args[0][1].elems == pytest.approx(
        (0, 0, 0), abs=3e-2
    )
    assert os.path.exists("optimised.expt")

    # Compare the shifts between the start and final detector models
    experiments = load.experiment_list(experiments_file, check_format=False)
    optimised_experiments = load.experiment_list("optimised.expt", check_format=False)
    detector_1 = experiments[0].detector
    detector_2 = optimised_experiments[0].detector
    shift = scitbx.matrix.col(detector_1[0].get_origin()) - scitbx.matrix.col(
        detector_2[0].get_origin()
    )
    assert shift.elems == pytest.approx((0.27, -0.12, 0.0), abs=1e-1)


def test_search_multiple(run_in_tmp_path, dials_data):
    """Perform a beam-centre search and check that the output is sane.

    Do the following:
    1. Run dials.search_beam_centre on two experiments and two pickled
    reflection tables, as output by dials.find_spots;
      a) Check that the program exits correctly;
      b) Check that it produces the expected output experiment.
    2. Check that the beam centre search has resulted in the expected shift
    in detector origin.
    """

    data_dir = dials_data("semisynthetic_multilattice")
    refl_path1 = str(data_dir / "ag_strong_1_50.refl")
    refl_path2 = str(data_dir / "bh_strong_1_50.refl")
    experiments_path1 = str(data_dir / "ag_imported_1_50.expt")
    experiments_path2 = str(data_dir / "bh_imported_1_50.expt")

    args = [experiments_path1, experiments_path2, refl_path1, refl_path2]
    search_beam_position.run(args)
    assert os.path.exists("optimised.expt")

    experiments = load.experiment_list(experiments_path1, check_format=False)
    optimised_experiments = load.experiment_list("optimised.expt", check_format=False)
    detector_1 = experiments[0].detector
    detector_2 = optimised_experiments[0].detector
    shift = scitbx.matrix.col(detector_1[0].get_origin()) - scitbx.matrix.col(
        detector_2[0].get_origin()
    )
    assert shift.elems == pytest.approx((-0.090, -0.168, 0.0), abs=1e-1)


def test_index_after_search(dials_data, run_in_tmp_path):
    """Integrate the beam centre search with the rest of the toolchain

    Do the following:
    1. Take a known good experiment and perturb the beam centre
    2. Run dials.search_beam_centre on the perturbated beam centre and original
    reflection table, check for expected output;
    3. Run dials.index with the found beam centre and check that the expected
    unit cell is obtained and that the RMSDs are smaller than or equal to some
    expected values."""

    insulin = dials_data("insulin_processed", pathlib=True)

    # load the original experiment and perturb the beam centre by a small offset
    experiments = load.experiment_list(insulin / "imported.expt", check_format=False)
    original_origin = experiments[0].detector.hierarchy().get_origin()
    shifted_origin = (
        original_origin[0] - 1.3,
        original_origin[1] + 1.5,
        original_origin[2],
    )
    experiments[0].detector.hierarchy().set_local_frame(
        experiments[0].detector.hierarchy().get_fast_axis(),
        experiments[0].detector.hierarchy().get_slow_axis(),
        shifted_origin,
    )
    assert experiments[0].detector.hierarchy().get_origin() == shifted_origin
    experiments.as_file(run_in_tmp_path / "shifted.expt")

    # search the beam centre
    search_beam_position.run(
        [
            str(run_in_tmp_path / "shifted.expt"),
            str(insulin / "strong.refl"),
        ]
    )
    assert run_in_tmp_path.joinpath("optimised.expt").is_file()

    # check we can actually index the resulting optimized experiments
    expected_unit_cell = uctbx.unit_cell(
        (67.655, 67.622, 67.631, 109.4583, 109.4797, 109.485)
    )
    expected_rmsds = (0.3, 0.3, 0.005)
    expected_hall_symbol = " P 1"
    run_indexing(
        insulin / "strong.refl",
        run_in_tmp_path / "optimised.expt",
        run_in_tmp_path,
        [],
        expected_unit_cell,
        expected_rmsds,
        expected_hall_symbol,
    )


def test_search_single(dials_data, run_in_tmp_path):
    """Perform a beam-centre search and check that the output is sane.

    Do the following:
    1. Run dials.search_beam_centre on a single experiment and pickled
    reflection table, as output by dials.find_spots;
      a) Check that the program exits correctly;
      b) Check that it produces the expected output experiment.
    2. Check that the beam centre search has resulted in the expected shift
    in detector origin.
    """

    insulin = dials_data("insulin_processed", pathlib=True)
    refl_path = insulin / "strong.refl"
    experiments_path = insulin / "imported.expt"

    search_beam_position.run([str(experiments_path), str(refl_path)])
    assert run_in_tmp_path.joinpath("optimised.expt").is_file()

    experiments = load.experiment_list(experiments_path, check_format=False)
    original_imageset = experiments.imagesets()[0]
    optimized_experiments = load.experiment_list("optimised.expt", check_format=False)
    detector_1 = original_imageset.get_detector()
    detector_2 = optimized_experiments.detectors()[0]
    shift = scitbx.matrix.col(detector_1[0].get_origin()) - scitbx.matrix.col(
        detector_2[0].get_origin()
    )
    assert shift.elems == pytest.approx((-0.165, -0.380, 0.0), abs=1e-1)


def test_search_small_molecule(dials_data, run_in_tmp_path):
    """Perform a beam-centre search on a multi-sequence data set..

    Do the following:
    1. Run dials.search_beam_centre on a single experiment and pickled
    reflection table containing multiple experiment IDs, as output by
    dials.find_spots;
      a) Check that the program exits correctly;
      b) Check that it produces the expected output experiment.
    2. Check that the beam centre search has resulted in the expected shift
    in detector origin.
    """

    data = dials_data("l_cysteine_dials_output", pathlib=True)
    experiments_path = data / "imported.expt"
    refl_path = data / "strong.refl"

    search_beam_position.run([os.fspath(experiments_path), os.fspath(refl_path)])
    assert run_in_tmp_path.joinpath("optimised.expt").is_file()

    experiments = load.experiment_list(experiments_path, check_format=False)
    optimised_experiments = load.experiment_list("optimised.expt", check_format=False)
    for old_expt, new_expt in zip(experiments, optimised_experiments):
        # assert that the detector fast/slow axes are unchanged from the input experiments
        # the last experiment actually does have a different detector model
        assert (
            old_expt.detector[0].get_slow_axis() == new_expt.detector[0].get_slow_axis()
        )
        assert (
            old_expt.detector[0].get_fast_axis() == new_expt.detector[0].get_fast_axis()
        )
        shift = scitbx.matrix.col(
            old_expt.detector[0].get_origin()
        ) - scitbx.matrix.col(new_expt.detector[0].get_origin())
        assert shift.elems == pytest.approx((0.091, -1.11, 0), abs=1e-2)


def test_multi_sweep_fixed_rotation(dials_data, run_in_tmp_path):
    data = dials_data("l_cysteine_dials_output", pathlib=True)
    experiments_path = data / "imported.expt"
    refl_path = data / "strong.refl"

    search_beam_position.run([str(experiments_path), str(refl_path)])
    assert run_in_tmp_path.joinpath("optimised.expt").is_file()

    experiments = load.experiment_list(experiments_path, check_format=False)
    optimised_experiments = load.experiment_list("optimised.expt", check_format=False)

    for orig_expt, new_expt in zip(experiments, optimised_experiments):
        shift = scitbx.matrix.col(
            orig_expt.detector[0].get_origin()
        ) - scitbx.matrix.col(new_expt.detector[0].get_origin())
        print(shift)
        assert shift.elems == pytest.approx((0.096, -1.111, 0), abs=1e-2)
