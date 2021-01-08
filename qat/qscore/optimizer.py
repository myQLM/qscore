# -*- coding : utf-8 -*-
"""
@authors Simon Martiel <simon.martiel@atos.net>
@file qat/qscore/optimizer.py
@brief A helper function that constructs a variational optimizer
@namespace qat.qscore.optimizer
"""
from qat.plugins import ScipyMinimizePlugin


OPTIMIZER = ScipyMinimizePlugin(
    method="COBYLA",
    tol=1e-5,
    options={
        "maxiter": 300
    }
)


