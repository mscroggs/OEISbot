import praw
import re
import urllib
import json
from praw.objects import MoreComments

import sys
test = False
if len(sys.argv)>1 and sys.argv[1]=="test":
    test=True
    print("TEST MODE")


def save_list(seen, _id):
    print(seen)
    with open("/home/pi/OEISbot/seen/"+_id,"w") as f:
        return json.dump(seen, f)

def open_list(_id):
    try:
        with open("/home/pi/OEISbot/seen/"+_id) as f:
            return json.load(f)
    except:
        return []

class FoundOne(BaseException):
    pass

def look_for_A(id_, text, url, comment):
    seen = open_list(id_)
    re_s = re.findall("A([0-9]{6})",text)
    re_s += re.findall("oeis\.org/A([0-9]{6})",url)
    if test:
        print(re_s)
    post_me = []
    for seq_n in re_s:
        if seq_n not in seen:
            post_me.append(markup(seq_n))
            seen.append(seq_n)
    if len(post_me)>0:
        post_me.append(me())
        comment(joiner().join(post_me))
        save_list(seen, id_)
        raise FoundOne

def look_for_ls(id_, text, url, comment):
    seen = open_list(id_)
    if test:
        print(text)
    re_s = re.findall("([0-9]+\, *(?:[0-9]+\, *)+[0-9]+)",text)
    if test:
        print(re_s)
    if len(re_s)>0 and re_s[0] not in seen:
        seen.append(re_s[0])
        first10, total = load_search(re_s[0])
        intro = "Your sequence ("+re_s[0]+") may be one of the following OEIS sequences."
        if total > 4:
            intro += " Or, it may be one of the "+str(total-4)+" other sequences listed [here](http://oeis.org/search?q="+re_s[0]+")."
        post_me = [intro]
        if test:
            print(first10)
        for seq_n in first10[:4]:
            post_me.append(markup(seq_n))
        post_me.append(me())
        comment(joiner().join(post_me))
        save_list(seen, id_)
        raise FoundOne
            

def load_search(terms):
    src=urllib.urlopen("http://oeis.org/search?fmt=data&q="+terms).read()
    ls = re.findall("href=(?:'|\")/A([0-9]{6})(?:'|\")",src)
    tot = int(re.findall("of ([0-9]+) results found",src)[0])
    return ls, tot

r = praw.Reddit('OEIS link and description poster by /u/mscroggs.')

access_i = r.refresh_access_information(refresh_token=r.refresh_token)
r.set_access_credentials(**access_i)

auth = r.get_me()

subs = ['TestingOEISbot','math','mathpuzzles','casualmath','theydidthemath',
        'learnmath','mathbooks','cheatatmathhomework','matheducation',
        'puremathematics','mathpics','mathriddles','askmath',
        'recreationalmath','OEIS']

if test:
    subs = ["TestingOEISbot"]

def markup(seq_n):
    pattern = re.compile("%N (.*?)<",re.DOTALL|re.M)
    desc=urllib.urlopen("http://oeis.org/A"+seq_n+"/internal").read()
    desc=pattern.findall(desc)[0].strip("\n")
    pattern = re.compile("%S (.*?)<",re.DOTALL|re.M)
    seq=urllib.urlopen("http://oeis.org/A"+seq_n+"/internal").read()
    seq=pattern.findall(seq)[0].strip("\n")
    new_com = "[A"+seq_n+"](http://oeis.org/A"+seq_n+"/): "
    new_com += desc+"\n\n"
    new_com += seq+"..."
    return new_com

def me():
    return "I am OEISbot. I was programmed by /u/mscroggs. [How I work](http://mscroggs.co.uk/blog/20)."

def joiner():
    return "\n\n- - - -\n\n"
try:
    for sub in subs:
        subreddit = r.get_subreddit(sub)
        for submission in subreddit.get_hot(limit = 10):
            if test:
                print(submission.title)
            look_for_A(submission.id, submission.title, submission.url, submission.add_comment)
            look_for_ls(submission.id, submission.title, submission.url, submission.add_comment)

            flat_comments = praw.helpers.flatten_tree(submission.comments)
            for comment in flat_comments:
                if not isinstance(comment,MoreComments) and comment.author is not None and comment.author.name != "OEISbot":
                    look_for_A(submission.id, re.sub("\[[^\]]*\]\([^\)*]\)","",comment.body), comment.body, comment.reply)
                    look_for_ls(submission.id, re.sub("\[[^\]]*\]\([^\)*]\)","",comment.body), comment.body, comment.reply)

except FoundOne:
    pass
