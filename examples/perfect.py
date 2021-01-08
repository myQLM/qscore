# -*- coding : utf-8 -*-
"""
@authors Simon Martiel <simon.martiel@atos.net>
@file examples/perfect.py
@brief A QScore run on a perfect simulator
"""
from qat.qscore.benchmark import QScore
from qat.plugins import ScipyMinimizePlugin
from qat.qpus import get_default_qpu

# Our QPU is composed of:
# - a variational optimizer plugin
# - a QLM/myQLM default qpu (either LinAlg or pyLinalg)

QPU = ScipyMinimizePlugin(method="COBYLA", tol=1e-4, options={"maxiter": 300}) | get_default_qpu()

benchmark = QScore(
    QPU,
    size_limit=20,  # limiting the instace sizes to 20
    depth=1,        # using an Ansatz depth of 1
    output="perfect.csv",
    rawdata="perfect.raw"
)
benchmark.run()
