# LIBTBX_SET_DISPATCHER_NAME dev.dials.generate_tutorial_text

from __future__ import division
import os
import shutil
import libtbx.load_env # required for libtbx.env.find_in_repositories
from libtbx.test_utils import open_tmp_directory
from dials.util.procrunner import run_process

class Job(object):
  def __call__(self):
    print self.cmd
    self.result = run_process(self.cmd.split(' '))
    print "running command took {0:.2f} seconds\n".format(self.result['runtime'])
    assert self.result['exitcode'] == 0
    self.mangle_result()
    return self.result

  def mangle_result(self):
    ''' function that can be overridden to change the return values after execution '''
    pass

class dials_import(Job):

  def __init__(self):
    # find i04 bag training data, this may be part of dials_regression or xia2_regression
    if not libtbx.env.has_module("dials_regression") and not libtbx.env.has_module('xia2_regression'):
      raise RuntimeError("No dials_regression or xia2_regression module available!")

    data_dir = None

    # use the i04_weak_data for this test
    try:
      dials_regression = os.path.join(
        libtbx.env.dist_path('dials_regression'),
        "data", "i04-BAG-training")
      if os.path.isdir(dials_regression): data_dir = dials_regression
    except Exception:
      pass

    xia2_regression = os.path.join(
      abs(libtbx.env.build_path),
      'xia2_regression', 'test_data', 'i04_bag_training')
    if os.path.isdir(xia2_regression): data_dir = xia2_regression

    if data_dir is None:
      raise RuntimeError("Cannot find i04 data in either %s or %s" % (dials_regression, xia2_regression))
    self.cmd = "dials.import {0}".format(os.path.join(data_dir,"th_8_2_0*cbf"))

class dials_find_spots(Job):
  cmd = "dials.find_spots datablock.json nproc=4"

class dials_index(Job):
  cmd = "dials.index datablock.json strong.pickle"

class dials_refine_bravais_settings(Job):
  cmd = "dials.refine_bravais_settings experiments.json indexed.pickle"

class dials_reindex(Job):
  cmd = "dials.reindex indexed.pickle change_of_basis_op=a,b,c"

class dials_refine(Job):
  cmd = "dials.refine bravais_setting_9.json reindexed_reflections.pickle"

class dials_sv_refine(Job):
  cmd = "dials.refine refined_experiments.json refined.pickle scan_varying=true"

class dials_integrate(Job):
  cmd = "dials.integrate refined_experiments.json refined.pickle nproc=4"

class dials_report(Job):
  cmd = "dials.report integrated_experiments.json integrated.pickle"

  def mangle_result(self):
    self.result['stdout'] = open('dials-report.html').read()


class LogWriter(object):

  def __init__(self, log_dir):
    self.log_dir = log_dir

  def __call__(self, filename, result):
    with open(os.path.join(self.log_dir, filename), "w") as f:
      f.write(result['stdout'])

if (__name__ == "__main__") :

  cwd = os.path.abspath(os.curdir)
  tmp_dir = open_tmp_directory(suffix="generate_tutorial_text")
  os.chdir(tmp_dir)

  try:
    import_log = dials_import()()

    find_spots_log = dials_find_spots()()

    index_log = dials_index()()

    refine_bravais_settings_log = dials_refine_bravais_settings()()

    reindex_log = dials_reindex()()

    refine_log = dials_refine()()

    sv_refine_log = dials_sv_refine()()

    integrate_log = dials_integrate()()

    report_html = dials_report()()

    # if we got this far, assume it is okay to overwrite the logs
    dials_dir = libtbx.env.find_in_repositories("dials")
    log_dir = os.path.join(dials_dir, "doc", "sphinx", "documentation",
                           "tutorials", "logs")

    log_writer = LogWriter(log_dir)
    log_writer("dials.import.log", import_log)
    log_writer("dials.find_spots.log", find_spots_log)
    log_writer("dials.index.log", index_log)
    log_writer("dials.refine_bravais_settings.log", refine_bravais_settings_log)
    log_writer("dials.refine.log", sv_refine_log)
    log_writer("dials.integrate.log", integrate_log)
    log_writer("dials-report.html", report_html)

    print "Updated log files written to {0}".format(log_dir)

  finally:
    os.chdir(cwd)
    # clean up tmp dir
    shutil.rmtree(tmp_dir)
