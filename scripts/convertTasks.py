import re
import os
import argparse
import csv
from subprocess import check_output

#This script helps write BenchExec files for CPAchecker
#It expects the program files to be in the folder "./precision-reuse-files/programs/".
#It places the generated xml file inside the precision-reuse-files folder.
#It needs to be run at the parent directory of "precision-reuse-files" and requires the main directory of CPAchecker to be at "./svn-svn/reuse-precision-k-induction" from directory this script runs in.

def header(args, result):
    result.write("""<?xml version="1.0"?>

<!DOCTYPE benchmark PUBLIC "+//IDN sosy-lab.org//DTD BenchExec benchmark 1.0//EN" "http://www.sosy-lab.org/benchexec/benchmark-1.0.dtd">""")
    result.write('\n<benchmark tool="cpachecker" timelimit="'+environment[0]+'" hardtimelimit="'+environment[1]+'" memlimit="'+environment[2]+'" cpuCores="'+environment[3]+'">')
    result.write('\n\n\t<require cpuModel="Intel Xeon E3-1230 v5 @ 3.40 GHz" cpuCores="'+environment[3]+'"/>')

    result.write('\n\n\t<option name="-heap">'+environment[4]+'</option>')
    result.write("\t"+"""<option name="-disable-java-assertions"/>
  <!-- SV-Comp files assume that malloc always succeeds -->
  <option name="-setprop">cpa.predicate.memoryAllocationsAlwaysSucceed=true</option>
  <option name="-benchmark"/>""")
    result.write('\n\t<option name="-timelimit">'+environment[5]+'</option>')


def middle(args, result, diff_output):
    for root, dirs, files in os.walk(u"./precision-reuse-files/programs/"):
        #drivers--net--tokenring--abyss.ko/
        path = root.split(os.sep)

        if (args.regression):
            print(path)
            set_regression(result, args, files, path[3], root, diff_output)

        else:
            for file in files:

                if re.search("\.yml$", file):

                    result.write("\n\t<tasks>")
                    result.write("\n\t\t<include>./programs/"+path[3]+"/"+file+"</include>")

                    if(re.search("reuse$", args.analysis)):
                        set_reuse(result, args, file)

                    set_property(result, root, file)

                    result.write("\n\t</tasks>")

def set_regression(result, args, files, driver_name, root, diff_output):
    regression_number = int(args.regression)
    should_be_file_number = 0
    files.sort()

    for i in range (len(files)):



        current_file = files[i]

        #only look at .yml files
        if not re.search("\.yml$", current_file):
            continue

        split_file = current_file.split(".")

        file_number = int(split_file[2])

        #since should be gets set anew
        if should_be_file_number > file_number:
            continue

        if should_be_file_number < file_number:
            #set i (plus normal loop i++) to the next execution in the regression history
            #but since there can be more than one
            should_be_file_number = should_be_file_number + regression_number
            if regression_number > 1:
                continue


        decreased_commit_number = file_number-regression_number

        #to early of a commit to possibly have a regression commit
        if decreased_commit_number < 0:
            continue

        #just look in all files before the current file in the list, since the files list is sorted
        for j in range (i):
            #should just be a single file or no file, which matches the counted down .yml file
            if re.search(str(decreased_commit_number).zfill(3)+".*"+split_file[4]+"\.cil\.yml",files[j]):

                if diff_output:
                    diff_from = files[j].replace(".yml",".i")
                    diff_from = diff_from.partition(driver_name+".")[2]
                    diff_to = current_file.replace(".yml",".i")
                    diff_to = diff_to.partition(driver_name+".")[2]
                    diffresult = check_output(["bash", "-c", "diff --ignore-all-space <(grep -v '#line' '" + root + "/" + diff_from + "')  <(grep -v '#line' '" + root + "/" + diff_to + "') | diffstat -t | tail -n +2"]).decode("utf-8")
                    diff_sum = sum(int(i) for i in diffresult.split(",") if i.isnumeric())
                    diff_output.writerow([diff_to, diff_from, diff_sum])
                    break

                else:
                    result.write("\n\t<tasks>")
                    result.write("\n\t\t<include>./programs/"+driver_name+"/"+current_file+"</include>")

                    set_reuse(result, args, files[j])
                    set_property(result, root, current_file)

                    result.write("\n\t</tasks>")
                    break

def set_reuse(result, args, file):

    result.write("\n\t\t<requiredfiles>../svn-svn/reuse-precision-k-induction/test/results/"+args.folder+"/"+file+"/output/predicatePrec.txt</requiredfiles>")
    if(args.analysis == "kInduction_reuse"):
        result.write('\n\t\t<option name="-setprop">bmc.kinduction.predicatePrecisionFile=./predicatePrec.txt</option>')
    if(args.analysis == "predicate_reuse"):
        result.write('\n\t\t<option name="-setprop">cpa.predicate.abstraction.initialPredicates=./predicatePrec.txt</option>')
    if(args.analysis == "value_reuse"):
        result.write('\n\t\t<option name="-setprop">cpa.value.initialPredicatePrecisionFile=./predicatePrec.txt</option>')


def set_property(result, root, file):

    property = open(root+"/"+file).readlines()[6]

    if re.search("unreach-call-main0.prp", property):
    #if property == "  - property_file: ../../properties/unreach-call-main0.prp":
        result.write("\n\t\t<propertyfile>./properties/unreach-call-main0.prp</propertyfile>")

    else:
        result.write("\n\t\t<propertyfile>./properties/unreach-call-main1.prp</propertyfile>")

def end(args, result):
    result.write("\n\t<rundefinition>")
    if(args.analysis == "kInduction" or args.analysis == "kInduction_reuse"):
        result.write('\n\t\t<option name="-kInduction"/>')
        if(args.analysis == "kInduction_reuse"):
            if(args.localAsFunction):
                result.write('\n\t\t<option name="-setprop">bmc.kinduction.localAsFunction='+args.localAsFunction+'</option>')
            result.write('\n\t\t<option name="-setprop">bmc.kinduction.strategy='+args.strategy+'</option>')

    if(args.analysis == "predicate" or args.analysis == "predicate_export" or args.analysis == "predicate_reuse"):
        result.write('\n\t\t<option name="-predicateAnalysis"/>')
        if(args.analysis == "predicate_export"):
            result.write('\n\t\t<option name="-setprop">cpa.predicate.predmap.export=true</option>')
            result.write('\n\t\t<option name="-setprop">cpa.predicate.predmap.file=./predicatePrec.txt</option>')

    if(args.analysis == "value"):
        result.write('\n\t\t<option name="-valueAnalysis"/>')
    if(args.analysis == "value_reuse"):
        result.write('\n\t\t<option name="-valueAnalysis"/>')
        result.write('\n\t\t<option name="-setprop">cpa.value.reuse.precision.predicate.strategy=CONVERT_ONLY</option>')

    result.write('\n\t\t<option name="-setprop">cpa.predicate.allowedUnsupportedFunctions=memset,memmove</option>')
    result.write('\n\t\t<option name="-skipRecursion"/>')
    result.write("\n\t</rundefinition>")
    result.write('\n\t<resultfiles>**</resultfiles>')
    result.write("\n</benchmark>")

if __name__ == "__main__":
    argParser = argparse.ArgumentParser()
    argParser.add_argument("-f", "--folder", help="folder in which the predicate precisions are")
    argParser.add_argument("-o", "--output", help="output file name")
    argParser.add_argument("-e", "--environment", help="define environment (known parameters: small, benchmark)")
    argParser.add_argument("-a", "--analysis", help="analysis to use (known parameters: predicate, predicate_export, predicate_reuse, kInduction, kInduction_reuse, value, value_reuse)")
    argParser.add_argument("-r", "--regression", help="use regression verification with every xth regression (known parameters: positive integers)")
    argParser.add_argument("-s", "--strategy", help="k-induction reuse strategy (known parameters see: CPAChecker/configurationOptions.txt bmc.kinduction.strategy)")
    argParser.add_argument("-l", "--localAsFunction", help="regard all local precisions as precisions of their respective function (known parameters: true, false)")
    argParser.add_argument("-d", "--writeDiffs", help="store line differences between regression versions (parameter: file name csv)")

    args = argParser.parse_args()

    if args.environment == "small":
        environment = ["7 min", "8 min", "7 GB", "2", "4000M", "420s"]
    else:
        environment = ["15 min", "15 min", "15 GB", "2", "8000M", "900s"]

    if args.writeDiffs:
        diff_output = csv.writer(open(args.writeDiffs, 'w', newline=''), delimiter=',',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)
        diff_output.writerow(['New Version', 'Old Version', 'Diff Lines'])
    else:
        diff_output = None

    result = open("precision-reuse-files/"+args.output, "w")
    if !diff_output:
        header(args, result)
    middle(args, result, diff_output)
    if !diff_output:
        end(args, result)
