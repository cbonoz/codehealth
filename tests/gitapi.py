import base64
import requests
import difflib
from pprint import pprint
BASE = "https://api.github.com" 

#your random hash here
random_hash = 
random_hash = random_hash.replace('-','')

user = "cbonoz"
d = difflib.Differ()
"""
Define custom request routes
"""

def add_url_params(url, params):
    return url + "?" + "&".join([p[0]+"="+p[1] for p in params])

def github_getresult(url, params=None, content_type=None):
    print("getresult: " + str(url))
    headers = {'Content-type': content_type or 'application/json'}
    r = requests.get(url, auth=(user, random_hash),  params=params, headers=headers)
    return r.json()

def get_commits(repo):
    return github_getresult(BASE+"/repos/"+user+"/"+repo+"/commits")

    # /repos/:owner/:repo/compare/:base...:head
def compare_commits(repo, path, commit1, commit2):
    # url = BASE + "/repos/" + user + "/" + repo + "/compare/" + commit1 + "..." + commit2
    # content_type= "application/vnd.github.VERSION.diff"
    content1 = get_commit_text(repo,path,commit1)
    content2 = get_commit_text(repo,path,commit2)

    result = list(d.compare(content1, content2))
    pprint(result)
    return result
    




def get_content(repo, path, commit=None):
    url = BASE+"/repos/"+user+"/"+repo+"/contents/"+path
    if commit is not None:
        url = add_url_params(url, [("ref",commit)])
        # url = add_url_params(url, params)
        
    return github_getresult(url)

"""
Github Information Methods
"""
def get_commit_text(repo, path, commit=None):
    r = get_content(repo, path, commit)
    try:
        content = r["content"]
        return base64.b64decode(content)
    except Exception as e:
        print(e)
        return None




"""
Main Method
"""

def main():
    repo_name = "cs230project"
    r = get_commits(repo_name)
    path = "README.md"#"website/app/index.html"

    commits = [x["sha"] for x in r]

    # print(get_commit_text(repo_name, path))
    diff = compare_commits(repo_name, path, commits[5],commits[len(commits)-1])




if __name__ == "__main__":
    main()