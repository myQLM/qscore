# -*- coding : utf-8 -*-
"""
@authors Simon Martiel <simon.martiel@atos.net>
@copyright 2017-2020  Bull S.A.S.  -  All rights reserved.
@file qat/qscore/job_generation.py
@brief Job generation mechanics
@namespace qat.qscore.job_generation
    Licensed to the Apache Software Foundation (ASF) under one
    or more contributor license agreements.  See the NOTICE file
    distributed with this work for additional information
    regarding copyright ownership.  The ASF licenses this file
    to you under the Apache License, Version 2.0 (the
    "License"); you may not use this file except in compliance
    with the License.  You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing,
    software distributed under the License is distributed on an
    "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
    KIND, either express or implied.  See the License for the
    specific language governing permissions and limitations
    under the License.
"""
import networkx as nx
from qat.vsolve.qaoa import MaxCut


def generate_maxcut_job(size, depth, seed=None):
    """
    Generate a QAOA-MAX-CUT job for a random Erdos-Renyi graph of a given size.

    Arguments:
        size(int): the size of the graph
        depth(int): the depth of the Ansatz
        seed(int, optional): the seed for the graph generation
    """
    graph = nx.generators.erdos_renyi_graph(size, 0.5, seed=seed)
    instance = MaxCut(graph)
    return instance.qaoa_ansatz(depth)
