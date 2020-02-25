# Notice
This folder used to generate final yaml that can be used to setup the openeuler rpm repo service.

# Dockerfile
There are 2 images used for repo service and they are:
1. ``rsyncd/Dockerfile``: it contains the rsync server as well as sshd server, it's used to server as a rsync server.
3. ``Official nginx dockerfile 1.17.5``: it's used in the main deployment and will expose 443 port to our repo clients.

# Sync files from rsync server
Command will be like, note password is required:
```bash
sspass -p <password> rsync -avz --info=progress2 rsync://root@<address of rsync server>:873/openeuler .
```

# Generate yaml Command
```$xslt
helm template repo-chart  -f repo-chart/values.yaml --namespace <namespace> --name openeuler  > deployment.yaml
```

# Secrets required before deploy
the `website-secrets` is required before deploy the generated yaml, it will contain website certficate as well
as the private key. the command will be like:
```bash
kubectl create secret generic website-secrets --from-file=./fullchain.pem --from-file=./privkey.pem -n <namespace>
```
