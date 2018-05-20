import json
import sys

"""
This script can be used to import a text file of socials into Undermountain.
No warranty is provided, YMMV. It was created by Meathe of Waterdeep.
The general shape of the socials.are file for purposes of this importer is:

#SOCIALS

aargh
AAAAAARRRRRRGGGGGGHHHHHH!!!!!!
$n throws back $s head and howls in profound frustration!
You scream your frustration and grab for $S throat with both hands!
$n howls in frustration and leaps for $N, trying to throttle $M!
$n grabs for your throat with two hands, howling in frustration!
$n grabs for your throat with two hands, howling in frustration!
You get even MORE frustrated when you can't find anyone to throttle!
$n screams in frustration at $e's own stupidity.

accept
You accept the profferred apology graciously.
$n graciously accepts the profferred apology.
You graciously accept $N's apology.
$n graciously accepts $N's apology.  Whew!
$n graciously accepts your apology.  Did you even offer it??
You look for someone to accept an apology from, but resort to feeling sorry for yourself instead.
You accept your own apology.  Strange, you never remembered doing anything wrong??
$n rather reluctantly accepts his own apology.

Adapt the file as necessary to your needs.

sample_social.are provided as a sample file to import.
"""

class Social:
    def __init__(self, name, a, b, c, d, e, f, g):
        self.name = name
        self.actor_no_arg = a
        self.others_no_arg = b
        self.actor_found_target = c
        self.others_found = d
        self.target_found = e
        self.actor_auto = f
        self.others_auto = g

filename = sys.argv[-1]

if filename:
    with open(filename,'r') as f:
        socs=f.readlines()
        count = 2
        socList=[]

    while count + 7 < len(socs):
        name = socs[count].rstrip()
        count+=1
        a = socs[count].rstrip()
        count+=1
        b = socs[count].rstrip()
        count+=1
        c = socs[count].rstrip()
        count+=1
        d = socs[count].rstrip()
        count+=1
        e = socs[count].rstrip()
        count+=1
        f = socs[count].rstrip()
        count += 2 # skip over second to last line in block.
        g = socs[count].rstrip()
        count += 1
        count += 1
        soc=Social(name, a, b, c, d, e, f, g)
        socList.append(soc)

    print("{} socials were found.".format(len(socList)))

    for s in socList:
        fname = s.name + ".json"
        sf = open(fname, "w")
        sf.write(json.dumps(s.__dict__, sort_keys=False, indent = 4, separators = (',', ':')))
        sf.close()
        print("{} file written.".format(fname))

else:
    print("Import failed: file not supplied.")