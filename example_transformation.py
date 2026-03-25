import tadashi
from tadashi import TrEnum
from tadashi.apps import Polybench
from tadashi.translators import Polly




def print_available_transformations(app):
    """
    Prints available transformations (they might not be legal)
    """
    for s in [1]: #range(len(app.scops)):
        st = app.scops[s].schedule_tree
        for n in range(len(st)):
            print("%3d, %3d," %(s, n), st[n].available_transformations)





translator = [None, Polly()][1]

gemm = Polybench(
    "linear-algebra/blas/gemm",
    compiler_options=["-DEXTRALARGE_DATASET"],
    translator = translator,
)

print(f"{gemm.user_compiler_options=}")

gemm.compile()

#print(f"{gemm.measure()=}")

#oa = str(gemm.dump_arrays())

for tile_size in [64,100]:
    gemm.reset_scops()

    sts = gemm.scops[1].schedule_tree

    #print("\n\n\n"+ sts[1].yaml_str)


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

    #print("\n\n\n"+ sts[1].yaml_str)

    tiled = gemm.generate_code(alt_infix=f"_tiled{tile_size}")
    tiled = gemm.generate_code(alt_infix=f"_tiled{tile_size}")

    print(f"{tile_size=} : {tiled.measure()=}")

    #na = str(gemm.dump_arrays())

    #print("Matches original output:", oa==na)


print("DONE")
