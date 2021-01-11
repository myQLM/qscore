# -*- coding : utf-8 -*-
"""
@authors Simon Martiel <simon.martiel@atos.net>
@copyright 2017-2021  Bull S.A.S.  -  All rights reserved.
           This is not Free or Open Source software.
           Please contact Bull SAS for details about its license.
           Bull - Rue Jean Jaurès - B.P. 68 - 78340 Les Clayes-sous-Bois

@file qat/qscore/benchmark.py
@brief The main benchmark class
@namespace qat.qscore.benchmark
"""
import pickle
import importlib
import argparse
from datetime import datetime
import numpy as np
from qat.qscore.job_generation import generate_maxcut_job

"""
Things to improve:

*********
Currently the QPU is expected to support variational optimization.
We could ask the user to provide a QPU and a compilation stack separately, and take care of
inserting the proper variational optimizer in between.
"""


_NB_INSTANCES_PER_SIZE = 40
_INITIAL_SIZE = 5
_DEFAULT_SIZE_LIMIT = 20
_DEFAULT_DEPTH = 1
_DEFAULT_OUT_FILE = "out.csv"
_DEFAULT_RAW_FILE = "out.raw"


_INTRO = """=== Running Q-score benchmark | {date} ===
Instances size:    {init_size} -- {final_size}
Ansatz depth:      {depth}
Output file:       {output}
Raw output file:   {rawdata}
Random seed:       {seed}
================================="""

_HEADER = """# Q-Score run | {date}
# Instances size:    {init_size} -- {final_size}
# Ansatz depth:      {depth}
# Output file:       {output}
# Raw output file:   {rawdata}
# Random seed:       {seed}
# size, avg. score, avg. random score
"""


class QScore:
    """
    # TODO #

    Arguments:
        qpu(:class:`~qat.core.qpu.QPUHandler`): the QPU to benchmark (including its compilation stack).
          The QPU should support variational optimization.
        size_limit(int, optional): a limit on the size of MAX-CUT instances to try to solve.
          Instance sizes will vary from 5 to this limit. Default to 20.
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
        depth=_DEFAULT_DEPTH,
        output=_DEFAULT_OUT_FILE,
        rawdata=_DEFAULT_RAW_FILE,
        seed=None,
    ):
        self._executor = qpu
        self._size_limit = size_limit
        self._depth = depth
        self._output = output
        self._rawdata = rawdata
        self._seed = seed if seed is not None else np.random.randint(100000)

    def run(self):
        """
        Runs the benchmark.
        """
        date_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        print(
            _INTRO.format(
                date=date_string,
                init_size=_INITIAL_SIZE,
                final_size=self._size_limit,
                depth=self._depth,
                output=self._output,
                rawdata=self._rawdata,
                seed=self._seed,
            )
        )
        all_data = {}
        largest_pass = 0
        seed = self._seed
        to_output = _HEADER.format(
            date=date_string,
            init_size=_INITIAL_SIZE,
            final_size=self._size_limit,
            depth=self._depth,
            output=self._output,
            rawdata=self._rawdata,
            seed=self._seed,
        )
        for size in range(_INITIAL_SIZE, self._size_limit + 1):
            print("Running for n={:2d}.".format(size), end=" ", flush=True)
            scores = []
            data = []
            for index in range(_NB_INSTANCES_PER_SIZE):
                job = generate_maxcut_job(size, self._depth, seed=seed)
                result = self._executor.submit(job)
                scores.append(-result.value)
                data.append({"seed": seed, "score": -result.value})
                seed += 1
            all_data[size] = data
            average_score = np.mean(scores)
            print("Score: {:.2f}.".format(average_score), end=" ")
            print("Random score: {:.2f}.".format(size * (size - 1) / 8), end="\t")
            to_output += "{},{},{}\n".format(size, average_score, size * (size - 1) / 8)
            if average_score > size * (size - 1) / 8:  # TODO check this
                print("Pass.")
                largest_pass = size
            else:
                print("Fail.")
                break
        print("Q-Score of", largest_pass)
        pickle.dump(all_data, open(self._rawdata, "wb"))
        with open(self._output, "w") as fout:
            fout.write(to_output)


_PARSER = argparse.ArgumentParser(prog="qscore")
_PARSER.add_argument(
    "qpu", type=str, help="The QPU to benchmark in 'module:object' format"
)
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
        "A limit on the size of MAX-CUT instances to try to solve. Instance sizes will"
        " vary from 5 to this limit. Default to 20."
    ),
)
_PARSER.add_argument(
    "--depth", type=int, default=1, help="The QAOA depth to use. Default to 1."
)
_PARSER.add_argument(
    "--output",
    type=str,
    default="out.csv",
    help=(
        "A file name to store the benchmark output (in CSV format). Default to out.csv"
    ),
)
_PARSER.add_argument(
    "--rawdata",
    type=str,
    default="out.raw",
    help=(
        "A file name in which to store the raw output of all the runs performed during"
        " the benchmark. Default to out.raw."
    ),
)
_PARSER.add_argument(
    "--seed", type=int, default=None, help="A seed for the instances generation."
)


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
