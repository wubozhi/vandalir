import argparse
import sys
import os
import subprocess


def parseArgs(parser):
    parser.add_argument('file', action='store', help='file that should be analyzed')
    parser.add_argument('-c', action='store_true', dest='compile', default=False, help='use compilation in Soufflé')
    parser.add_argument('-pc', action='store_true', dest='previous_compile', default=False, help='use previous compiled version')
    parser.add_argument('-p', action='store_true', dest='profile', default=False, help='use the Soufflé profiler')
    parser.add_argument('-f', action='store', dest='facts_dir', default="facts",
                        help='specify facts directory (default: facts)')
    parser.add_argument('-o', action='store', dest='output_dir', default="output",
                        help='specify output directory (default: output)')
    parser.add_argument('-j', action='store', dest='thread_count', default="4",
                        help='specify how many threads Soufflé may use (default: 4)')


def parse(filepath, facts_dir):

    if(not os.path.isdir(facts_dir)):
        os.mkdir(facts_dir)

    folder, filename = os.path.split(filepath)
    filename = filename[:-2]

    if(filepath.endswith(".c")):
        command = "clang -S -emit-llvm \""+filepath+"\" -o \"./llvm-ir/"+filename+".ll\""
        os.system(command)
        command2 = "python3 Parser.py ./llvm-ir/"+filename+".ll "
        if(facts_dir):
            command2 += "-o "+facts_dir
        subprocess.call(command2, shell=True)
    elif(filepath.endswith(".ll") or filepath.endswith(".bc")):
        command = "python3 Parser.py "+filepath+" "
        if(facts_dir):
            command += "-o "+facts_dir
        subprocess.call(command, shell=True)
    else:
        print("Unsupported file type. File extension needs to be .c, .bc or .ll")

def compile_datalog():
    print("Compiling Datalog...")
    command = "souffle \"logic/main.dl\" -o bin/analyzer -L logic/functors "
    subprocess.call(command, shell=True, cwd="./")
    print("Datalog compiled.")


def run(filepath, compile, previous_compile, profile, facts_dir, output_dir, thread_count):

    if(not os.path.isdir(output_dir)):
            os.mkdir(output_dir)

    if(compile):
        compile_datalog()
    
    if((previous_compile or compile) and not profile):
        #execute previously compiled

        command = "bin/analyzer "+filepath+" "
        command += "-F "+facts_dir+" "
        command += "-D "+output_dir+" "
        command += "-j "+thread_count+" "

        subprocess.call(command, shell=True)

    else:
        compile_functors()

        command = "souffle \"logic/main.dl\" "
        command += "-F \""+facts_dir+"\" -D \""+output_dir+"\" "
        command += "-L logic/functors "
        if(compile or previous_compile):
            command += "--compile "
        if(profile):
            command += "-p ./profile "
        command += "-j "+thread_count

        subprocess.call(command, shell=True)

    if(profile):
        command = "souffle-profile \"./profile\" -j"
        subprocess.call(command, shell=True)

    if(compile):
        subprocess.call("rm ./*.cpp", shell=True)

    print("Execution finished output written to output directory")


def compile_functors():
    command = "./make.sh "
    subprocess.call(command, shell=True, cwd="logic/functors/")
    # print("Functors compiled.")


def main():
    filepath = args.file
    compile = args.compile
    previous_compile = args.previous_compile
    profile = args.profile

    facts_dir = args.facts_dir
    output_dir = args.output_dir
    thread_count = args.thread_count
    if(not thread_count):
        thread_count = 4

    parse(filepath, facts_dir)
    run(filepath, compile, previous_compile, profile, facts_dir, output_dir, thread_count)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run Datalog analysis on supplied file')
    parseArgs(parser)
    args = parser.parse_args(sys.argv[1:])
    main()
