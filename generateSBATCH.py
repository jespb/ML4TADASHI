
pb = ['jacobi-1d', 'bicg', 'atax', 'gesummv', 'trisolv', 'durbin', 'mvt', 'gemver', 'deriche', 'doitgen', 'gemm', 'syrk', '2mm', 'trmm', 'symm', 'jacobi-2d', 'fdtd-2d', 'cholesky', 'syr2k', '3mm', 'correlation', 'covariance', 'heat-3d', 'gramschmidt', 'ludcmp', 'lu', 'nussinov', 'adi', 'floyd-warshall', 'seidel-2d']
    

for i in range(len(pb)):
    if i == 0:
        print("jid%d=$(sbatch -o results_evost/%s.txt --job-name=%s genoa_EvoTADASHI_Heuristic.sh --benchmark %s | awk '{print $4}')" % (i, pb[i], pb[i], pb[i]) )
    else:
        print("jid%d=$(sbatch -o results_evost/%s.txt --job-name=%s --dependency=afterany:$jid%d genoa_EvoTADASHI_Heuristic.sh --benchmark %s | awk '{print $4}')" % (i, pb[i], pb[i], i-1, pb[i]) )


print("\n\n\n")

last_jid1=0
last_jid2=0
last_jid3=0
for run in range(4, 31):
    for i in range(len(pb)):
        jid1 = run*1000+i*3
        jid2 = run*1000+i*3+1
        jid3 = run*1000+i*3+2
        if run==4 and i==0:
            print("jid%d=$(sbatch -o results_evost_XL_run%d/Evo_B_%s.txt --job-name=%s genoa_ML4T.sh --benchmark %s --dataset EXTRALARGE --method EvoTADASHI --use-heuristic| awk '{print $4}')"  % (jid1, run, pb[i], pb[i], pb[i]))
            print("jid%d=$(sbatch -o results_evost_XL_run%d/Evo_H_%s.txt --job-name=%s genoa_ML4T.sh --benchmark %s --dataset EXTRALARGE --method EvoTADASHI| awk '{print $4}')"                  % (jid2, run, pb[i], pb[i], pb[i]))
            print("jid%d=$(sbatch -o results_evost_XL_run%d/BeamS_%s.txt --job-name=%s genoa_ML4T.sh --benchmark %s --dataset EXTRALARGE --method BeamSearch| awk '{print $4}')"                  % (jid3, run, pb[i], pb[i], pb[i]))
        else:
            print("jid%d=$(sbatch -o results_evost_XL_run%d/Evo_B_%s.txt --job-name=%s --dependency=afterany:$jid%d genoa_ML4T.sh --benchmark %s --dataset EXTRALARGE --method EvoTADASHI --use-heuristic| awk '{print $4}')" % (jid1, run, pb[i], pb[i],last_jid1, pb[i]))
            print("jid%d=$(sbatch -o results_evost_XL_run%d/Evo_H_%s.txt --job-name=%s --dependency=afterany:$jid%d genoa_ML4T.sh --benchmark %s --dataset EXTRALARGE --method EvoTADASHI| awk '{print $4}')"                 % (jid2, run, pb[i], pb[i],last_jid2, pb[i]))
            print("jid%d=$(sbatch -o results_evost_XL_run%d/BeamS_%s.txt --job-name=%s --dependency=afterany:$jid%d genoa_ML4T.sh --benchmark %s --dataset EXTRALARGE --method BeamSearch| awk '{print $4}')"                 % (jid3, run, pb[i], pb[i],last_jid3, pb[i]))
        last_jid1=jid1
        last_jid2=jid2
        last_jid3=jid3