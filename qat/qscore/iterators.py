# -*- coding : utf-8 -*-

"""
@authors Simon Martiel <simon.martiel@atos.net>
@copyright 2017-2021  Bull S.A.S.  -  All rights reserved.
           This is not Free or Open Source software.
           Please contact Bull SAS for details about its license.
           Bull - Rue Jean Jaurès - B.P. 68 - 78340 Les Clayes-sous-Bois

@file qat/qscore/iterators.py
@brief Two simple iterators (an exhaustive enumeration and a dichotomic search)
@namespace qat.qscore.iterators
"""


def _exhaustive(start_size, end_size):
    """"""
    values = dict()
    for index in range(start_size, end_size + 1):
        value = yield index
        values[index] = value
        if value < 0:
            if index == start_size:
                return False, value, None
            return True, values, index - 1
    return False, values, None


def _dichotomic(start_size, end_size):
    """"""
    lower = start_size
    upper = end_size
    value = yield lower
    values = dict()
    values[lower] = value
    value = yield upper
    values[upper] = value

    if values[upper] > 0:
        return False, values, None
    if values[lower] < 0:
        return False, value, None
    while True:
        if abs(upper - lower) <= 1:
            return True, values, lower
        next_index = (upper + lower) // 2
        values[next_index] = yield next_index
        if values[next_index] < 0:
            upper = next_index
        else:
            lower = next_index


GENERATORS = {"exhaustive": _exhaustive, "dichotomic": _dichotomic}


class Driver:
    """
    Drives the interaction with an iterator.

    Arguments:
        fun(callable): the evaluation function.
          It should take an index and return a score.
        iteration(str): either "exhaustive" or "dichotomic"
        start_size(int): the start size (i.e the lowest index)
        end_size(int): the end size (i.e the highest index)
    """

    def __init__(self, fun, iteration, start_size, end_size):
        if iteration not in GENERATORS:
            raise ValueError(f"Unknown iteration method {iteration}")
        self.generator = GENERATORS[iteration](start_size, end_size)
        self.fun = fun

    def run(self):
        """
        Runs the iteration and returns a tuple containing:
        - the success status (True, if an index exists such that f(index) > 0 and f(index + 1) <= 0, False otherwise)
        - a map<index, value> containing all the evaluated point
        - if found, the index such that f(index) > 0 and f(index + 1) <= 0
        """
        index = next(self.generator)
        while True:
            try:
                index = self.generator.send(self.fun(index))
            except StopIteration as exp:
                return exp.value
        return False, {}, None


if __name__ == "__main__":
    import numpy as np
    MAX_V = 10000 - 1
    SOME = np.random.randint(0, MAX_V)
    ARRAY = list(range(MAX_V))

    def some_function(index):
        return (SOME - ARRAY[index]) + 1e-3

    success, values, index = Driver(
        some_function, "exhaustive", 0, MAX_V - 1
    ).run()
    print(success, index, values[index])

    success, values, index = Driver(
        some_function, "dichotomic", 0, MAX_V - 1
    ).run()
    print(success, index, values[index])

