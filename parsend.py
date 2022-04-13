from msilib.schema import Error
import re
series_regex = "s([0-9]+)"
time_regex = "t([0-9]+)"

##Parses .nd files from metamorph on the optotaxis microscope

def parseND(filePath):
    with open(filePath,'r') as f:
        lines = f.readlines();
    args = {};
    for line in lines:
        largs = line.split(", "); #line args lol
        if len(largs) == 0:
            assert largs[0] == "\"EndFile\"";
            break;
        args[largs[0].replace("\"","")] = largs[1].replace("\"","");
    return args;

def sorted_dir(paths:list[str]):
    def get_key(s:str):
        out = [];
        series = re.findall(series_regex,s);
        if series: 
            out.append(int(series[0]));
        else:
            print(s);
        time = re.findall(time_regex,s);
        if time:
            out.append(int(time[0]));
        else:
            print(s);
        return out;
    try:
        paths.sort(key=get_key);
    except Exception as e:
        print(e);
        print("hello my darling")
    return paths;

# def getNDFileInfo(path):
#     args = parseND(path);
    
#     for arg,val in args.items():

print(sorted_dir([f's{i}_t{j}.TIF' for i in range(5) for j in range(30)]))