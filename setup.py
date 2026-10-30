# -*- coding: utf-8 -*-
"""
Setup for qat-qscore
"""
import importlib
from setuptools import setup, find_packages


def detect_if_qaptiva():
    """
    Detects if this setup is run in a Qaptiva environment.
    If not, we will need to add myQLM to the dependencies of the package.
    """
    try:
        importlib.import_module("qat.linalg")
        print("=> Detected a Qaptiva installation. <=")
        return True
    except ModuleNotFoundError:
        print("=> No Qaptiva installation detected, adding myQLM to the dependencies. <=")
    return False


setup(
    name="qat-qscore",
    description="QScore implementation based on Bull's myQLM framework.",
    version="0.0.1",
    packages=find_packages(include=["qat.*"]),
    install_requires=["networkx", "numpy"] + ([] if detect_if_qaptiva() else ["myqlm"]),
)
