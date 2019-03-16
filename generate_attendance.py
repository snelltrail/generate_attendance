# TODO break everything out into separate functions
# TODO use protobuffs to improve serialization/communication?, essentially allow
# config in a json-like format
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from absl import app
from absl import flags

import pandas as pd
import os
import subprocess
import collections
import textwrap

from tqdm import tqdm

FLAGS = flags.FLAGS

flags.DEFINE_string("input", None, "CSV file from Canvas.")
flags.DEFINE_string("output", "output.csv", "Suffix for output files.")
flags.DEFINE_string("number", None, "Tutorial number")
flags.DEFINE_string(
    "metadata", "tutorial_metadata.tsv", "File containing tutorial metadata"
)
# TODO Input parsing, check e.g. a valid number is given

TEX_BOILERPLATE = textwrap.dedent(
    r"""
    \documentclass[14pt, a4paper]{{article}}
    \usepackage{{tabularx, extsizes}}
    \usepackage[margin=1in]{{geometry}}
    \usepackage[table]{{xcolor}}
    \usepackage{{longtable, tabu}}

    \newcommand{{\mathpaper}}{{{}}}
    \newcommand{{\tutorialnumber}}{{{}}}
    \newcommand{{\tutorialgroup}}{{{}}}
    \newcommand{{\tutorialtimeplace}}{{{}}}
    \newcommand{{\tutorname}}{{{}}}

    \newcolumntype{{Y}}{{>{{\centering\arraybackslash}}X}}
    \renewcommand{{\familydefault}}{{\sfdefault}}

    \pagestyle{{empty}}

    \begin{{document}}

    \begin{{center}}
    {{\mathpaper}}\\
    \vspace{{10pt}}
    {{Tutorial group: \tutorialgroup}}\\
    \vspace{{10pt}}
    {{\tutorialtimeplace}}\\
    \end{{center}}

    \begin{{longtabu}} to \textwidth {{X Y}}
      Tutor: \tutorname & Tutorial number: \tutorialnumber
    \end{{longtabu}}

    \begin{{center}}
    \rowcolors{{2}}{{gray!25}}{{white}}
    \tabulinesep=2.0mm
    \begin{{longtabu}} to \textwidth {{ | c | Y | Y | c | c | }} \hline
      \rowcolor{{gray!50}}
      & First name & Last name & ID Number & UPI\\ \hline
    {}
    \end{{longtabu}}
    \end{{center}}

    \end{{document}}"""
)


def generate_tex(paper, tutorial_number, tutorial_group, time, tutor, data):
    """Returns contents of an attendance sheet as a tex file.

    Args:
        paper: String describing the paper, e.g. "Maths 108".
        tutorial_number: The tutorial number for that week, e.g. 1. 
        tutorial_group: The id for the tutorial, e.g. 1.
        time: The time of the tutorial, e.g. "3pm".
        tutor: The name of the tutor, e.g. "Daniel".
        data: A dataframe with columns "First Name", "Last Name", "ID Number",
            "UPI", "Tutorial".

    Returns:
        The tex file as a string.
    """
    # Add a row for each student.
    table_rows = []
    for i, row in enumerate(data.iterrows()):
        _, student_info = row
        table_rows.append(
            "{row_num} & & & {id_num} & {upi} \\\ \hline".format(
                row_num=i + 1, id_num=student_info["ID Number"], upi=student_info["UPI"]
            )
        )
    # Add blank rows at bottom of the sheet.
    table_rows.extend(
        ["{} &  &  &  & \\\ \hline".format(i) for i in range(len(data.index) + 1, 51)]
    )
    table = "\n".join(table_rows)
    return TEX_BOILERPLATE.format(
        paper, tutorial_number, tutorial_group, time, tutor, table
    )


def main(argv):
    os.mkdir(FLAGS.output)
    df = pd.read_csv(FLAGS.input).filter(
        items=["Student", "SIS User ID", "SIS Login ID", "Section"]
    )
    initial_length = len(df)
    # More readable column titles
    df = df.rename(columns={"SIS User ID": "ID Number", "SIS Login ID": "UPI"})

    df = df[df["ID Number"].notna()]
    df["ID Number"] = df["ID Number"].astype(int)
    # Just get the tutorial number
    df["Tutorial"] = df["Section"].apply(lambda x: x.split()[-1][1:-1])
    df["Tutorial"] = df["Tutorial"].astype(int)
    df["First Name"] = ""
    df["Last Name"] = ""
    df = df.filter(items=["First Name", "Last Name", "ID Number", "UPI", "Tutorial"])
    tutorials_nums = sorted(pd.unique(df["Tutorial"]))
    # Should construct a dictionary of tut_group: named tuple where the tuple
    # makes sure all the metadata for a given tutorial is bundled together
    tutorials = {i: df[df["Tutorial"] == i] for i in tutorials_nums}

    # TODO two dictionaries needed here?

    # Now need to generate the .tex files

    full_tut = collections.namedtuple("full_tut", ["details", "tutor"])
    complete_tuts = {}

    # TODO get rid of .tsv, use separate columns and csv instead; still read in
    # without pandas
    with open(FLAGS.metadata) as f:
        next(f)
        for row in f:
            group, details, tutor = row.strip().split("\t")
            complete_tuts[int(group)] = full_tut(details=details, tutor=tutor)

    for i, tut in tqdm(tutorials.items()):
        output_string = generate_tex(
            "Math 108 Tutorial Attendance",
            FLAGS.number,
            str(i),
            complete_tuts[i].details,
            complete_tuts[i].tutor,
            tut,
        )

        output_file = (
            FLAGS.output + "tut" + str(i)
            if FLAGS.output[-4:] == ".tex"
            else FLAGS.output + "tut" + str(i) + ".tex"
        )
        with open(FLAGS.output + "/" + output_file, "w") as f:
            f.write(output_string)

        with open(os.devnull, "w") as devnull:
            subprocess.run(
                ["latexmk", "-pdf", "-cd", FLAGS.output + "/" + output_file],
                stdout=devnull,
                stderr=devnull,
            )
            subprocess.run(
                ["latexmk", "-c", "-cd", FLAGS.output + "/" + output_file],
                stdout=devnull,
                stderr=devnull,
            )
            os.remove(FLAGS.output + "/" + output_file)


if __name__ == "__main__":
    app.run(main)
