# Parameter explanation
|  parameters   | usage | required | optional value |
|  ----  | ----  | --- | --- |
| type   | what do you want to import to gitlab, a repository or a organization |  True  | repository / organization |
| source  | information of your source repository or organization  | True  | / |
| target  | information of your target repository or organization | True  | / |
| duration  | the time of executing cron job  | True | / |
| org  | 1.in source: the organization of your repository or the source organization.  2.in target: the organization which you want to backup your repositories.| True  | / |
| platform  |  1.in source: the repository's or organization's code platform (such as github, gitee). 2.in target: the place where you can backup your repositories.| True  | target platform has a default value (gitlab) |
| url  | 1.in source: the source link of organization. 2.in target: the target link of organization which you want to backup  | True  | / |

# Example config
## repository's config
###   
      - task:
        - duration: "H * * 0 *"
          type: repository
          source:
          - org: cert-manager
            repos:
            - cert-manager
            platform: github
            url: https://github.com/cert-manager
          target:
          - org: opensourceway
            platform: gitlab
            url: https://source.openeuler.sh/opensourceway
## organization's config
### 
      - task:
        - duration: "H * * 0 *"
          type: organization
          source:
          - org: opengauss
            platform: gitee
            url: https://gitee.com/opengauss
          target:
          - org: opengauss
            platform: gitlab
            url: https://source.openeuler.sh/opengauss
