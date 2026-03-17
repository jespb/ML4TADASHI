import tadashi
from tadashi import TrEnum
from tadashi.apps import Polybench

from tadashi.translators import Polly

gemm = Polybench(
    "linear-algebra/blas/gemm",
    compiler_options=["-DEXTRALARGE_DATASET", "-O3"],
    translator = Polly(),
)

print("\n\n\n"+ f"{gemm.user_compiler_options=}")

gemm.compile()

print("\n\n\n"+ f"{gemm.measure()=}")


for tile_size in [100]:
    gemm.reset_scops()

    ## Shows available transformations (they might not be legal)
    sts = gemm.scops[1].schedule_tree
    print("\n\n\n")
    for si in range(len(sts)):
        print(si, sts[si].available_transformations)

    print("\n\n\n"+ sts[0].yaml_str)

    trs = [
        #[1, TrEnum.FULL_SPLIT],
        [7, TrEnum.TILE_2D, tile_size, tile_size],
        #[3, TrEnum.TILE_2D, tile_size, tile_size],
        #[7, TrEnum.SET_PARALLEL, 0],
    ]

    print("\n\n\n",  gemm.scops[1].transform_list(trs))
        
    transformed = gemm.generate_code(alt_infix=f"_tiled{tile_size}")

    trans_measure = transformed.measure()
    print("\n\n\n")
    print("Transformed measure: %.4f" % trans_measure)
    

print("[DONE]")
