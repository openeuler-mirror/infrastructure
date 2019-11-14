# Usage: move this file into the destination folder you used for downloading.
import os.path

RPMFILE = "package_lists"
ARCHITECTURE = "x86_64" #change this into 'x86_64' or 'aarch64' if required.
try:
    results = []
    # Read to plain object
    with open(RPMFILE) as rpmlist:
        content = rpmlist.readline()
        count = 1
        while content:
            if content.endswith(".rpm\n"):
                package_name = content.split(" ")[-1].rstrip("\n")
                if not os.path.exists(package_name):
                    full_url = "https://dl.fedoraproject.org/pub/" \
                               "fedora/linux/releases/29/Everything/"\
                               +ARCHITECTURE+"/os/Packages/"+package_name[0]+"/"+package_name
                    results.append("curl -o {0} {1}".format(package_name, full_url))
                    count = count+1
            content = rpmlist.readline()

    with open("download.sh", "w") as result_file:
        result_file.write("#!/bin/bash\n")
        result_file.write("echo 'starting to download full packages : {0}'\n".format(len(results)))
        count = 1
        for item in results:
            result_file.write("echo 'starting to download {0}/{1}'\n".format(count, len(results)))
            result_file.write("%s\n" % item)
            count = count+1
except Exception as e:
    print(e)
