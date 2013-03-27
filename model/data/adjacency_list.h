/*
 * adjacency_list.h
 *
 *  Copyright (C) 2013 Diamond Light Source
 *
 *  Author: James Parkhurst
 *
 *  This code is distributed under the BSD license, a copy of which is
 *  included in the root directory of this package.
 */
#ifndef DIALS_MODEL_ADJACENCY_LIST_H
#define DIALS_MODEL_ADJACENCY_LIST_H

#include <boost/graph/adjacency_list.hpp>

namespace dials { namespace model {

  // Create the adjacency list type
  typedef boost::adjacency_list<
    boost::listS,
    boost::vecS,
    boost::undirectedS> AdjacencyList;

}} // namespace dials::model

#endif /* DIALS_MODEL_DATA_ADJACENCY_LIST_H */
