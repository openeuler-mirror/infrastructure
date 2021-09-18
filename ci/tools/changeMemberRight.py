import argparse
import re
import os
import sys
import requests
import json

GET_URL = "https://api.gitee.com/enterprises/{}/members"
SET_URL = "https://api.gitee.com/enterprises/{}/members/{}"
FILENAME = "memberinfo.log"

def getMemberRightInfo(enterid, token):
    '''
    This function is to get the members info of enterprise.
    '''
    get_url = GET_URL.format(enterid)
    param = {'access_token': token, 'page': '1'}
    print(get_url)
    response = requests.get(get_url, params=param, timeout=10)
    if response.status_code != 200:
        print("Get issues failed, error code:{}.".format(response.status_code))
        return
    members = []

    jstr = json.loads(response.text)
    total_count = jstr['total_count']
    print(total_count)
    users = jstr['data']

    return users

def setSingleMemberRight(enterid, token, memerid, roleid):
    '''
    This function is to set a member right.
    '''
    set_url = SET_URL.format(enterid, memerid)
    param = {'access_token': token, 'role_id': roleid}
    response = requests.put(set_url, params=param, timeout=10)
    if response.status_code != 200:
        print("Get issues failed, error code:{}.".format(response.status_code))
        return
    member = json.loads(response.text)
    return member

def changeAllMemberRight(users, enterid, token, OLD_ROLE_ID, NEW_ROLE_ID):

    with open(FILENAME, 'w') as f:
        for idx, member in enumerate(users):
            print('==================================')
            userinfo = member['user']
            enterprise_role = member['enterprise_role']
            memberinfomation = "INDEX:{:<4}. UserInfo: {:<16},{:<20}. RoleInfo: {:<16},{:<16}.".format(idx,
                                                                                     userinfo["id"],
                                                                                     userinfo["login"],
                                                                                     enterprise_role['id'],
                                                                                     enterprise_role['name'])
            print(memberinfomation)
            f.write(memberinfomation)
            f.write(",\n")

            if (OLD_ROLE_ID != enterprise_role['id']):
                print("USER:{} :OLD_ROLE_ID:{}, CUR_ID:{}.".format(userinfo["id"], OLD_ROLE_ID, enterprise_role['id']))
                continue

            newMember = setSingleMemberRight(enterid, token, userinfo["id"], NEW_ROLE_ID)
            newUserinfo = newMember['user']
            newEnterprise_role = newMember['enterprise_role']
            newMemberinfomation = "INDEX:{:<4}. UserInfo: {:<16},{:<20}. RoleInfo: {:<16},{:<16}.".format(idx,
                                                                          newUserinfo["id"],
                                                                          newUserinfo["login"],
                                                                          newEnterprise_role['id'],
                                                                          newEnterprise_role['name'])
            print(newMemberinfomation)
            f.write(newMemberinfomation)
            f.write(",\n")
    return

if __name__ == '__main__':
    if len(sys.argv) != 5:
        for arg in sys.argv:
            print(arg)
        print("参数错误，enterprise_id , v8Token, oldroleid, newroleid")
        print("请参考: https://gitee.com/api/v8/swagger#/putEnterpriseIdMembersUserId")
        sys.exit(2)
    enterid = sys.argv[1]
    token = sys.argv[2]
    OLD_ROLE_ID = sys.argv[3]
    NEW_ROLE_ID = sys.argv[4]
    users = getMemberRightInfo(enterid, token)
    changeAllMemberRight(users, enterid, token, OLD_ROLE_ID, NEW_ROLE_ID)