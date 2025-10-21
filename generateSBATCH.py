
pb = ['jacobi-1d', 'bicg', 'atax', 'gesummv', 'trisolv', 'durbin', 'mvt', 'gemver', 'deriche', 'doitgen', 'gemm', 'syrk', '2mm', 'trmm', 'symm', 'jacobi-2d', 'fdtd-2d', 'cholesky', 'syr2k', '3mm', 'correlation', 'covariance', 'heat-3d', 'gramschmidt', 'ludcmp', 'lu', 'nussinov', 'adi', 'floyd-warshall', 'seidel-2d']
    

for i in range(len(pb)):
    if i == 0:
        print("jid%d=$(sbatch -o results_evost/%s.txt genoa_EvoTADASHI_Heuristic.sh --benchmark %s | awk '{print $4}')" % (i, pb[i], pb[i]) )
    else:
        print("jid%d=$(sbatch -o results_evost/%s.txt --dependency=afterany:$jid%d genoa_EvoTADASHI_Heuristic.sh --benchmark %s | awk '{print $4}')" % (i, pb[i], i-1, pb[i]) )
