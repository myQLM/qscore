# -*- coding : utf-8 -*-

"""
@authors Simon Martiel <simon.martiel@atos.net>
@copyright 2017-2021  Bull S.A.S.  -  All rights reserved.
@file qat/qscore/iterators.py
@brief Two simple iterators (an exhaustive enumeration and a dichotomic search)
@namespace qat.qscore.iterators
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


def _exhaustive(start_size, end_size):
    """
    Iterates over all the values of the domain until it finds a negative value.
    """
    values = dict()
    for index in range(start_size, end_size + 1):
        value = yield index
        values[index] = value
        if value < 0:
            if index == start_size:
                return False, value, (False, start_size)
            return True, values, index - 1
    return False, values, (True, max(values), values[max(values)])


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
        return False, values, (True, max(values), values[max(values)])
    if values[lower] < 0:
        return False, value, (False, start_size)
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
