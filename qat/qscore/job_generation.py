# -*- coding : utf-8 -*-
"""
@authors Simon Martiel <simon.martiel@atos.net>
@copyright 2017-2020  Bull S.A.S.  -  All rights reserved.
           This is not Free or Open Source software.
           Please contact Bull SAS for details about its license.
           Bull - Rue Jean Jaurès - B.P. 68 - 78340 Les Clayes-sous-Bois

@file qat/qscore/job_generation.py
@brief Job generation mechanics
@namespace qat.qscore.job_generation
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
