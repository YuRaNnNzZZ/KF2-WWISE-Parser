# Killing Floor 2 WWISE bank dump parser.
# Copies .wem files into their valid locations.
# Supports automatic unpacking with bnkextr and .wem conversion with WW2OGG and revorb when placed alongside the script.

import json, sys, os.path
from shutil import copyfile
import subprocess

scriptDir = ""
hasBnkextr = False
hasWW2OGG = False
hasRevorb = False
hasvgmstream = False

wwiseLangs = [
    'Chinese(PRC)',
    'Chinese(Taiwan)',
    'English(US)',
    'French(France)',
    'German',
    'Italian',
    'Japanese',
    'Korean',
    'Polish',
    'Portuguese(Brazil)',
    'Portuguese(Portugal)',
    'Russian',
    'Spanish(Mexico)',
    'Spanish(Spain)',
]

def processFileDict(fileDict, wemFilesDir, inputDir, baseOutDir):
    processedFiles = []

    # Copy and process the files
    for fileID in fileDict:
        # Convert backslashes to proper file separators and strip slashes from start/end
        outFilePath = fileDict[fileID].replace("\\", os.path.sep).strip(os.path.sep)
        if not outFilePath.lower().endswith(".wem"):
            outFilePath = outFilePath + ".wem"

        inputFile = os.path.join(wemFilesDir, fileID)
        outputFile = os.path.join(baseOutDir, outFilePath)

        # Search in root first
        if os.path.exists(inputDir + os.path.sep + fileID):
            inputFile = inputDir + os.path.sep + fileID

        if not os.path.exists(inputFile):
            print("Input file %s missing, skipping..." % fileID)
            continue

        if os.path.exists(outputFile.replace(".wem", ".ogg")) or os.path.exists(outputFile.replace(".wem", ".wav")):
            continue # do not copy and don't process file if wav or ogg already exists

        print("Copying file", outFilePath)
        outDir = os.path.dirname(outputFile)

        if not os.path.exists(outDir):
            os.makedirs(outDir)

        copyfile(inputFile, outputFile)

        processedFiles.append(outputFile)

    if hasWW2OGG:
        for filePath in processedFiles:
            subprocess.run([os.path.join(scriptDir, "ww2ogg.exe"), filePath, "--pcb", os.path.join(scriptDir, "packed_codebooks_aoTuV_603.bin")])

            outputFileOGG = filePath.replace(".wem", ".ogg")

            if os.path.exists(outputFileOGG) and os.path.exists(filePath):
                os.remove(filePath) # we don't need the wem anymore

                if hasRevorb:
                    subprocess.run([os.path.join(scriptDir, "revorb.exe"), outputFileOGG])
            elif hasvgmstream:
                outputFileWAV = filePath.replace(".wem", ".wav")

                subprocess.run([os.path.join(scriptDir, "vgmstream-win64", "vgmstream-cli.exe"), "-o", outputFileWAV, filePath])

                if os.path.exists(outputFileWAV):
                    os.remove(filePath) # we don't need the wem anymore
    elif hasvgmstream:
        for filePath in processedFiles:
            outputFileWAV = filePath.replace(".wem", ".wav")

            subprocess.run([os.path.join(scriptDir, "vgmstream-win64", "vgmstream-cli.exe"), "-o", outputFileWAV, filePath])

            if os.path.exists(outputFileWAV):
                os.remove(filePath) # we don't need the wem anymore

def tryCopyJSON(defTextFile, baseOutDir):
    print("Input file:", defTextFile)
    print("Output dir:", baseOutDir)

    inputDir = os.path.dirname(defTextFile)

    wemFilesDir = os.path.join(inputDir, os.path.basename(defTextFile).replace(".json", ""))

    if not os.path.exists(wemFilesDir) and os.path.exists(wemFilesDir + ".bnk") and hasBnkextr:
        os.makedirs(wemFilesDir)

        subprocess.run([os.path.join(scriptDir, "bnkextr.exe"), wemFilesDir + ".bnk"])

    fileDict = {}

    with open(defTextFile, "r") as WWISEDefFile:
        data = json.loads(WWISEDefFile.read())
        
        if data.get("SoundBanksInfo"):
            info = data["SoundBanksInfo"]

            if info.get("StreamedFiles"):
                for f in info["StreamedFiles"]:
                    fileDict[f["Id"] + ".wem"] = f["Path"]

            if info.get("SoundBanks"):
                for bank in info["SoundBanks"]:
                    if bank.get("IncludedEvents"):
                        for event in bank["IncludedEvents"]:
                            if event.get("IncludedMemoryFiles"):
                                for f in event["IncludedMemoryFiles"]:
                                    fileDict[f["Id"] + ".wem"] = f["Path"]
                            if event.get("ReferencedStreamedFiles"):
                                for f in event["ReferencedStreamedFiles"]:
                                    fileDict[f["Id"] + ".wem"] = f["Path"]

    processFileDict(fileDict, wemFilesDir, inputDir, baseOutDir)

def tryCopyFiles(defTextFile, baseOutDir):
    print("Input file:", defTextFile)
    print("Output dir:", baseOutDir)

    inputDir = os.path.dirname(defTextFile)

    wemFilesDir = os.path.join(inputDir, os.path.basename(defTextFile).replace(".txt", ""))

    checkParent = False
    for lang in wwiseLangs:
        if wemFilesDir.lower().find(lang.lower()):
            checkParent = True
            break

    if not os.path.exists(wemFilesDir) and os.path.exists(wemFilesDir + ".bnk") and hasBnkextr:
        os.makedirs(wemFilesDir)

        subprocess.run([os.path.join(scriptDir, "bnkextr.exe"), wemFilesDir + ".bnk"])

    fileDict = {}

    with open(defTextFile, "r") as WWISEDefFile:
        if WWISEDefFile.read()[:5] != "Event":
            exit("The file is not a valid WWISE bank dump file.")

        WWISEDefFile.seek(0)
        isReadingEvents = False
        # In Memory Audio
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

            if checkParent:
                fileDict[os.path.join(os.path.dirname(lineData[1]), "..", os.path.basename(lineData[1])) + ".wem"] = lineData[5]

            fileDict[lineData[1] + ".wem"] = lineData[5]

        WWISEDefFile.seek(0)
        isReadingEvents = False
        # Streamed Audio (loose files?)
        for line in WWISEDefFile:
            if not isReadingEvents:
                if line.startswith("Streamed Audio"):
                    isReadingEvents = True

                continue

            if not line.startswith("\t"):
                break

            lineData = line.split("\t")

            if len(lineData) < 7:
                continue

            if checkParent:
                fileDict[os.path.join(os.path.dirname(lineData[4]), "..", os.path.basename(lineData[4]))] = lineData[5]

            fileDict[lineData[4]] = lineData[5]

    processFileDict(fileDict, wemFilesDir, inputDir, baseOutDir)

if __name__ == "__main__":
    args = sys.argv

    scriptDir = sys.path[0]

    # Check for bnkextr
    if os.path.exists(os.path.join(scriptDir, "bnkextr.exe")):
        hasBnkextr = True

    # Check for WW2OGG
    if os.path.exists(os.path.join(scriptDir, "ww2ogg.exe")) and os.path.exists(os.path.join(scriptDir, "packed_codebooks_aoTuV_603.bin")):
        hasWW2OGG = True

    # Check for Revorb
    if os.path.exists(os.path.join(scriptDir, "revorb.exe")):
        hasRevorb = True

    # Check for vgmstream
    if os.path.exists(os.path.join(scriptDir, "vgmstream-win64", "vgmstream-cli.exe")):
        hasvgmstream = True

    if len(args) < 2:
        exit("You must provide at least one input file.")

    for arg in args[1:]:
        baseOutDir = os.path.dirname(os.path.abspath(arg))

        if arg.lower().endswith(".txt"):
            tryCopyFiles(os.path.abspath(arg), baseOutDir)
            continue

        if arg.lower().endswith(".json"):
            tryCopyJSON(os.path.abspath(arg), baseOutDir)
            continue

        if arg.lower().endswith(".bnk") and hasBnkextr:
            subprocess.run([os.path.join(scriptDir, "bnkextr.exe"), os.path.abspath(arg)])
            continue

        print("Skipping unknown file " + arg)

