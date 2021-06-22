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
        self.branch_map = None
        self.branch_map_yaml = branch_map_yaml
        self.pr_id = pr_id
        self.community_path = community_path
        self.change_msg = self._get_change_msg()
        self._get_branch_map()

    def _get_change_msg(self):
        """
        get messages of changeing about branch
        """
        change_msg = []
        if os.path.exists(self.community_path):
            cmd = "cd {0} && git diff --name-status HEAD~1 HEAD~0 | grep src-openeuler.yaml".format(self.community_path)
            ret = os.popen(cmd).read()
            if ret:
                cmd = "cd {0} && git diff HEAD~1 HEAD~0 | grep '^+ '".format(self.community_path)
                ret = os.popen(cmd).read()
                self._parse_change_msg(ret, change_msg)
        return change_msg

    def _get_branch_map(self):
        """
        get branch map from yaml file
        """
        if os.path.exists(self.branch_map_yaml):
            with open(self.branch_map_yaml, 'r', encoding='utf-8') as f:
                self.branch_map = yaml.load(f, Loader=yaml.FullLoader)
        else:
            raise FileError("ERROR: No file {0}".format(self.branch_map_yaml)) 

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
                    change_msg.append({"mbranch": mbranch, "sbranch": sbranch})
                sbranch = msg.split(':')[-1].strip()
                mbranch = None
            if "create_from" in msg:
                mbranch = msg.split(':')[-1].strip()
        change_msg.append({"mbranch": mbranch, "sbranch": sbranch})

    def _check_branch(self, mbranch, sbranch):
        """
        check
        :parm mbranch: branch which now branch created from
        :parm sbranch: now branch
        """
        if sbranch == "master":
            pass
        else:
            self._check_main_branch(mbranch)
            self._check_sub_branch(mbranch, sbranch)

    def _check_main_branch(self, mbranch):
        """
        check main branch which now branch created from
        :parm mbranch: main branch
        """
        if mbranch not in self.branch_map["branch"].keys():
            if mbranch.startswith("Multi"):
                if mbranch.split("_")[-1] not in self.branch_map["branch"].keys():
                    raise CheckError("FAIL: Not found main branch {0}".format(mbranch.split("_")[-1]))
                else:
                    print("Check main branch {0} SUCCESS".format(mbranch.split("_")[-1]))
            elif mbranch.startswith("oepkg"):
                tmp = mbranch.split("_")[-1]
                if tmp.startswith("oe"):
                    tmp = tmp.replace("oe", "openEuler")
                    if tmp not in self.branch_map["branch"].keys():
                        raise CheckError("FAIL: Not found main branch {0}".format(tmp))
                    else:
                        print("Check main branch {0} SUCCESS".format(tmp))
                else:
                    raise CheckError("FAIL: Not found main branch {0}".format(tmp))
            else:
                raise CheckError("FAIL: Not found main branch {0}".format(mbranch))
        else:
            print("Check main branch {0} SUCCESS".format(mbranch))

    def _check_sub_branch(self, mbranch, sbranch):
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
                raise CheckError("FAIL: main branch is wrong")

        if sbranch not in self.branch_map["branch"][mbranch]:
            sb = sbranch.split("_")
            if sbranch.startswith("Multi"):
                if "Multi-Version" != sb[0]:
                    raise CheckError("FAIL: sub branch {0} is wrong".format(sbranch))
                if sb[-1] not in self.branch_map["branch"][mbranch]:
                    raise CheckError("FAIL: sub branch {0}\'s {1} not found in list given by main branch {2}"\
                            .format(sbranch, sb[-1], mbranch))
            elif sbranch.startswith("oepkg"):
                if sb[-1].startswith("oe"):
                    tmp = sb[-1].replace("oe", "openEuler")
                    if tmp not in self.branch_map["branch"][mbranch]:
                        raise CheckError("FAIL: sub branch {0}\'s {1} not found in list given by main branch {2}"\
                                .format(sbranch, sb[-1], mbranch))
                else:
                    raise CheckError("FAIL: sub branch is wrong")
            elif sbranch.startswith("openEuler"):
                raise CheckWarn("WARN: sub branch {0} not found in list given by main branch {1}".format(sbranch, mbranch))
            else:
                raise CheckError("FAIL: sub branch {0} not found in list given by main branch {1}".format(sbranch, mbranch))
            print("Check sub branch {0} SUCCESS".format(sbranch))
        else:
            print("Check sub branch {0} SUCCESS".format(sbranch))

    def check(self):
        """
        check start
        """
        error_flag = 0
        warn_flag = 0
        for _dict in self.change_msg:
            try:
                self._check_branch(_dict["mbranch"], _dict["sbranch"])
            except CheckError as e:
                print(e)
                error_flag = error_flag + 1
            except CheckWarn as e:
                print(e)
                warn_flag = warn_flag + 1
            except FileError as e:
                print(e)
                error_flag = error_flag + 1
        print("========================")
        print("Check PR {0} Result: error {1}, warn {2}".format(self.pr_id, error_flag, warn_flag))
        if error_flag:
            sys.exit(1)


if __name__ == "__main__":
    import argparse
    par = argparse.ArgumentParser()
    par.add_argument("-conf", "--config", help="branch map", required=True)
    par.add_argument("-id", "--pr_id", help="community pr id, you", required=True)
    par.add_argument("-repo", "--community_repo_path", help="community repo path", required=True)
    args = par.parse_args()
    C = checkBranch(args.config, args.community_repo_path, args.pr_id)
    C.check()
