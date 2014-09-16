/*
 * integration_ext.cc
 *
 *  Copyright (C) 2013 Diamond Light Source
 *
 *  Author: James Parkhurst
 *
 *  This code is distributed under the BSD license, a copy of which is
 *  included in the root directory of this package.
 */
#include <boost/python.hpp>
#include <boost/python/def.hpp>

namespace dials { namespace algorithms { namespace boost_python {

  using namespace boost::python;

  void export_summation();
  void export_profile_fitting_reciprocal_space();
  void export_preprocessor();
  void export_interface();
  void export_corrections();

  BOOST_PYTHON_MODULE(dials_algorithms_integration_ext)
  {
    export_summation();
    export_profile_fitting_reciprocal_space();
    export_preprocessor();
    export_interface();
    export_corrections();
  }

}}} // namespace = dials::algorithms::boost_python
