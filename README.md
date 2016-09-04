There's some ugly code, and no guarantees here at all.

Clone this repo as a subdirectory of an empty directory. Then, run quickstart.sh from within this repo.

Example of neat things it can do right now (it's a work in progress, and not friendly yet):

```sh
$ source env/bin/activate
$ bash grab.sh
--2016-09-04 07:50:18--  http://www.dmr-marc.net/cgi-bin/trbo-database/datadump.cgi?table=repeaters&format=json
Resolving www.dmr-marc.net (www.dmr-marc.net)... 109.69.110.230, 44.103.0.25
Connecting to www.dmr-marc.net (www.dmr-marc.net)|109.69.110.230|:80... connected.
HTTP request sent, awaiting response... 200 OK
Length: 1062081 (1.0M) [text/html]
Saving to: ‘datadump.json’

datadump.json               100%[==========================================>]   1.01M   786KB/s    in 1.3s    

2016-09-04 07:50:20 (786 KB/s) - ‘datadump.json’ saved [1062081/1062081]

$ ./dmr-programmer
[DMRsh] $ select md380
[DMRsh][md380] $ sync in
Done.
[DMRsh][md380] $ to_csv myfile
radio to_csv
[DMRsh][md380] $ edit myfile
# Your edit will launch to edit three files - contacts, memories, and rxgroups.
# When you save and quit from your editor, dmr-programmer will be running again.
# In this session, I added contacts and rxgroups to use NEDECN.

[DMRsh][md380] $ eval self.model.add_memories( self.dmrdump.rxgroups_and_repeaters_to_memories( self.model, ("NEDECN_1","NEDECN_2"), self.dmrdump.find(ipsc_network="NE-TRBO") ) )
# lots of output, or a failure.

# NEDECN_1 is an rxgroup for the NEDECN talkgroups that are commonly on timeslot 1, NEDECN_2 is similar for TS2.
# assuming it works, there are now 47 more repeaters from the NE-TRBO network programmed than previously, 
#  each with two memories (one for each timeslot), 
#   each of which uses the first contact of the specified rxgroup as the txgroup.

[DMRsh][md380] $ sync out
```

It's a work in progress. More to come.
