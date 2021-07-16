pipeline {
    agent { node { label 'infra-check' } }
    environment {
        GITEE_TOKEN = credentials('openeuler-ci-bot')
    }
    stages {
        stage('source code clone') {
            steps {
                sh """#!/bin/sh -e

                test -f ci_tags.py && rm ci_tags.py*
                wget https://gitee.com/openeuler/infrastructure/raw/master/ci/tools/ci_tags.py
                python3 ci_tags.py $giteeTargetNamespace $giteeTargetRepoName $giteePullRequestIid $GITEE_TOKEN ATP

                if [ -d "PR-$giteePullRequestIid" ]; then
                    echo "The build is running by another trigger, please try again later!"
                    exit 1
                fi
                mkdir PR-$giteePullRequestIid
                cd PR-$giteePullRequestIid
                if [ -d community ]; then
                rm -rf community
                fi
                git clone https://gitee.com/$giteeSourceNamespace/community.git
                cd community
                git fetch origin pull/$giteePullRequestIid/head:$giteeSourceNamespace/$giteeSourceBranch
                git checkout $giteeSourceNamespace/$giteeSourceBranch
                """
            }
        }

        stage('sanity_check'){
            steps{
                sh """#!/bin/sh -e

                cd PR-$giteePullRequestIid
                python3 community/zh/technical-committee/governance/sanity_check.py community
                """
            }
        }

        stage('branch check'){
            steps{
                sh """#!/bin/sh -e

                cd PR-$giteePullRequestIid
                test -f branch.yaml && rm branch.yaml
                wget https://gitee.com/openeuler/infrastructure/raw/master/ci/tools/branch.yaml
                test -f check_branch.py && rm check_branch.py
                wget https://gitee.com/openeuler/infrastructure/raw/master/ci/tools/check_branch.py
                python3 check_branch.py -conf branch.yaml -repo community -id $giteePullRequestIid
                """
            }
        }

        stage('sig info check'){
            steps{
                sh """#!/bin/sh -e

                cd PR-$giteePullRequestIid
                test -f sigInfoCheck.py && rm sigInfoCheck.py*
                test -f /tmp/sigs.yaml && rm /tmp/sigs.yaml*
                test -f /tmp/diff.txt && rm /tmp/diff.txt*
                wget https://gitee.com/openeuler/infrastructure/raw/master/ci/tools/sigInfoCheck.py
                python3 sigInfoCheck.py $giteeTargetNamespace $giteeTargetRepoName $giteePullRequestIid $GITEE_TOKEN
                """

            }
        }

        stage('validate user and projects'){
            parallel {
        		stage('validate gitee user') {
		            steps {
		                sh "/home/infra_check/validator owner check -f OWNERS -d  ${WORKSPACE}/PR-${giteePullRequestIid}/community/sig -g ${GITEE_TOKEN}"

		            }
        		}
		        stage('validate gitee project') {
		            steps {
		                sh '''#!/bin/bash
                         cd ${WORKSPACE}/PR-${giteePullRequestIid}/community
                         git fetch origin master:master
                         export OPENEULER_IGNORE=$(git diff origin/master... -- repository/openeuler.yaml | grep '^+- name:' | sed 's/+- name://g' | tr -d '[:blank:]' | awk '{printf "openeuler/%s,", $0}')
                         export SRC_OPENEULER_IGNORE=$(git diff origin/master... -- repository/src-openeuler.yaml | grep '^+- name:' | sed 's/+- name://g' | tr -d '[:blank:]' | awk '{printf "src-openeuler/%s,", $0}')
                         echo "${OPENEULER_IGNORE}${SRC_OPENEULER_IGNORE}"
                         /home/infra_check/validator sig checkrepo -f ${WORKSPACE}/PR-${giteePullRequestIid}/community/sig/sigs.yaml -g ${GITEE_TOKEN} -i "${OPENEULER_IGNORE}${SRC_OPENEULER_IGNORE}"
                          '''
		            }
		        }
		    }
        }
    }

    post {
        success {
        	script {
        		comments = giteeCommentHeader + "| Infra Check | **success** :white_check_mark: | [#${currentBuild.fullDisplayName}](${env.BUILD_URL}/console) | \n"
        	    sh "python3 ci_tags.py $giteeTargetNamespace $giteeTargetRepoName $giteePullRequestIid $GITEE_TOKEN ATS"
        	}
        	addGiteeMRComment comment: comments
            echo 'succeeded!'

        }

        failure {
        	script {
                comments = giteeCommentHeader + "| Infra Check | **failed** :x: | [#${currentBuild.fullDisplayName}](${env.BUILD_URL}) | \n"
        	    sh "python3 ci_tags.py $giteeTargetNamespace $giteeTargetRepoName $giteePullRequestIid $GITEE_TOKEN ATF"
        	}
        	addGiteeMRComment comment: comments
            echo 'failed :('
        }

        always {
            sh """#!/bin/sh -e

            rm -rf PR-$giteePullRequestIid
            """
        }
    }
}
