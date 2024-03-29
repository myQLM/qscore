# -*- coding : utf-8 -*-
"""
@authors Simon Martiel <simon.martiel@atos.net>
@copyright 2017-2021  Bull S.A.S.  -  All rights reserved.
@file qat/qscore/benchmark.py
@brief The main benchmark class
@namespace qat.qscore.benchmark

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
import pickle
import importlib
import argparse
from datetime import datetime
import numpy as np
from .job_generation import generate_maxcut_job
from .iterators import Driver


_NB_INSTANCES_PER_SIZE = 100
_INITIAL_SIZE = 5
_DEFAULT_SIZE_LIMIT = 20
_DEFAULT_DEPTH = 1
_DEFAULT_OUT_FILE = "out.csv"
_DEFAULT_RAW_FILE = "out.raw"


_INTRO = """=== Running Q-score benchmark | {date} ===
Instances size:    {init_size} -- {final_size}
Beta:              {beta}
Ansatz depth:      {depth}
Output file:       {output}
Raw output file:   {rawdata}
Random seed:       {seed}
================================="""

_HEADER = """# Q-Score run | {date}
# Instances size:    {init_size} -- {final_size}
# Ansatz depth:      {depth}
# Beta:              {beta}
# Output file:       {output}
# Raw output file:   {rawdata}
# Random seed:       {seed}
# size, avg. score, avg. random score
"""


class QScore:
    # pylint: disable=too-many-instance-attributes
    """

    Arguments:
        qpu(:class:`~qat.core.qpu.QPUHandler`): the QPU to benchmark (including its compilation stack).
          The QPU should support variational optimization.
        initial_size(int, optional): the initial instance size to try. Default to 5.
        size_limit(int, optional): a limit on the size of MAX-CUT instances to try to solve.
          Instance sizes will vary from 5 to this limit. Default to 20.
        beta(float, optional): the threshold ratio for the test. The official test uses
          20% (0.2) as threshold. Default to 0.2
        iterator(str, optional): the iteration method to use ("exhaustive" or "dichotomic").
          Default to "dichotomic".
        depth(int, optional): the QAOA depth to use. Default to 1.
        output(str, optional): a file name to store the benchmark output (in CSV format).
          Default to out.csv.
        rawdata(str, optional): a file name in which to store the raw output of all the runs
          performed during the benchmark. Default to out.raw.
        seed(int, optional): a seed for the instances generation
    """

    def __init__(
        self,
        qpu,
        size_limit=_DEFAULT_SIZE_LIMIT,
        initial_size=_INITIAL_SIZE,
        beta=0.2,
        iterator="dichotomic",
        depth=_DEFAULT_DEPTH,
        output=_DEFAULT_OUT_FILE,
        rawdata=_DEFAULT_RAW_FILE,
        seed=None,
    ):
        self._executor = qpu
        self._size_limit = size_limit
        self._iterator = iterator
        self._initial_size = initial_size
        self._depth = depth
        self._output = output
        self._rawdata = rawdata
        self._seed = seed if seed is not None else np.random.randint(100000)
        self._beta = beta

    def run(self):
        """
        Runs the benchmark.
        """
        date_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        print(
            _INTRO.format(
                date=date_string,
                init_size=self._initial_size,
                final_size=self._size_limit,
                beta=self._beta,
                depth=self._depth,
                output=self._output,
                rawdata=self._rawdata,
                seed=self._seed,
            )
        )
        all_data = {}
        seed = self._seed
        to_output = _HEADER.format(
            date=date_string,
            init_size=self._initial_size,
            beta=self._beta,
            final_size=self._size_limit,
            depth=self._depth,
            output=self._output,
            rawdata=self._rawdata,
            seed=self._seed,
        )

        def _evaluate_point(size, seed=seed, to_output=to_output, self=self):
            """
            Function that evaluates a single point.
            """
            print(f"Running for n={size:2d}.", end=" ", flush=True)
            scores = []
            data = []
            for _ in range(_NB_INSTANCES_PER_SIZE):
                job = generate_maxcut_job(size, self._depth, seed=seed)
                result = self._executor.submit(job)
                scores.append(-result.value)
                data.append({"seed": seed, "score": -result.value})
                seed += 1
            average_score = np.mean(scores) - size * (size - 1) / 8
            avg_best_score = 0.178 * pow(size, 3 / 2)
            print(f"Score: {average_score:.2f}.", end=" ")
            print(f"Random best score: {avg_best_score:.2f}.", end="\t")
            to_output = f"{size},{average_score},{avg_best_score}\n"
            all_data[size] = data
            pickle.dump(all_data, open(self._rawdata, "wb"))
            with open(self._output, "a") as fout:
                fout.write(to_output)
            achieved_ratio = average_score / avg_best_score
            if achieved_ratio > self._beta:
                print("Success.")
            else:
                print("Fail.")
            return achieved_ratio - self._beta

        success, _, info = Driver(_evaluate_point, self._iterator, self._initial_size, self._size_limit).run()

        if success:
            print(f"Success. QScore({self._beta}) = {info}")
        else:
            if info[0]:
                print(f"Failure. QScore({self._beta}) > {info[1]}")
                print("Maybe try to increase the max instance size !")
            else:
                print(f"Failure. QScore({self._beta}) < {info[1]}")


_PARSER = argparse.ArgumentParser(prog="qscore")
_PARSER.add_argument("qpu", type=str, help="The QPU to benchmark in 'module:object' format")
_PARSER.add_argument(
    "--plugin",
    action="append",
    default=[],
    help=(
        "Plugins to add to the QPU. They will be added from inside out (i.e first"
        " Plugin will end up the closest to the QPU). Plugins are specified in the same"
        " way as QPUs."
    ),
)
_PARSER.add_argument(
    "--sizelimit",
    type=int,
    default=20,
    help=(
        "A limit on the size of MAX-CUT instances to try to solve. Instance sizes will" " vary from 5 to this limit. Default to 20."
    ),
)
_PARSER.add_argument("--depth", type=int, default=1, help="The QAOA depth to use. Default to 1.")
_PARSER.add_argument(
    "--output",
    type=str,
    default="out.csv",
    help=("A file name to store the benchmark output (in CSV format). Default to out.csv"),
)
_PARSER.add_argument(
    "--rawdata",
    type=str,
    default="out.raw",
    help=("A file name in which to store the raw output of all the runs performed during" " the benchmark. Default to out.raw."),
)
_PARSER.add_argument("--seed", type=int, default=None, help="A seed for the instances generation.")


def _load_qpu(argument, plugins):
    """
    Load a QPU from its command line argument.
    """
    module_name, object_name = argument.split(":")
    module = importlib.import_module(module_name)
    qpu = module.__dict__[object_name]
    if isinstance(qpu, type):
        qpu = qpu()
    for plugin in plugins:
        module_name, object_name = plugin.split(":")
        module = importlib.import_module(module_name)
        plugin = module.__dict__[object_name]
        qpu = plugin | qpu
    return qpu


if __name__ == "__main__":
    arguments = _PARSER.parse_args()
    QPU = _load_qpu(arguments.qpu, arguments.plugin)
    QScore(
        QPU,
        size_limit=arguments.sizelimit,
        depth=arguments.depth,
        output=arguments.output,
        rawdata=arguments.rawdata,
        seed=arguments.seed,
    ).run()
