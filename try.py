from tadashi import TrEnum
from tadashi.apps import Polybench
from tadashi.scop import TRANSFORMATIONS

app = Polybench("jacobi-1d")
trs = [
    [0, 4, TrEnum.PARTIAL_SHIFT_PARAM, 0, 0, -36],
    [0, 2, TrEnum.FUSE, 0, 1],
]

app.transform_list(trs)
node = app.scops[0].schedule_tree[3]
tr = TrEnum.FUSE
T = TRANSFORMATIONS[tr]

# print(node.yaml_str)

a = node.available_transformations
print(f"{tr in a=}")
print(f"{T.valid(node)=}")

args = node.get_args(tr, -10, 10)
print(f"{args=}")

trs = [[0, 3, tr, -10, 10]]

# app.transform_list(trs)
# tapp = app.generate_code()
