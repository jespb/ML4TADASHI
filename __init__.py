from util import get_args


def run(cls, kwargs):
    args = get_args()
    args.cls = cls
    args.kwargs = kwargs
    if args.method == "EvoTADASHI":
        from EvoTADASHI import EvoTADASHI
    elif args.method == "FugakuEvoTADASHI":
        from EvoTADASHI_fugaku import EvoTADASHI
    elif args.method == "BeamSearch":
        from BeamSearch import BeamSearch
    elif args.method == "Heuristic":
        from Heuristic import Heuristic
    else:
        print("Method not implemented %s" % args.method)
        assert False

    if args.method in ["EvoTADASHI", "FugakuEvoTADASHI"]:
        method = EvoTADASHI(args)
    elif args.method == "BeamSearch":
        method = BeamSearch(args)
    elif args.method == "Heuristic":
        method = Heuristic(args)
    print(str(args) + "\n")
    method.fit()
