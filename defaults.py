from typing import List, Tuple

class LoadMode:
    biof = 'bioformats';
    skimage = 'skimage';
    imageio = 'imageio';

class Defaults:
    bioLogging:bool = False;
    loadMode:str = LoadMode.imageio; #TODO: image load error when switching between formats on first load, not reproducible
    blankSize:Tuple[int,int] = (300,300);
    blankColor:str = "#00000000";
    defaultFG:str = "#20FFFFFF";
    defaultBG:str = "#B0460000";
    defaultBrushSize:int = 10;
    maxBrushSliderSize:int = 80;
    maxBrushInputSize:int = 999;
    filePathMaxLength:int = 200; #characters
    drawButtonNames:Tuple[str,str] = ("Include", "Exclude");
    drawButtonsLabel:str = "Draw Mode";
    workingDirectory:str = "working_masks/";
    sessionFileName:str = "session_dat.json";
    supportedImageExts:List[str] = [".bmp",".png",".jpg",".pbm",".jpeg",".tif",".sld",".aim",".al3d",".gel",".am",".amiramesh",".grey",".hx",".labels",".cif",".img",".hdr",".sif",".afi",".svs",".htd",".pnl",".avi",".arf",".exp",".sdt",".1sc",".pic",".raw",".xml",".scn",".ims",".cr2",".crw",".ch5",".c01",".dib",".dv",".r3d",".dcm",".dicom",".v",".eps",".epsi",".ps",".flex",".mea",".res",".tiff",".fits",".dm3",".dm4",".dm2",".gif",".naf",".his",".vms",".i2i",".ics",".ids",".seq",".ipw",".hed",".mod",".leff",".obf",".msr",".xdce",".frm",".inr",".ipl",".ipm",".dat",".par",".jp2",".jpk",".jpx",".xv",".bip",".fli",".lei",".lif",".scn",".sxm",".l2d",".lim",".stk"]; 
    supportedMaskExts:List[str] = supportedImageExts; #TODO: filter list by image formats and not just supported formats
    autosaveTime:int = 60*1000; #milliseconds
    exportedFlagFile:str = "export.flag";
    attemptMaskResize:bool = False;
    penPreview:bool = True;
    exactPreviewWidth:float = 0.6;
    circlePreviewWidth:float = exactPreviewWidth*5;
    allowMaskCreation:bool = True;
    defaultMaskFormat:str = ".bmp";
    adjustSigFigs:int = 4;
    histSliderPrecision:int = 100000
    convertUnassignedMasks:bool = True; #whether to convert masks with no equivalent in the mask source directory to some standard type, and prompt the user of that type
    createEmptyMasksForExport:bool = False;
    adjustForcePreview:bool = False;