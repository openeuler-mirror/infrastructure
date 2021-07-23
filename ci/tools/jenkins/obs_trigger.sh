#!/bin/bash

pip3 install python-jenkins
test -f obs_trigger.py && rm obs_trigger.py
test -f retry.yaml && rm retry.yaml
wget https://gitee.com/openeuler/infrastructure/raw/master/ci/tools/jenkins/obs_trigger.py
wget https://gitee.com/openeuler/infrastructure/raw/master/ci/tools/jenkins/retry.yaml
python3 obs_trigger.py $giteeTargetNamespace $giteeTargetRepoName $giteePullRequestIid $GITEE_TOKEN $OBS_USER $OBS_PWD
