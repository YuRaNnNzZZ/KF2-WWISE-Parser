# Killing Floor 2 WWISE bank dump parser.
# Copies .wem files into their valid locations.
# Supports automatic unpacking with bnkextr and .wem conversion with WW2OGG and revorb when placed alongside the script.

import sys, os.path
from shutil import copyfile
import subprocess

scriptDir = ""
hasBnkextr = False
hasWW2OGG = False
hasRevorb = False

def tryCopyFiles(defTextFile, baseOutDir):
    print("Input file:", defTextFile)
    print("Output dir:", baseOutDir)

    inputDir = os.path.dirname(defTextFile)

    with open(defTextFile, "r") as WWISEDefFile:
        if WWISEDefFile.read()[:5] != "Event":
            exit("The file is not a valid WWISE bank dump file.")

        WWISEDefFile.seek(0)

        wemFilesDir = os.path.join(inputDir, os.path.basename(defTextFile).replace(".txt", ""))

        if not os.path.exists(wemFilesDir) and hasBnkextr:
            os.makedirs(wemFilesDir)

            subprocess.run([os.path.join(scriptDir, "bnkextr.exe"), wemFilesDir + ".bnk"])

        isReadingEvents = False

        for line in WWISEDefFile:
            if not isReadingEvents:
                if line.startswith("In Memory Audio"):
                    isReadingEvents = True

                continue

            if not line.startswith("\t"):
                break

            lineData = line.split("\t")

            if len(lineData) < 8:
                continue

            # Convert backslashes to proper file separators and strip slashes from start/end
            lineData[5] = lineData[5].replace("\\", os.path.sep).strip(os.path.sep)

            inputFile = os.path.join(wemFilesDir, lineData[1] + ".wem")
            outputFile = os.path.join(baseOutDir, lineData[5] + ".wem")
            print("Copying file", lineData[2])

            # Search in root first
            if not os.path.exists(inputFile) and os.path.exists(inputDir + os.path.sep + lineData[1] + ".wem"):
                inputFile = inputDir + os.path.sep + lineData[1] + ".wem"

            if not os.path.exists(inputFile):
                print("Input file missing, skipping...")
                continue

            outDir = os.path.dirname(outputFile)

            if not os.path.exists(outDir):
                os.makedirs(outDir)

            copyfile(inputFile, outputFile)

            if hasWW2OGG and os.path.exists(outputFile):
                subprocess.run(
                    [os.path.join(scriptDir, "ww2ogg.exe"), outputFile, "--pcb", os.path.join(scriptDir, "packed_codebooks_aoTuV_603.bin")])

                outputFileOGG = outputFile.replace(".wem", ".ogg")

                if os.path.exists(outputFileOGG):
                    os.remove(outputFile) # we don't need the wem anymore

                    if hasRevorb:
                        subprocess.run([os.path.join(scriptDir, "revorb.exe"), outputFile.replace(".wem", ".ogg")])

if __name__ == "__main__":
    args = sys.argv

    scriptDir = sys.path[0]

    # Check for bnkextr
    if os.path.exists(os.path.join(scriptDir, "bnkextr.exe")):
        hasBnkextr = True

    # Check for WW2OGG
    if os.path.exists(os.path.join(scriptDir, "ww2ogg.exe")) and os.path.join(scriptDir, "packed_codebooks_aoTuV_603.bin"):
        hasWW2OGG = True

    # Check for Revorb
    if os.path.exists(os.path.join(scriptDir, "revorb.exe")):
        hasRevorb = True

    inputFile = ""

    if len(args)>=2:
        inputFile = args[1]
    else:
        exit("You have to supply the file to parse.")

    if not os.path.isfile(inputFile):
        exit("THATS NO FILE")

    if not inputFile.endswith(".txt"):
        exit("Only text files are supported.")

    directory = os.path.dirname(os.path.abspath(inputFile))

    tryCopyFiles(os.path.abspath(inputFile), directory)
