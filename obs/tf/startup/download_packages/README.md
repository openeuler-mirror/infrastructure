# NOTE
Please put both 'package_lists' and 'prepare.py' files into the destination folder
you want to download before executing command, and then generate the execute sh file
via command:
```$xslt
python prepare.py
```
this py file will generate a new executable file 'download.sh', since it will take a
long time to finish you can execute the `nohup` command:
```$xslt
chmod +x download.sh
nohup ./download.sh > result.log 2>&1 &
```  
when all packages has been downloaded, we need refresh the project via command (assume we
create the project named Fedora-29-1.2)
```$xslt
cd /srv/obs/build/Fedora-29-1.2/standard/aarch64
chown -R obsrun:obsrun .
obs_admin --rescan-repository Fedora-29-1.2 standard aarch64
```
