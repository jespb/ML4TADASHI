from tadashi import TrEnum
from tadashi.apps import Polybench

app = Polybench("jacobi-1d")
trs = [
    [0, 4, TrEnum.PARTIAL_SHIFT_PARAM, 0, 0, -36],
    [0, 2, TrEnum.FUSE, 0, 1],
]

app.transform_list(trs)
node = app.scops[0].schedule_tree[2]
print(node.yaml_str)

a = node.available_transformations
print(a)

print(f"{node.get_args(TrEnum.FUSE, -10, 10)=}")

app.transform_list(trs)
tapp = app.generate_code()
