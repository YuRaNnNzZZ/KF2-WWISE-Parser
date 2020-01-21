# Killing Floor 2 WWISE Bank Dump Parser

Allows to organize extracted .wem files when .txt file with paths is available.

## Requirements
* Python 3.5+

## Usage
1. Download the script
2. (Optional) Place the tools listed below to the folder with the script
3. Navigate to `SteamApps/common/killingfloor2/KFGame/BrewedPC/WwiseAudio/Windows` folder
4. Drag and drop the .txt dump file (same name as the .bnk file) to the script (or run it with the file path as first argument if drag-and-drop is not available for you)
5. Output folder hierarchy will be created in the root directory of input file (so make sure the total path doesn't exceed the 255 characters limit!)

## Automation support
* If `bnkextr.exe` is present in the folder with this script, the bank will be extracted before processing. Otherwise, extracted .wem files are required.
* If `ww2ogg.exe` and `packed_codebooks_aoTuV_603.bin` are available in the same folder, copied .wem files would be converted to .ogg and removed.
* Additionally, if `revorb.exe` is present, resulting .ogg files will be processed (requires ww2ogg).