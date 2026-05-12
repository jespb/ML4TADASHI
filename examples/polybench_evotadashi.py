import argparse
from typing import Optional

from ml4tadashi.EvoTADASHI import EvoTADASHI
from ml4tadashi.EvoTADASHI import get_parser as get_mlargs_parser
from tadashi import translators
from tadashi.apps import Polybench, Simple


def get_appargs_parser(
    parser: Optional[argparse.ArgumentParser] = None,
) -> argparse.ArgumentParser:
    if not parser:
        parser = argparse.ArgumentParser()
    parser.add_argument("--cls", type=str, choices=["Pet", "Polly"], default="Pet")
    parser.add_argument("--benchmark", type=str, default="stencils/jacobi-1d")
    parser.add_argument("--base", type=str, default="examples/polybench")
    parser.add_argument("--dataset", type=str, default="LARGE")
    parser.add_argument("--oflag", type=int, default=3)
    return parser


if __name__ == "__main__":
    app_args, ml_args = get_appargs_parser().parse_known_args()
    ml_args = get_mlargs_parser().parse_args(ml_args)

    translator = None
    if app_args.cls == "Polly":
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
