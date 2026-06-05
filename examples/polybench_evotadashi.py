import argparse
from typing import Optional

from ml4tadashi.EvoTADASHI import EvoTADASHI
from ml4tadashi.EvoTADASHI import get_parser as get_mlargs_parser
from tadashi import translators
from tadashi.apps import Polybench

if __name__ == "__main__":
    app_args, ml_args = Polybench.args_parser().parse_known_args()
    ml_args = get_mlargs_parser().parse_args(ml_args)

    translator = None
    if app_args.translator == "Polly":
        translator = translators.Polly()
    else:
        translator = translators.Pet()

    app = Polybench(
        app_args.benchmark,
        compiler_options=[f"-D{app_args.dataset}_DATASET", f"-O{app_args.oflag}"],
        translator=translator,
    )

    method = EvoTADASHI(app, **vars(ml_args))

    print(f"{ml_args=}")
    print(f"{app_args=}")
    method.fit()
