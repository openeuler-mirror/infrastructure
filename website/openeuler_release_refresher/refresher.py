import os
from gitee_actions import handler as giteehandler
from obs_actions import handler

# Prepare requirement configs
# 1. Config for OBS related.
# AK/SK use for OBS access authentication.
# Since the folder is open for read, we can left it empty.
OBS_AK = ""
OBS_SK = ""
# OBS_ENDPOINT is the HuaweiCloud OBS API endpoint, not a IP address.
OBS_ENDPOINT = "obs.cn-south-1.myhuaweicloud.com"
# *_BUCKET and *_FOLDER used for release files visiting
OPENEULER_BUCKET = "openeuler-release"
OPENEULER_FOLDER = "openeuler/"


# 2. Config for Gitee related.
# PROJECT_OWNER
PROJECT_OWNER = "TommyLike"
# PROJECT
PROJECT = "test_openeuler"
# release folder inside of the project
RELEASE_FOLDER = "download_folder"
# project branch
BRANCH = "master"

COMMITTER_NAME = "TommyLike"
COMMITTER_EMAIL = "tommylikehu@gmail.com"


# event type is ignored, since we will always do a full scan when triggered.
def handling(event, context):

    if not os.environ.has_key("GITEE_TOKEN"):
        print("Please set 'GITEE_TOKEN' in environment.")
        exit(1)
    GITEE_TOKEN = os.environ["GITEE_TOKEN"]

    print("starting to refresh gitee files based on obs information")
    # Running Steps:
    # 1. Collecting available release files, return empty if has error
    obs_handler = handler.ObsHandler(ak=OBS_AK, sk=OBS_SK,
                                     endpoint=OBS_ENDPOINT,
                                     accept_types=["image", "img", "iso"])

    release_files = obs_handler.get_available_releases(OPENEULER_BUCKET,
                                                       OPENEULER_FOLDER)
    if len(release_files) == 0:
        print(
            "no release files found in OBS bucket, skip committing changes.")
        exit(0)

    # 2. Patch gitee files based on the files from obs and existing
    # files on gitee, the `lastModified` attribute will be considered.
    gitee_handler = giteehandler.GiteeHandler(access_token=GITEE_TOKEN,
                                              owner=PROJECT_OWNER,
                                              project=PROJECT,
                                              branch=BRANCH,
                                              committer_name=COMMITTER_NAME,
                                              committer_email=COMMITTER_EMAIL)
    gitee_handler.refresh_release_files(RELEASE_FOLDER, release_files)


if __name__ == "__main__":
    handling("", "")

