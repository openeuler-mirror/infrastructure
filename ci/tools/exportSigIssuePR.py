#!/usr/bin/python3
import json
import urllib.request 

PER_PAGE = 80

def getAuthors(page):
    url = "https://ipb.osinfra.cn/pulls?repo=openeuler/docs&per_page=80&page="
#    url = "https://ipb.osinfra.cn/issues?repo=openeuler/docs&per_page=80&page="
    url = url + str(page)
    response = urllib.request.urlopen(url)
    ejson = json.loads(response.read())
    data = ejson["data"]
    lens = len(data)
    authors = []
    for idx in range(lens):
        info = data[idx]
        author = info["author"]
        authors.append(author)
#        print(author)
    return authors

def getCount():
    url = "https://ipb.osinfra.cn/pulls?repo=openeuler/docs"
#    url = "https://ipb.osinfra.cn/issues?repo=openeuler/docs"
    response = urllib.request.urlopen(url)
    ejson = json.loads(response.read())
    cnt = ejson["total"]
    return cnt


def main():
    cnt = getCount()
    print(cnt)
    pages = cnt // PER_PAGE
    if 0 != cnt % PER_PAGE:
        pages = pages + 1
    textfile = open("txt.log", "w")
    print(pages)
    allAuthors = {} 
    for page in range(pages):
        authors = getAuthors(page + 1)
        for auth in authors:
            allAuthors[auth] = auth
            
    for committer in allAuthors.values():
        print(committer)
        textfile.write(committer)
        textfile.write(",\n")
    
    textfile.close()
    return

if __name__=="__main__":
    main()

