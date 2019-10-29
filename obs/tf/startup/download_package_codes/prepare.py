import xmlplain

try:
    # Read to plain object
    with open("projects_raw.xml") as inf:
        root = xmlplain.xml_to_obj(inf, strip_space=True, fold_dict=True)

    projects = []
    for project in root['manifest']:
        projects.append(
            "git clone https://gitee.com/openeuler/{0}.git".format(project['project']['@path'].split("/")[-1]))

    # Output plain YAML
    with open("download.sh", "w") as outf:
        outf.write("#!/bin/bash\n")
        for line in projects:
            outf.write("echo 'git clone project: {0}'\n".format(line))
            outf.write("{0}\n".format(line))


except Exception as e:
    print(e)
