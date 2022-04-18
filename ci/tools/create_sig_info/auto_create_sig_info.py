import os

import yaml
import sys


def load_yaml(file_path):
    """
    load yaml
    :param file_path: yaml file path
    :return: content of yaml
    """
    with open(file_path, encoding="utf-8") as fp:
        try:
            content = yaml.load(fp.read(), Loader=yaml.Loader)
        except yaml.MarkedYAMLError as e:
            print(e)
            sys.exit(1)
    return content


def get_owners_and_sig_name(directory_path):
    sig_name_owners = {}
    sig_path = os.path.join(directory_path, "sig")
    for sig in os.listdir(sig_path):
        if os.path.isdir(os.path.join(sig_path, sig)):
            sig_name_owners[sig] = os.path.join(directory_path, "sig") + "/" + sig + "/OWNERS"
    return sig_name_owners


def make_template_file_data_and_write(sig_name_owners):
    content = {}
    for sig_name, owners_path in sig_name_owners.items():
        content["name"] = sig_name
        content["description"] = "NA"
        content["mailing_list"] = "NA"
        content["meeting_url"] = "NA"
        content["mature_level"] = "NA"
        content["mentors"] = [{"gitee_id": "--xxx--", "name": "xxx", "organization": "xxx", "email": "xxxx@xxx"}]

        v = []
        for m in decode_owners(owners_path):
            v.append({"gitee_id": m, "name": "xxx", "organization": "xxx", "email": "xxx"})

        if len(v) == 0:
            content["maintainers"] = [{"gitee_id": "--xxx--", "name": "xxx", "organization": "xxx", "email": "xxx"}]
        else:
            content["maintainers"] = v

        repos = []
        for root, dirs, files in os.walk(owners_path.split("OWNERS")[0]):
            if len(dirs) == 0:
                if len(files) == 0:
                    break
                for f in files:
                    if root.count("/") > 2 and f.endswith(".yaml"):
                        repos.append(root.split("/")[-2] + '/' + f.split(".yaml")[0])
                    else:
                        continue
        if len(repos) == 0:
            content["repositories"] = [{"repo": ["example/repos1", "example/repos2"], "committers": [{"gitee_id": "--xxx--", "name": "xxx", "organization": "xxx", "email": "xxxx@xxx"}],
                                        "contributors": [{"gitee_id": "--xxx--", "name": "xxx", "organization": "xxx", "email": "xxxx@xxx"}],}, {"repo": ["example/repos1", "example/repos2"],}, ]
        else:
            content["repositories"] = [{"repo": repos, "committers": [{"gitee_id": "--xxx--", "name": "xxx", "organization": "xxx", "email": "xxxx@xxx"}],
                                        "contributors": [{"gitee_id": "--xxx--", "name": "xxx", "organization": "xxx", "email": "xxxx@xxx"}], }]
        if os.path.exists(os.path.join(owners_path.split("OWNERS")[0], "sig-info.yaml")):
            continue
        print(sig_name)
        write_yaml_to_sig(owners_path.split("OWNERS")[0], content)


def decode_owners(owners_path):
    if os.path.exists(owners_path):
        c = load_yaml(owners_path)
        return c["maintainers"]
    else:
        return []


def write_yaml_to_sig(dst_path, data):
    file_path = os.path.join(dst_path, "sig-info.yaml")
    with open(file_path, 'w', encoding="utf-8") as f:
        yaml.dump(data, f, Dumper=yaml.Dumper, sort_keys=False)


def main():
    owners_sigs = get_owners_and_sig_name("community".split("/")[-1])
    make_template_file_data_and_write(owners_sigs)


# this file is used to create sig-info.yaml for sig automatically
# make sure this script will be executed in the place where community folder exists.
# 执行脚本时，确保和community文件夹处于同一目录下。
if __name__ == '__main__':
    main()

