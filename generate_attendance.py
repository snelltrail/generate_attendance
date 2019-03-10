from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from absl import app
from absl import flags

import pandas as pd

FLAGS = flags.FLAGS

flags.DEFINE_string("input", None, "CSV file from Canvas.")
flags.DEFINE_string("output", "output.csv", "Suffix for output files.")


def main(argv):
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
    tutorials_nums = sorted(pd.unique(df["Tutorial"]))
    tutorials = [df[df["Tutorial"] == i] for i in tutorials_nums]

    for tut, i in zip(tutorials, tutorials_nums):
        tut.to_csv(
            "tut" + "{:02d}".format(i) + FLAGS.output,
            index=False,
            columns=["First Name", "Last Name", "ID Number", "UPI", "Tutorial"],
        )

    # Now we write the data to the .tex file

    with open("output1.tex", "r+") as f:

if __name__ == "__main__":
    app.run(main)
