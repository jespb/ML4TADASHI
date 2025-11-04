
pb = [
    "jacobi-1d",
    "bicg",
    "atax",
    "gesummv",
    "trisolv",
    "durbin",
    "mvt",
    "gemver",
    "deriche",
    "doitgen",
    "gemm",
    "syrk",
    "2mm",
    "trmm",
    "symm",
    "jacobi-2d",
    "fdtd-2d",
    "cholesky",
    "syr2k",
    "3mm",
    "correlation",
    "covariance",
    "heat-3d",
    "gramschmidt",
    "ludcmp",
    "lu",
    "nussinov",
    "adi",
    "floyd-warshall",
    "seidel-2d",
]

methods = ["Heuristic", "BeamSearch", "EvoTD", "EvoTD_H"]

results = {}


for p in pb:
    for m in methods:
        results["%s_%s" % (p, m)] = 1

for p in pb:
    try:
        f1 = open("BeamS_%s.txt"%p).readlines()
        spd1 = 1
        for line in f1:
            if "Speed up" in line:
                spd1 = float(line.split("Speed up: ")[1].split(", ")[0])
                results["%s_%s" % (p, methods[1])] = spd1

        f2 = open("Evo_B_%s.txt"%p).readlines()
        spd2 = 1
        for line in f2:
            if "Fitness on generation" in line:
                spd2 = float(line.split(" (")[1].split("x ")[0])
                results["%s_%s" % (p, methods[3])] = spd2


        f3 = open("Evo_H_%s.txt"%p).readlines()
        spd3 = 1
        for line in f3:
            if "Fitness on generation" in line:
                spd3 = float(line.split(" (")[1].split("x ")[0])
                results["%s_%s" % (p, methods[2])] = spd3
    except:
        print("ERROR on file %s" % p)



for p in pb:
    print("\n\nBENCHMARK: %s" % p)
    best_spd = max([ results["%s_%s"%(p, m)] for m in methods])
    for m in methods:
        spd = results["%s_%s"%(p, m)]
        print("  %15s: %.3f %s" % (m, spd, "*" if spd > best_spd*0.99 else ""))

print("G-MEANs:")
for m in methods:
    gm = 1
    for p in pb:
        gm *= results["%s_%s"%(p, m)]
    gm = gm**(1.0/len(pb))
    print("  %15s: %.3f" % (m, gm))
        
