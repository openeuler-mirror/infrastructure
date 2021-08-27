#/bin/env python3
# -*- encoding=utf8 -*-
#******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Author: miao_kaibo
# Create: 2021-06-18
# ******************************************************************************
import os
import sys
import yaml
import subprocess


class CheckError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return self.message


class FileError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return self.message


class CheckWarn(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return self.message


class checkBranch(object):
    def __init__(self, branch_map_yaml, community_path, pr_id):
        """
        :parm branch_map_yaml: yaml file of branch map
        :parm community_path: community repo path
        :parm pr_id: id of community pr
        """
        self.error_flag = 0
        self.warn_flag = 0
        self.branch_map = None
        self.branch_map_yaml = branch_map_yaml
        self.pr_id = pr_id
        self.community_path = community_path
        self._get_branch_map()
        self.change_msg = []

    def get_change_msg(self):
        """
        get messages of changeing about branch
        """
        if os.path.exists(self.community_path):
            cmd = "cd {0} && git diff --name-status HEAD~1 HEAD~0 | grep src-openeuler.yaml".format(self.community_path)
            ret = os.popen(cmd).read()
            if ret:
                cmd = "cd {0} && git diff HEAD~1 HEAD~0 | grep '^+ '".format(self.community_path)
                p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
                out = p.stdout.read().decode("utf-8")
                self._parse_change_msg(out, self.change_msg)

    def _get_branch_map(self):
        """
        get branch map from yaml file
        """
        if os.path.exists(self.branch_map_yaml):
            with open(self.branch_map_yaml, 'r', encoding='utf-8') as f:
                self.branch_map = yaml.load(f, Loader=yaml.FullLoader)
        else:
            raise FileError("ERROR: No file {0}".format(self.branch_map_yaml)) 

    def get_src_openeuler_yaml(self):
        """
        get message from src-openeuler.yaml
        """
        src_openeuler_yaml = os.path.join(self.community_path, "repository", "src-openeuler.yaml")
        if os.path.exists(src_openeuler_yaml):
            with open(src_openeuler_yaml, 'r', encoding='utf-8') as f:
                self.change_msg = yaml.load(f, Loader=yaml.FullLoader)["repositories"]
        else:
            raise FileError("ERROR: No file {0}".format(src_openeuler_yaml))

    def _parse_change_msg(self, message, change_msg):
        """
        parser for messsages
        :parm message: message about branch
        :parm change_msg: list which store message
        """
        message = message.split('\n')
        while '' in message:
            message.remove('')
        mbranch = None
        sbranch = None
        for msg in message:
            if "  - name" in msg:
                if sbranch:
                    if mbranch:
                        change_msg.append({"mbranch": mbranch, "sbranch": sbranch})
                    elif sbranch:
                        if sbranch == "master":
                            pass
                        else:
                            print("WARN: No main branch, if just to change sub branch, you can ignore this")
                            self.warn_flag = self.warn_flag + 1
                sbranch = msg.split(':')[-1].strip()
                mbranch = None
            if "create_from" in msg:
                mbranch = msg.split(':')[-1].strip()
        if sbranch and mbranch:
            change_msg.append({"mbranch": mbranch, "sbranch": sbranch})
        elif sbranch:
            if sbranch == "master":
                pass
            else:
                print("WARN: No main branch, if just to change sub branch, you can ignore this")
                self.warn_flag = self.warn_flag + 1

    def _check_branch(self, mbranch, sbranch, pkg_name=''):
        """
        check
        :parm mbranch: branch which now branch created from
        :parm sbranch: now branch
        """
        if sbranch == "master":
            if mbranch:
                raise CheckError("FAIL: {} master cannot branch from other branch".format(pkg_name))
            else:
                pass
        else:
            self._check_main_branch(mbranch, pkg_name=pkg_name)
            self._check_sub_branch(mbranch, sbranch, pkg_name=pkg_name)

    def _check_main_branch(self, mbranch, pkg_name=''):
        """
        check main branch which now branch created from
        :parm mbranch: main branch
        """
        if mbranch not in self.branch_map["branch"].keys():
            if mbranch.startswith("Multi"):
                if mbranch.split("_")[-1] not in self.branch_map["branch"].keys():
                    raise CheckError("FAIL: {0} Not found main branch {1}".format(pkg_name, mbranch.split("_")[-1]))
            elif mbranch.startswith("oepkg"):
                tmp = mbranch.split("_")[-1]
                if tmp.startswith("oe"):
                    tmp = tmp.replace("oe", "openEuler")
                    if tmp not in self.branch_map["branch"].keys():
                        raise CheckError("FAIL: {0} Not found main branch {1}".format(pkg_name, tmp))
                else:
                    raise CheckError("FAIL: {0} Not found main branch {1}".format(pkg_name, tmp))
            else:
                raise CheckError("FAIL: {0} Not found main branch {1}".format(pkg_name, mbranch))

    def _check_sub_branch(self, mbranch, sbranch, pkg_name=''):
        """
        check sub branch
        :parm mbranch: main branch
        :parm sbranch: sub branch
        """
        if mbranch not in self.branch_map["branch"].keys():
            if mbranch.startswith("Multi"):
                mbranch = mbranch.split("_")[-1]
            elif mbranch.startswith("oepkg"):
                if "_oe" in mbranch:
                    mbranch = mbranch.split("_")[-1].replace("oe", "openEuler")
            else:
                raise CheckError("FAIL: {0} main branch is wrong".format(pkg_name))

        if sbranch not in self.branch_map["branch"][mbranch]:
            sb = sbranch.split("_")
            if sbranch.startswith("Multi"):
                if "Multi-Version" != sb[0]:
                    raise CheckError("FAIL: {0} sub branch {1} is wrong".format(pkg_name, sbranch))
                if sb[-1] not in self.branch_map["branch"][mbranch]:
                    raise CheckError("FAIL: {0} sub branch {1}\'s {2} not found in list given by main branch {3}"\
                            .format(pkg_name, sbranch, sb[-1], mbranch))
            elif sbranch.startswith("oepkg"):
                if sb[-1].startswith("oe"):
                    tmp = sb[-1].replace("oe", "openEuler")
                    if tmp not in self.branch_map["branch"][mbranch]:
                        raise CheckError("FAIL: {0} sub branch {1}\'s {2} not found in list given by main branch {3}"\
                                .format(pkg_name, sbranch, sb[-1], mbranch))
                else:
                    raise CheckError("FAIL: {0} sub branch is wrong".format(pkg_name))
            else:
                raise CheckError("FAIL: {0} sub branch {1} not found in list given by main branch {2}".format(pkg_name, sbranch, mbranch))

    def check(self):
        """
        check start
        """
        for _dict in self.change_msg:
            try:
                self._check_branch(_dict["mbranch"], _dict["sbranch"])
            except CheckError as e:
                print(e)
                self.error_flag = self.error_flag + 1
            except CheckWarn as e:
                print(e)
                self.warn_flag = self.warn_flag + 1
            except FileError as e:
                print(e)
                self.error_flag = self.error_flag + 1
        print("Check PR {0} Result: error {1}, warn {2}".format(self.pr_id, self.error_flag, self.warn_flag))
        if self.error_flag:
            sys.exit(1)

    def check_all(self):
        for pkg in self.change_msg:
            pkg_name = pkg["name"]
            branches = pkg["branches"]
            for bch in branches:
                sbranch = bch['name']
                if sbranch == "master":
                    mbranch = None
                else:
                    mbranch = bch['create_from']
                try:
                    self._check_branch(mbranch, sbranch, pkg_name=pkg_name)
                except CheckError as e:
                    print(e)
                    self.error_flag = self.error_flag + 1
                except CheckWarn as e:
                    print(e)
                    self.warn_flag = self.warn_flag + 1
                except FileError as e:
                    print(e)
                    self.error_flag = self.error_flag + 1
        print("Check PR {0} Result: error {1}, warn {2}".format(self.pr_id, self.error_flag, self.warn_flag))
        if self.error_flag:
            sys.exit(1)


if __name__ == "__main__":
    import argparse
    par = argparse.ArgumentParser()
    par.add_argument("-conf", "--config", help="branch map", required=True)
    par.add_argument("-id", "--pr_id", help="community pr id, you", required=True)
    par.add_argument("-repo", "--community_repo_path", help="community repo path", required=True)
    par.add_argument("-a", "--all", help="check all packages", default="False")
    args = par.parse_args()
    C = checkBranch(args.config, args.community_repo_path, args.pr_id)
    if args.all == "True":
        C.get_src_openeuler_yaml()
        C.check_all()
    else:
        C.get_change_msg()
        C.check()
