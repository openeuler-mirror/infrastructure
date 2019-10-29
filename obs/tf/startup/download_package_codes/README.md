# NOTE
prepare.py file used to generate the command script which will be used to clone the whole projects,
please clone the source projects in the folder `/srv/cache/obs/tar_scm/repo/next/openEuler`
```$xslt
python prepare.py
chmod +x download.sh
cp download.sh /srv/cache/obs/tar_scm/repo/next/openEuler/download.sh
cd /srv/cache/obs/tar_scm/repo/next/openEuler
nohup ./download.sh > result.log 2>&1 & 
```
