import tadashi
from tadashi import TrEnum
from tadashi.apps import Polybench

base = "examples/polybench"

gemm = Polybench(
    "linear-algebra/blas/gemm",
    base,
    compiler_options=["-DEXTRALARGE_DATASET", "-O3"],
)

print(f"{gemm.user_compiler_options=}")

gemm.compile()

print(f"{gemm.measure()=}")


for tile_size in [31, 100]:
    gemm.reset_scops()
    trs = [
        [0, 2, TrEnum.FULL_SPLIT],
        [0, 7, TrEnum.TILE_3D, tile_size, tile_size, tile_size],
    ]
    gemm.transform_list(trs)
        
    tiled = gemm.generate_code(alt_infix=f"_tiled{tile_size}", ephemeral=False)

    tiled.compile()    
    print(f"{tile_size=} : {tiled.measure()=}")

print("DONE")
