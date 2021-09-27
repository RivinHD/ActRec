import argparse
import os
import json

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-files", type= list)
    args = parser.parse_args()

    addon_directory = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    version = (0, 0, 0)
    with open(os.path.join(addon_directory, "__init__.py"), 'r', encoding= 'utf-8') as file:
        for line in file.readlines():
            if "version" in line:
                version = eval("%s)" %line.split(":")[1].split(")")[0].strip())
                break
    with open(os.path.join(addon_directory, "actrec/config.py")) as file:
        for line in file.readlines():
            if "version" in line:
                check_version = line.split("=")[1].strip()
                if check_version > version:
                    version = check_version
                break

    print("Update to Version %s\nFiles:%s" %(version, args.files))

    version = list(version)
    with open(os.path.join(addon_directory, "download_file.json"), 'w+', encoding= 'utf-8') as file:
        data = json.loads(file.read())
        for file in args.files:
            if data.get(file, None):
                data[file] = version
        json.dump(data, file, ensure_ascii= False, indent= 4)
    
    with open(os.path.join(addon_directory, "__init__.py"), 'r+', encoding= 'utf-8') as file:
        lines = []
        for line in file.readlines():
            if "version" in line:
                split = line.split(": ")
                sub_split = split[1].split(")")
                line = "%s: %s%s" %(split[0], tuple(version), sub_split[-1])
            lines.append(line)
                
        

    

    
    

