"""validate script."""

import sys

from absl import app
from absl import flags
from absl import logging
from ml_croissant import Dataset, ValidationError

flags.DEFINE_string(
    "file",
    None,
    "Path to the file to validate.",
)

flags.DEFINE_bool(
    "debug",
    False,
    "Whether to print debug hints.",
)

flags.mark_flag_as_required("file")


FLAGS = flags.FLAGS


def main(argv):
    del argv
    file = FLAGS.file
    debug = FLAGS.debug
    try:
        Dataset(file, debug=debug)
        logging.info("Done.")
    except ValidationError as exception:
        logging.error(exception)
        sys.exit(1)


if __name__ == "__main__":
    app.run(main)
