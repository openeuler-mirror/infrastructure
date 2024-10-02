1. **How do I apply for joining the openEuler organization on Gitee?**

    Click this [link](https://gitee.com/open_euler?invite=10c2a5093d0832fb8ca218f5b1b951684826839babb9d3c68e7cde0b62298f898e2a5d1b1b807987439bc1f65eaa027860f010c409ba4a18108234d13d970cb1), fill in related information, and submit you application.

    Applications are usually reviewed and approved within three working days. If your application is not approved in time, send an email to [infra@openeuler.sh](mailto:infra@openeuler.sh).

---

2. **How do I create a code repository in the openEuler community?**

    To create a code repository in the openEuler community, perform the following steps:

    1. The user modifies the repository configuration file and submits a pull request (PR).
    2. The TC reviews the application. Once the application is approved, the PR will be merged. The TC may have questions during the review process. Therefore, the applicant is advised to monitor the status of the PR for any updates or inquiries.
    3. openeuler-ci-bot automatically creates a code repository based on the repository configuration file.

    In short, to create a code repository, refer to this [link](https://gitee.com/openeuler/community/tree/master/repository) to modify the configuration file, submit a PR, and then track the PR status and creation of your repository.

    If the code repository has not been created two hours after the PR is merged, contact [infra@openeuler.org](mailto:infra@openeuler.org) or submit an issue to the [infrastructure repository](https://gitee.com/openeuler/infrastructure).

---

3. **What can I do if the openeuler-cla/no label is added to my PR?**

    This label indicates that the commits of the PR are authored by one or more contributors who have not signed the CLA of the openEuler community. You can find the [signing address](https://gitee.com/link?target=https%3A%2F%2Fclasign.osinfra.cn%2Fsign%2FZ2l0ZWUlMkZvcGVuZXVsZXI%3D) in the PR comment area. Sign the individual CLA or employee CLA accordingly. Use an email address of your corporation (for example, <xxx@huawei.com> or <xxx@kylinos.cn>) when you sign the employee CLA. The CLA check is based on the author email address of each commit. You can run the `git log --pretty=fuller` command to query the email address.

    <table>
    <tbody><tr>
    <th>Scenario</th>
    <th>Option</th>
    <th>Solution</th>
    </tr>
    <tr>
    <td>The author email address is the Gitee commit email address.</td>
    <td>Using the email address</td>
    <td>Use the email address to sign the CLA.</td>
    </tr>
    <tr>
    <td rowspan="2">The author email address is not the Gitee commit email address.</td>
    <td>Using the author email address</td>
    <td>On the Settings page of Gitee , add the author email address as the commit email address. Then, sign the CLA.</td>
    </tr>
    <tr>
    <td>Using the Gitee commit email address</td>
    <td>On the computer where you use Git, run <b>git config --global user.name your_user_name and git config --global user.email your_email</b> to change the author email address to the Gitee commit email address. Then, sign the CLA.</td>
    </tr>
    </tbody>
    </table>

---

4. **Why can't I fork the src-openeuler/abcd repository to my account?**

    This error typically occurs if you already have a repository named **abcd**, such as an **abcd** repository forked from the openEuler organization. Gitee repository links include both the account and repository name. Therefore, duplicate repository names under your account are not allowed.

    Change the name and path of the existing repository, and then fork the **src-openeuler/abcd** repository again.

---

5. **Can I directly push code to non-protected branches as a non-maintainer contributor?**

    Sorry, non-maintainer contributors cannot directly push code to any branches in the repositories, including both protected and unprotected branches.

    The difference between protected and unprotected branches lies in whether maintainers can directly push code to them. On unprotected branches, maintainers have the permission to push code directly. However, on protected branches, even maintainers cannot directly push code. Instead, they must submit changes through PRs, which are then merged by openeuler-ci-bot.

---

6. **Can maintainers directly push code to repositories?**

    Maintainers can push code directly to unprotected branches, but not to protected branches.

---

7. **What is the difference between directly pushing code to a repository and merging code by commenting /lgtm or /approve?**

    Using Git commands to directly push code to a repository bypasses the necessary review process, introducing risks. For example, when a file to upload is too large for a personal repository, you need push it directly to an unprotected branch in the organization repository, then merge the change into a protected branch.

    The code review process using the "/lgtm" or "/approve" comment ensures that at least one maintainer other than the author approves each code merging. Even if the author is a maintainer, another maintainer's approval is required before the code can be merged.

---

8. **What commands can I use in the comments area of openEuler community repositories and what are their functions?**

    See the [openEuler Community Command Help](https://gitee.com/openeuler/community/blob/master/en/sig-infrastructure/command.md) for the supported commands.

---

9. **Why is CI build not triggered after I submit a PR? What should I do?**

    CI build will not be triggered in the following scenarios:

    1. The network or system task scheduling may be faulty. As a result, the webhook notification event sent from the code repository does not reach the target service in time, and CI build is not triggered. In this case, you can comment "/retest" in the PR to manually trigger CI build.

    2. The PR is submitted within a short period of time after the code repository is created. At this time, the CI project is not created on the Jenkins server. Therefore, CI build cannot be triggered, and the "/retest" comment does not take effect. In this case, wait for the system to create the CI project or contact <infra@openeuler.org>.

---

10. **How do I modify the attributes of a branch?**

    In <https://gitee.com/openeuler/community/tree/master/repository>, open configuration files **openeuler.yaml** and **src-openeuler.yaml**, locate the target repository name and branch, and modify the branch attributes. openeuler-ci-bot will update the attribute information to the repository.

    If the modification does not take effect within one hour, contact <infra@openeuler.org>.

---

11. **How do I work with tags in an organization repository?**

    List all tags of a repository:

    ```shell
    git tag
    ```

    View details of tag **v2.0**:

    ```shell
    git show v2.0
    ```

    Create a tag **v2.0** for a specific commit:

    ```shell
    git tag -a v2.0 ea0982sf34
    ```

    Push tag **v2.0** to a remote repository:

    ```shell
    git push origin v2.0
    ```

    Delete tag **v2.0** locally:

    ```shell
    git tag -d v2.0
    ```

    Delete tag **v2.0** from a remote repository (the empty value before the colon indicates deletion):

    > Note: Repository developers (openEuler community maintainers) have the permission to push tags to organization repositories such as **openeuler/infrastructure**.

    ```shell
    git push origin :refs/tags/v2.0
    ```

---

12. **Why cannot a PR be associated with issues?**

    A PR may not be associated with issues due to the following reasons:

    - You do not have related permissions and need to join the openEuler organization. For details, see question 1.
    - The issue you want to associate the PR with belongs to another repository. Perform the following operations on Gitee Enterprise Edition:
    On <https://e.gitee.com/open_euler/dashboard>, choose **Code** > _Repository_ > **Pull Request** > _PR_ > **Relate Issue**, then enter the issue ID.

---

13. **How do I change or remove the members to mention in the welcome information in PRs and issues?**
    - To change members to mention:
        1. Create an issue in the [infrastructure repository](https://gitee.com/openeuler/infrastructure) to specify the repository for which members need to be changed.
        2. Create a **PATH_OWNER_MAPPING.YAML** file in the repository for which members need to be changed. See [File example](https://gitee.com/openeuler/docs/blob/master/PATH_OWNER_MAPPING.YAML).
        3. The infrastructure SIG will update the information based on the file.
    - To remove members to mention:
        1. Create an issue in the [infrastructure repository](https://gitee.com/openeuler/infrastructure) to specify the repository for which members need to be removed.
        2. The infrastructure SIG will update the information.

---