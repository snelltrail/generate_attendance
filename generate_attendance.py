from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from absl import app
from absl import flags
import pandas as pd

FLAGS = flags.FLAGS

flags.DEFINE_string('input', None, 'CSV file from Canvas.')
flags.DEFINE_string('output', 'output', 'Prefix for output files.')


def main(argv):
    print(FLAGS.input, FLAGS.output)


if __name__ == '__main__':
  app.run(main)
