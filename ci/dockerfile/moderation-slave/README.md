## Moderation
moderation.py is a script to moderate text and image of a Pull Request with parameters. If this is the first run the script, type `python moderation.py -h` or `python moderation.py --help` to get help information as follows.

```
usage: moderation.py [-h] -o OWNER -r REPO -n NUMBER
                     [-s [SUFFIX [SUFFIX ...]]] [-tc [TC [TC ...]]]
                     [-ic [IC [IC ...]]] [-iac [IAC [IAC ...]]]

The script is used to moderate the text and image of Pull Request.To run the
script, you must provide owner(-o),repo(-r) and number(-n) of a pull request.
You can also declare a list which limit the types of files you need to
moderate by suffix(-s).

optional arguments:
  -h, --help            show this help message and exit
  -o OWNER, --owner OWNER
                        owner of pull request
  -r REPO, --repo REPO  repo of pull request
  -n NUMBER, --number NUMBER
                        number of pull request
  -s [SUFFIX [SUFFIX ...]], --suffix [SUFFIX [SUFFIX ...]]
                        limit the suffix of files to moderate
  -tc [TC [TC ...]]     limit text categories
  -ic [IC [IC ...]]     limit image categories
  -iac [IAC [IAC ...]]  limit image ad categories
```
### Required Parameters 
**owner**, **repo** and **number** of Pull Request are required parameters to start. You can start the script like, for example,  `python moderation.py -o openeuler -r community -n 1505`. 


### Optional Parameters 
**suffix**, **text categories**, **image categories**, **image ad categories** are optional.  These parameters are received in the form of a list. For example, if you want to limit the suffix to moderate , you can run `python moderation.py -o openeuler -r community -n 1505 -s txt md` , the script will moderate files which suffix is `txt` or `md` through the Pull Request. So `-tc` `-ic` `-iac` as the same.


### Enviroment Parameters 
The script will call the Huawei cloud interface to get iam-token.  **ACCOUNT_USERNAME**, **REGION**, **IAM_USERNAME**, **IAM_PASSWORD** are required. 
`ACCOUNT_USERNAME: username of your account`
`REGION: region where supply your service, e.g. cn-north-4`
`IAM_USERNAME: username of IAM`
`IAM_PASSWORD: password of IAM`

### Categories Config
categories.yaml supply text_suffixes, text_categories, image_suffiex, image_categories and image_ad_categories. You can customize them according to your personal needs.
