import tadashi
from tadashi import TrEnum
from tadashi.apps import Polybench
from tadashi.translators import Polly


translator = [None, Polly()][1]

benchmark = "linear-algebra/blas/gemm"
compiler_options = ["-DEXTRALARGE_DATASET", "-O3" if translator is None else ""]

gemm = Polybench(
    benchmark,
    compiler_options=compiler_options,
    translator = translator,
)

print("Transforming", benchmark)
print(gemm.user_compiler_options)

gemm.compile()

print("Baseline measure:", gemm.measure())

for tile_size in [32, 128]:
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
            [1, 7, TrEnum.TILE_3D, tile_size, tile_size, tile_size],
        ]

    gemm.transform_list(trs)

    tiled = gemm.generate_code(alt_infix=f"_tiled{tile_size}")

    print("Measure with tile size %d:"%tile_size, tiled.measure())



print("DONE")
