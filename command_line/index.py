from __future__ import absolute_import, division
from __future__ import print_function

# DIALS_ENABLE_COMMAND_LINE_COMPLETION

import logging

logger = logging.getLogger("dials.command_line.index")

try:
    # try importing scipy.linalg before any cctbx modules, otherwise we
    # sometimes get a segmentation fault/core dump if it is imported after
    # scipy.linalg is a dependency of sklearn.cluster.DBSCAN
    import scipy.linalg  # import dependency
except ImportError:
    pass

import copy

import iotbx.phil
from dials.util.options import OptionParser
from dials.util.options import flatten_reflections
from dials.util.options import flatten_experiments
from dials.util.options import flatten_experiments

help_message = """

This program attempts to perform autoindexing on strong spots output by the
program dials.find_spots. The program is called with a "experiments.json" file
(as generated by dials.import) and a "strong.pickle" file (as generated by
dials.find_spots). If one or more lattices are identified given the input
list of strong spots, then the crystal orientation and experimental geometry
are refined to minimise the differences between the observed and predicted
spot centroids. The program will output an "experiments.json" file which
is similar to the input "experiments.json" file, but with the addition of the
crystal model(s), and an "indexed.pickle" file which is similar to the input
"strong.pickle" file, but with the addition of miller indices and predicted
spot centroids.

dials.index provides both one-dimensional and three-dimensional fast Fourier
transform (FFT) based methods. These can be chosen by setting the parameters
indexing.method=fft1d or indexing.method=fft3d. By default the program searches
for a primitive lattice, and then proceeds with refinement in space group P1.
If the unit_cell and space_group parameters are set, then the program will
only accept solutions which are consistent with these parameters. Space group
constraints will be enforced in refinement as appropriate.

Examples::

  dials.index experiments.json strong.pickle

  dials.index experiments.json strong.pickle unit_cell=37,79,79,90,90,90 space_group=P43212

  dials.index experiments.json strong.pickle indexing.method=fft1d

"""

phil_scope = iotbx.phil.parse(
    """\
include scope dials.algorithms.indexing.indexer.master_phil_scope
output {
  experiments = indexed_experiments.json
    .type = path
  split_experiments = False
    .type = bool
  reflections = indexed.pickle
    .type = path
  unindexed_reflections = None
    .type = path
  log = dials.index.log
    .type = str
  debug_log = dials.index.debug.log
    .type = str
}

verbosity = 1
  .type = int(value_min=0)
  .help = "The verbosity level"
""",
    process_includes=True,
)

# local overrides for refiner.phil_scope
phil_overrides = iotbx.phil.parse(
    """
refinement
{
  verbosity = 1
}
"""
)

working_phil = phil_scope.fetch(sources=[phil_overrides])


def run(phil=working_phil, args=None):
    import libtbx.load_env
    from dials.util import Sorry

    usage = "%s [options] experiments.json strong.pickle" % libtbx.env.dispatcher_name

    parser = OptionParser(
        usage=usage,
        phil=phil,
        read_reflections=True,
        read_experiments=True,
        check_format=False,
        epilog=help_message,
    )

    params, options = parser.parse_args(args=args, show_diff_phil=False)

    if __name__ == "__main__":
        from dials.util import log

        # Configure the logging
        log.config(
            params.verbosity, info=params.output.log, debug=params.output.debug_log
        )

    from dials.util.version import dials_version

    logger.info(dials_version())

    # Log the diff phil
    diff_phil = parser.diff_phil.as_str()
    if diff_phil is not "":
        logger.info("The following parameters have been modified:\n")
        logger.info(diff_phil)

    experiments = flatten_experiments(params.input.experiments)
    reflections = flatten_reflections(params.input.reflections)

    if len(experiments) == 0:
        parser.print_help()
        return

    if experiments.crystals()[0] is not None:
        known_crystal_models = experiments.crystals()
    else:
        known_crystal_models = None

    if len(reflections) == 0:
        raise Sorry("No reflection lists found in input")
    if len(reflections) > 1:
        assert len(reflections) == len(experiments)
        from scitbx.array_family import flex

        for i in range(len(reflections)):
            reflections[i]["imageset_id"] = flex.int(len(reflections[i]), i)
            if i > 0:
                reflections[0].extend(reflections[i])

    reflections = reflections[0]

    for expt in experiments:
        if (
            expt.goniometer is not None
            and expt.scan is not None
            and expt.scan.get_oscillation()[1] == 0
        ):
            expt.goniometer = None
            expt.scan = None

    from dials.algorithms.indexing.indexer import indexer_base

    idxr = indexer_base.from_parameters(
        reflections,
        experiments,
        known_crystal_models=known_crystal_models,
        params=params,
    )
    idxr.index()
    refined_experiments = idxr.refined_experiments
    reflections = copy.deepcopy(idxr.refined_reflections)
    reflections.extend(idxr.unindexed_reflections)
    if len(refined_experiments):
        if params.output.split_experiments:
            logger.info("Splitting experiments before output")
            from dxtbx.model.experiment_list import ExperimentList

            refined_experiments = ExperimentList(
                [copy.deepcopy(re) for re in refined_experiments]
            )
        logger.info("Saving refined experiments to %s" % params.output.experiments)
        idxr.export_as_json(refined_experiments, file_name=params.output.experiments)
        logger.info("Saving refined reflections to %s" % params.output.reflections)
        idxr.export_reflections(reflections, file_name=params.output.reflections)

        if params.output.unindexed_reflections is not None:
            logger.info(
                "Saving unindexed reflections to %s"
                % params.output.unindexed_reflections
            )
            idxr.export_reflections(
                idxr.unindexed_reflections,
                file_name=params.output.unindexed_reflections,
            )
            return refined_experiments, reflections, idxr.unindexed_reflections

    return refined_experiments, reflections


if __name__ == "__main__":
    run()
