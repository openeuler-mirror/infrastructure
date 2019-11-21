def jobsString = "task-check-binary-file,task-check-code-style,task-check-patchname,openeuler-rpm-build"
ArrayList jobsList = jobsString.split('\\,')

def parallelJobs2Run = [:]
def parallelJobResults = [:]
jobsList.each { job ->
    echo "Going to parallel for job ${job}"
    parallelJobs2Run["${job}"] = { ->
        echo "Calling job ${job}"
        jobResults=build job: "${job}",
        parameters: [
            string(name: 'giteeTargetRepoName', value: env.giteeTargetRepoName),
            string(name: 'giteePullRequestIid', value: env.giteePullRequestIid),
            string(name: 'giteeBranch', value: env.giteeBranch)
                ],
        propagate: false,
        wait: true

        parallelJobResults["${job}"] = jobResults
    }
};

parallel parallelJobs2Run
parallelJobResults.each { name, result ->
    echo "Details for job ${name}"
    echo "RESULT: ${result.result}"
    echo "URL: ${result.absoluteUrl}"
    echo "NUMBER: ${result.number}"
}

giteeComments = "| Check Name | Build Result | Build Details |\n| --- | --- | --- |\n"

def JobSuccess = true
parallelJobResults.each {name, result ->
    echo result.result
    if (result.result == "SUCCESS") {
        resultIcon = ":white_check_mark: "
    } else {
        JobSuccess = false
        resultIcon = ":x:"
    }
    giteeComments += "|  ${name} | ${resultIcon}**${result.result}** |  [#${result.number}](${result.absoluteUrl}/console) |\n"
}

addGiteeMRComment(giteeComments)

if (JobSuccess) {
    currentBuild.result = 'SUCCESS'
    } else {
    currentBuild.result = 'FAILURE'
}
