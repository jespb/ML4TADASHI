import tadashi
from tadashi import TrEnum
from tadashi.apps import Polybench
from tadashi.translators import Polly


translator = [None, Polly()][1]

gemm = Polybench(
    "linear-algebra/blas/gemm",
    compiler_options=["-DEXTRALARGE_DATASET"],
    translator = translator,
)

print(f"{gemm.user_compiler_options=}")

gemm.compile()

print(f"{gemm.measure()=}")


for tile_size in [64,100]:
    gemm.reset_scops()

    if translator is None:
        trs = [
            [0, 2, TrEnum.FULL_SPLIT],
            [0, 7, TrEnum.TILE_3D, tile_size, tile_size, tile_size],
        ]
    else:
        # The lists are different across translators
        trs = [
            [1, 2, TrEnum.FULL_SPLIT],
            [1, 7, TrEnum.TILE_2D, tile_size, tile_size],
        ]

    gemm.transform_list(trs)

    tiled = gemm.generate_code(alt_infix=f"_tiled{tile_size}")

    tiled.compile()
    print(f"{tile_size=} : {tiled.measure()=}")

print("DONE")
