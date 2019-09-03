import obs
import os
import tempfile


# Found the image file according to the file name of release file,
# the image file SHOULD be in the same folder and the accept types
# are 1. image, 2. img
def build_image_url(file_name, endpoint, bucket):
    return "https://{0}.{1}:443/{2}".format(
        str(bucket).lower(),
        str(endpoint).lower(),
        str(file_name).lstrip("/").lower())


class ObsHandler:

    def __init__(self, ak, sk, endpoint, accept_types=[]):
        self.endpoint = endpoint
        self.accept_types = accept_types
        self.obsClient = obs.ObsClient(
            access_key_id=ak, secret_access_key=sk, server=endpoint)

    # Build image file from release file, the bucket is open for read,
    # therefore we just assemble it from template.
    def get_image_file(self, release_key, all_files):
        image_base = os.path.splitext(release_key)[0]
        possible_types = self.accept_types
        for t in possible_types:
            image_file = "{0}.{1}".format(image_base, t)
            image_key = filter(
                lambda ff: str(ff.get("key")).lower() == image_file.lower(),
                all_files)
            if len(image_key) != 0:
                return image_key[0].get("key")
        return ""

    def get_available_releases(self, bucket, folder):
        results = []
        try:
            resp = self.obsClient.listObjects(bucket, folder)
            if resp.status != 200:
                print(
                    "failed to get release files from obs bucket: {0}".format(
                        resp.body))
                return []
            # Only check the markdown files
            all_files = map(
                lambda ff: {"key": ff.key,
                            "lastModified": ff.lastModified}, resp.body.contents)

            r_files = filter(lambda ff: str(ff.get("key")).lower().endswith(
                ".md") or str(
                ff.get("key")).lower().endswith(".markdown"), all_files)

            # Prepare release file lists in the format of:
            # {
            #   //File's last modified time
            #   'lastModified': '2019/08/31 15:02:49',
            #   // release file's local path
            #   'local_path': 'this/is/local/path.md',
            #   // release file's identity in OBS bucket
            #   'key': 'openeuler/release_v1.0.0.md'
            #   // release files' file name
            #   'file_name': 'release_v1.0.0.md'
            #   // the image file's public url corresponding to release file
            #   'image_file': 'https://{bucket}.{endpoint}:443/{file_key}'
            # }
            temp_folder = tempfile.mkdtemp(suffix="openeuler")
            for f in r_files:
                f["file_name"] = str.split(f.get("key"), "/")[-1]
                image_file = self.get_image_file(f.get("key"), all_files)
                if image_file == "":
                    print("could not found image file for "
                          "release {0}. skipping.".format(f.get("key")))
                    continue
                f["image_file"] = build_image_url(
                    image_file, self.endpoint, bucket)
                l_file = os.path.join(temp_folder, f["file_name"])
                self.obsClient.getObject(bucket, f.get("key"),
                                         downloadPath=l_file)
                f["local_path"] = l_file
                results.append(f)
        except Exception as e:
            print("failed to prepare release files from OBS bucket {0}".format(e))
            return []
        else:
            return results
