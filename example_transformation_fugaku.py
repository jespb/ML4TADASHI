import tadashi
from tadashi import TrEnum
from tadashi.apps import Polybench

from tadashi.translators import Polly

gemm = Polybench(
    "linear-algebra/blas/gemm",
    compiler_options=["-DEXTRALARGE_DATASET", "-O3"],
    translator = Polly(),
)

print(f"{gemm.user_compiler_options=}")

gemm.compile()

print(f"{gemm.measure()=}")


for tile_size in [100]:
    gemm.reset_scops()

    ## Shows available transformations (they might not be legal)
    sts = gemm.scops[1].schedule_tree
    for si in range(len(sts)):
        print(si, sts[si].available_transformations)

    print(sts[0].yaml_str)

    trs = [
        #[0, 1, TrEnum.FULL_SPLIT],
        [1, 7, TrEnum.TILE_2D, tile_size, tile_size],
        #[0, 3, TrEnum.TILE_2D, tile_size, tile_size],
        #[1, 7, TrEnum.SET_PARALLEL, 0],
    ]

    gemm.transform_list(trs)

    #sts = gemm.scops[0].schedule_tree
    #for si in range(len(sts)):
    #    print(si, sts[si].available_transformations)
        
    #gemm.transform_list(trs)
        
    tiled = gemm.generate_code(alt_infix=f"_tiled{tile_size}", ephemeral=False)

    tiled.compile()    
    print(f"{tile_size=} : {tiled.measure()=}")

print("DONE")
