# SegmenterGui
A simple GUI for making and editing masks using Python, specifically made for editing of AI-generated cell movie masks (but useful for creating / touching up binary masks in general).

# Install
1. Install python https://www.python.org/downloads/
2. Clone the repository to your machine
3. Open a terminal in the local folder and run ```pip install -r requirements.txt```

# Usage
Run `maskeditor.py` to open the application. 

## Image/Mask Selection
On the left is the image and mask selection pane: Selecting an image directory will list the images in the folder in the scroll menu. Left/Right arrow key to switch image, previous/next buttons, or just select an image from the list. Selecting a mask folder will tell the program to try to load masks from that directory: for every image in the image directory, it will try to load a mask with the same name from the mask folder. If no mask exists, a blank one will be editable.

## Working masks / Exporting
Changes you make do not overwrite the original masks; the unexported version of every mask exists in its own folder in the segmenter's install location, working_masks. Exporting will copy every mask from the source and working masks folder into the target directory. To overwrite the source folder, simply export into it. Newly created masks (if no source is selected or no mask is available) will also be exported from working_masks, and will be saved in the format specfied by the default mask extension dropdown. Note that only masks that have corresponding images will be exported from the source and working mask folders.s

## Session / Saving
The current mask is saved whenever you make a brushstroke, and the program's session state is saved whenever you make a change (and every 15 seconds). This means closing the window / crashing (please report any bugs!) will never* lose your work. If you have unexported masks, the program will prompt you to export, but if you choose not to your current working masks will always be saved.

If for whatever reason, something does go wrong, your masks will still be stored in the working masks folder (as .bmp files, you may have to use an image converter script). If the program breaks on opening because of session data corruption, deleting session_dat.json will reset the session. 

*hopefully

## More
See the Help tab in the program itself for more information. 

# FAQ
"Images not Loading / Showing as black"
First, check the brightness adjustment settings. If the adjustment range is outside of the brightness range of the image, it will appear as black. Reset to Default should ensure that all values in the image are within the range, though more tuning may be needed to ensure visibility and picture quality.
