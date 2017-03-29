import praw
import re
import urllib
import json
from praw.objects import MoreComments

import os
test = False

if os.argv[1]=="test":
    test=True

print test

with open("/home/pi/OEISbot/seen") as f:
    seen = json.load(f)

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

for sub in subs:
    subreddit = r.get_subreddit(sub)
    for submission in subreddit.get_hot(limit = 10):
        try:
            seen[submission.id]
        except KeyError:
            seen[submission.id] = []
        re_s = re.findall("A([0-9]{6})",submission.title)
        re_s += re.findall("oeis\.org/A([0-9]{6})",submission.url)
        post_me = []
        for seq_n in re_s:
            if seq_n not in seen[submission.id]:
                post_me.append(markup(seq_n))
                seen[submission.id].append(seq_n)
        if len(post_me)>0:
            post_me.append(me())
            submission.add_comment(joiner().join(post_me))
            break

        re_s = re.findall("[^0-9, ] ?[0-9]+, ?([0-9]+, ?)+ ?[^0-9, ]",submission.title)
        if test:
            print re_s

        flat_comments = praw.helpers.flatten_tree(submission.comments)
        for comment in flat_comments:
            if not isinstance(comment,MoreComments) and comment.author is not None and comment.author.name != "OEISbot":
                re_s = re.findall("oeis\.org/A([0-9]{6})",comment.body)
                post_me = []
                for seq_n in re_s:
                    if seq_n not in seen[submission.id]:
                        post_me.append(markup(seq_n))
                        seen[submission.id].append(seq_n)
                no_links = re.sub("\[[^\]]*\]\([^\)*]\)","",comment.body)
                re_s = re.findall("oeis\.org/A([0-9]{6})",no_links)
                for seq_n in re_s:
                    if seq_n not in seen[submission.id]:
                        post_me.append(markup(seq_n))
                        seen[submission.id].append(seq_n)
                if len(post_me)>0:
                    post_me.append(me())
                    comment.reply(joiner().join(post_me))
                    break
        else:
            continue
        break
    else:
        continue
    break

with open("/home/pi/OEISbot/seen","w") as f:
    json.dump(seen,f)
