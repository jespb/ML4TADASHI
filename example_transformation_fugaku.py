import tadashi
from tadashi import TrEnum
from tadashi.apps import Polybench

from tadashi.translators import Polly


def print_available_transformations(app):
    """
    Prints available transformations (they might not be legal)
    """
    for s in range(len(app.scops)):
        st = app.scops[s].schedule_tree
        for n in range(len(st)):
            print("%3d, %3d," %(s, n), st[n].available_transformations)


gemm = Polybench(
    "linear-algebra/blas/gemm",
    compiler_options=["-DEXTRALARGE_DATASET", "-O3"],
    translator = Polly(),
)

print("\n\n\n"+ f"{gemm.user_compiler_options=}")

gemm.compile()

#print("\n\n\n"+ f"{gemm.measure()=}")


for tile_size in [128]:
    gemm.reset_scops()

    ## Shows available transformations (they might not be legal)
    #print("\n\n\n")
    #print_available_transformations(gemm)

    sts = gemm.scops[1].schedule_tree

    print("\n\n\n"+ sts[1].yaml_str)

    trs = [
        [1, 2, TrEnum.FULL_SPLIT],
	#[0, 7, TrEnum.INTERCHANGE],
        #[1, 12, TrEnum.TILE_2D, tile_size, tile_size],
        #[1, 7, TrEnum.TILE_2D, tile_size, tile_size],
        #[7, TrEnum.SET_PARALLEL, 0],
    ]

    print("\n\n\n",  gemm.transform_list(trs))


    #print("\n\n\n")
    #print_available_transformations(gemm)

    print("\n\n\n"+ sts[1].yaml_str)


    transformed = gemm.generate_code(alt_infix=f"_tiled{tile_size}", ephemeral=False, populate_scops=True)
    trans_measure = transformed.measure()

    print("\n\n\n"+ transformed.scops[1].schedule_tree[1].yaml_str)


    print("\n\n\n")
    print("Transformed measure: %.4f" % trans_measure)


print("[DONE]")
