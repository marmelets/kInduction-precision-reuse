# kInduction-predicate-reuse
This repository includes supplementary files for the bachelor thesis: Re-Use of Predicate Precision in K-Induction.

## How to use

If you want to have a look at the raw data, you can find it in ./runs or the csv files in ./csvFiles
If you want to re-create the data:
1. download the program files from https://www.sosy-lab.org/research/cpa-reuse/regression-benchmarks/
2. Rename the files by running the script scripts/renamePrograms.sh inside the folder "programs" from the downloaded artifact in order to have no problems with logging of BenchExec
3. Then you can use the readily available task sets in xmlFiles/ if your directory structure complies to the one mentioned at the top of convertTasks.py. Otherwise, use convertTasks.py to generate your own task sets.
4. run the task sets with BenchExec.
5. Generate the csv files by using TableGenerator with -x xmlFiles/tableGenOptions.xml
6. use boxplot_gen.ipynb to generate the boxplots