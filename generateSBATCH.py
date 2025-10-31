
pb = ['jacobi-1d', 'bicg', 'atax', 'gesummv', 'trisolv', 'durbin', 'mvt', 'gemver', 'deriche', 'doitgen', 'gemm', 'syrk', '2mm', 'trmm', 'symm', 'jacobi-2d', 'fdtd-2d', 'cholesky', 'syr2k', '3mm', 'correlation', 'covariance', 'heat-3d', 'gramschmidt', 'ludcmp', 'lu', 'nussinov', 'adi', 'floyd-warshall', 'seidel-2d']
    

for i in range(len(pb)):
    if i == 0:
        print("jid%d=$(sbatch -o results_evost/%s.txt --job-name=%s genoa_EvoTADASHI_Heuristic.sh --benchmark %s | awk '{print $4}')" % (i, pb[i], pb[i], pb[i]) )
    else:
        print("jid%d=$(sbatch -o results_evost/%s.txt --job-name=%s --dependency=afterany:$jid%d genoa_EvoTADASHI_Heuristic.sh --benchmark %s | awk '{print $4}')" % (i, pb[i], pb[i], i-1, pb[i]) )


print("\n\n\n")

for i in range(len(pb)):
    #t = (pb[i], pb[i], pb[i])
    if i == 0:
        print("jid%d=$(sbatch -o results_evost_XL/Evo_B_%s.txt --job-name=%s genoa_ML4T.sh --benchmark %s --dataset EXTRALARGE --method EvoTADASHI --use-heuristic| awk '{print $4}')" % (i*3,pb[i], pb[i], pb[i]))
        print("jid%d=$(sbatch -o results_evost_XL/Evo_H_%s.txt --job-name=%s genoa_ML4T.sh --benchmark %s --dataset EXTRALARGE --method EvoTADASHI| awk '{print $4}')" % (i*3+1,pb[i], pb[i], pb[i]))
        print("jid%d=$(sbatch -o results_evost_XL/BeamS_%s.txt --job-name=%s genoa_ML4T.sh --benchmark %s --dataset EXTRALARGE --method BeamSearch| awk '{print $4}')" % (i*3+2,pb[i], pb[i], pb[i]))
    else:
        print("jid%d=$(sbatch -o results_evost_XL/Evo_B_%s.txt --job-name=%s --dependency=afterany:$jid%d genoa_ML4T.sh --benchmark %s --dataset EXTRALARGE --method EvoTADASHI --use-heuristic| awk '{print $4}')" % (i*3  ,pb[i], pb[i],i*3-3, pb[i]))
        print("jid%d=$(sbatch -o results_evost_XL/Evo_H_%s.txt --job-name=%s --dependency=afterany:$jid%d genoa_ML4T.sh --benchmark %s --dataset EXTRALARGE --method EvoTADASHI| awk '{print $4}')"                 % (i*3+1,pb[i], pb[i],i*3-2, pb[i]))
        print("jid%d=$(sbatch -o results_evost_XL/BeamS_%s.txt --job-name=%s --dependency=afterany:$jid%d genoa_ML4T.sh --benchmark %s --dataset EXTRALARGE --method BeamSearch| awk '{print $4}')"                 % (i*3+2,pb[i], pb[i],i*3-1, pb[i]))
