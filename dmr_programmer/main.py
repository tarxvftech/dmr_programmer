#!/usr/bin/env python

import os
import sys
import cmd
import glob
import shlex
import chirp.chirp_common as cc
import chirp.errors
from chirp.dmr import *
from drivers import md380

import errno    


def mkdir_p(path):
    """http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python"""
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


class DMRsh( cmd.Cmd ):
    """DMR shell"""
    radios = {"md380": md380.MD380Radio}
    current = None
    currentname = None
    model = None
    wd = None
    promptbase = " $ "
    firstlevel = "DMRsh"
    levels = [
            firstlevel
            ]
    prompt = " $ "
    intro = """
    This is the DMR Programmer shell. It supports tab completion some times (try the tab key).
    You can load data from a radio or file, edit some values, save them, and sync them back.

    Type "help" and press enter to get started.

    Typical workflow:
        select <model>
        load <radio image file> (or) sync in
        to_csv <somename>
        edit <somename>
            an editor launches to change the various files
            the specific editor is controlled by your EDITOR environment variable.
        from_csv <somename>
        save <radio image file> (and/or) sync out

    
    """
    # base = sys.argv[1]
    # image = base + ".img"
    def parse( self, line ):
        return line.split(' ')

    def do_edit( self, line ):
        args = self.parse( line )
        filename = args[0]
        try:
            os.system("$EDITOR %s*.csv"%(filename))
        except Exception as e:
            print(e)
        # def edit(filename):
            # os.system('%s %s' % (os.getenv('EDITOR'), filename))

    def complete_edit( self, text, line, begidx, endidx ):
        return self.complete_ls( text, line, begidx, endidx )
    
    def do_list( self, line ):
        print("Radios available: ")
        for k in self.radios.keys():
            print(k)

    def do_unselect( self, line ):
        """
            De-select a radio.
        """
        self.levels.remove(  self.currentname )
        self.current = None
        self.currentname = None
        self.model = None

    def do_select( self, line ):
        """
            Select a radio model to use.
            Usage:
                select <modelname>
            Example:
                select md380
        """
        args = self.parse(line)
        if len(args) < 1 or args[0] == '':
            return self.do_list(line)
        radioname = args[0]
        self.levels.insert(0, radioname)
        self.current = self.radios[ radioname ]
        self.currentname = radioname 

    def complete_select( self, text, line, begidx, endidx ):
        return [key for key in self.radios.keys() if text in key.lower()]

    def complete_sync( self, text, line, begidx, endidx ):
        return [key for key in ["in","off"] if text in key.lower()]

    def do_pdb( self, line ):
        import pdb; pdb.set_trace()
        
    def do_sync( self, line ):
        """
        Sync in the selected radio
            Usage:
                sync in
                sync out
        """
        args = self.parse(line)
        if self.current:
            try:
                if args[0] == "in":
                    if self.model == None:
                        self.model = self.current(None)
                    self.model.sync_in()
                elif args[0] == "out":
                    self.model.sync_out()
                else:
                    print("sync in or sync out")
            except chirp.errors.RadioError as e:
                print("You sure the radio is ready to sync? We couldn't talk to it.")
        else:
            print("Select a radio first")

    def do_load( self, line ):
        """
            Load a radio image file for the selected radio (*.img files).
            Do not provide the file extension.
            Usage:
                load <filename>
        """
        args = self.parse(line)
        if len(args) < 1 or args[0] == '':
            print("Requires a filename")
            return
        if self.current:
            self.model = self.current(None)
            self.model.load( args[0] )
        else:
            print("Select a radio first")

    def do_pwd( self, line ):
        print( os.getcwd() )

    def do_ls( self, line ):
        try:
            os.system("ls --color=auto %s" %(line) )
        except Exception as e:
            print(e)

    def do_l(self, line ):
        return self.do_ls(" -latr %s"%(line) )

    def complete_ls( self, text, line, begidx, endidx):
        return self.complete_cd( text, line, begidx, endidx )

    def complete_l( self, text, line, begidx, endidx):
        return self.complete_cd( text, line, begidx, endidx )

    def do_cd( self, line ):
        args = self.parse(line)
        if len(args) < 1 or args[0] is '':
            return
        try:
            os.chdir( args[0] )
        except Exception as e:
            print(e)

    def complete_cd( self, text, line, begidx, endidx ):
        ds = os.listdir('.')
        x = [d for d in ds if text in d.lower()]
        return x

    def complete_load( self, text, line, begidx, endidx):
        res = glob.glob( os.getcwd() + "/" + text +"*.img")
        res = [os.path.basename(name) for name in res]
        return res


    # National simplex
    # UHF    1) 441.0000   2) 446.5000   3) 446.0750   4-US & Europe 433.450
    # nedecn: 446.075
    # VHF     1) 145.7900   2) 145.5100
    # TG ID: 99  /  CC 1  /  TS 1  /  "Admit Criteria": Always  /  "In Call Criteria": TXI or Always

    # networks
    #   DMR-MARC, New england trbo?
    #   DCI, dmrx, brandmeister, PRN, 

    def base_parse(self, ctx):
        select_or_set = 0 #0 for select, >0 for set
        selectme = {}
        setme = {}
        bo = None
        lpt = None
        ltok = None
        for tok in ctx:
            pt, v = tok
            if pt == "BIG":
                bo = v
            elif pt == "WITH":
                select_or_set = 1

            if not select_or_set and lpt in ["ATTR","KEY"]: #selecting
                selectme[ ltok ] = v
            elif select_or_set and lpt in ["ATTR","KEY"]: #setting
                setme[ ltok ] = v
            ltok = v
            lpt = pt
        print( "SELECTME",selectme, "SETME",setme )
        return (bo, selectme, setme)


    def fn_add(self, ctx):
        bo, selectme, setme = self.base_parse(ctx)
        bos = getattr(self.model, self.myobjects[ bo ])
        # add( **setme)

    def fn_show(self, ctx):
        bo, selectme, setme = self.base_parse(ctx)
        bos = getattr(self.model, self.myobjects[ bo ])
        if len(selectme.keys()) > 0:
            print( selectme)
            these = bos.find( **selectme )
        else:
            these = bos
        for each in these:
            print(each)



    def fn_configure(self, ctx):
        bo, selectme, setme = self.base_parse(ctx)
        bos = getattr(self.model, self.myobjects[ bo ])
        # these = bos.find( **selectme )
        # these.set( **setme )
        # these.set( selectme, setme )
        bos.set( selectme, setme)

    def fn_delete(self, ctx):
        bo, selectme, setme = self.base_parse(ctx)
        # bos = getattr(self.model, self.myobjects[ bo ])
        # these = bos.find( **selectme )
        # delete these
        print(these)

    objects = {
            "contact":DMRContact,
            "rxgroup":DMRRXGroup,
            "contacts":DMRContactList,
            "rxgroups":DMRRXGroupList,
            "channel":DMRMemory,
            "bank":cc.MTOBankModel
            }
    myobjects = {
            "contact":"contacts",
            "rxgroup":"rxgroups",
            "contacts":"contacts",
            "rxgroups":"rxgroups",
            "channel":"memories", #?
            "bank": "get_bank_model" #?
            }
                # "contacts","rxgroups","channels","banks"]
    actions = {
            "add": fn_add,
            "show":fn_show,
            "configure": fn_configure,
            "delete": fn_delete,
            }
    def default( self,line ):
        args = self.parse(line)

        def fieldlookup(oname, tok):
            if not oname:
                return False
            # print("fieldlookup", oname, tok)
            test = self.objects[ oname ]()

            try:
                if hasattr(test, tok) or hasattr(test,"_"+tok):
                    return "ATTR"
            except:
                pass
            try:
                if tok in test or "_"+tok in test:
                    return "KEY"
            except:
                pass

            # print(test, tok)
            return False

        if args[0] in self.actions:
            lex = shlex.shlex(line, posix=True)
            ctx = []
            actions = self.actions.keys()
            bigobjects = self.objects.keys()
            lasttok = None
            lastattr = None
            bo = None
            for tok in lex:
                t = fieldlookup(bo, tok)
                if tok.lower() == "with":
                    tok = ("WITH", tok)
                elif tok in actions:
                    tok = ("ACT", tok)
                elif tok in bigobjects:
                    bo = tok
                    tok = ("BIG", tok)
                elif bo in bigobjects and t:
                    tok = ( t, tok)
                    lastattr = tok
                elif lasttok[0] in ["ATTR","KEY"]:
                    tok = ("VALUE", tok)
                else:
                    tok = ("UNK", tok)
                print(tok)
                ctx.append( tok )
                lasttok = tok

            if not self.model:
                print("Select a radio and load an image first.")
                return
            else:
                if ctx[0][0] == "ACT":
                    self.actions[ ctx[0][1] ](self, ctx)
                else:
                    print("Not sure what to do: ")
                    print( ctx )
        else:
            try:
                os.system(line)
            except Exception as e:
                print(e)

        #
        # banks centered around sending to a talkgroup across multiple repeaters in an area
        #       a single talkgroup with related talkgroups to listen to (regional, state, etc)
        #       across multiple close-by repeaters
        #
        # banks centered around specific repeaters (talk to tg9, listen to selected regional talkgroups)
        #       
        # hybrid, one channel for each TS of each repeater, so 8 repeaters per zone, local zone only and regional zone only depending on TS layout?
                # add channels repeater location Massachusetts mode DMR band UHF name dmr_ma_uhf
        #

        """
        syntax target (from clean slate):
            (import repeaters database)
            edit bank 1 name "mike was here" or add bank name "mike also here" (note no index)
            edit bank "mike was here" style [ manual, repeater, talkgroup, hybrid]
            for manual:
                nothing special, everything done manually with some help
            for hybrid:
                build off manual, choose a single talkgroup per timeslot:
                    e.g. TS1 is always 3172, TS2 is always 3125
                and then add 8 repeaters with that setup

            for repeater:
                add channel[s] "w2fbi" repeater callsign W2FBI
                    make a "base" dmrmemory that has the details for this single repeater
                    tag it with the text after "channel[s]" as the identifier
                edit c "w2fbi" ts 1 tg 3172 310 311 3
                                where the first one is the "txgroup" and the rest go in the rxgroup
                edit c "w2fbi" ts 2 tg 3125 9 8

                edit bank "mike was here" add channels "w2fbi"

            for talkgroup:
                add channel[s] "ma_dmr" repeaters location Massachusetts, United States 
                edit channels "ma_dmr" add talkgroup 3125 on timeslot 2
                add bank "ma_dmr" with channels "ma_dmr"
        """

                
    def completedefault( self, text, line, begidx, endidx ):
        return []




    def do_to_csv( self, line ):
        """
            Dump current model to several component csv files, all with base filename provided.
            Usage:
                to_csv <fileprefix>
            Example:
                to_csv md380-work
        """
        if not self.model or not self.current:
            print("Select a radio, and instantiate a radio image (load, or sync in) first.")
            return
        args = self.parse(line)
        self.model.to_csv( args[0] )



    def do_from_csv( self, line ):
        """
             Refresh current model with data from several csv files, as from to_csv.
             Usage:
                from_csv <fileprefix>
            Example:
                from_csv md380-work
        """

        if not self.model or not self.current:
            print("Select a radio, and instantiate a radio image (load, or sync in) first.")
            return
        args = self.parse(line)
        print("from_csv is currently breaking frequencies, so keep that in mind")
        self.model.from_csv( args[0] )

    def do_save( self, line ):
        """
            Save a radio memory file, do not provide an extension, it will be added automatically.
            Usage:
                save <filename>
            Example:
                save tytera
                    Will create "tytera.img" from the loaded radio image.
        """
        if self.current:
            args = self.parse(line)
            self.model.save( args[0] +".img" )
        else:
            print("Select a radio first")

    def do_eval( self, line ):
        try:
            print(eval(line))
        except Exception as e:
            print(e)

    def do_EOF( self, arg ):
        return True
    def do_exit( self, line):
        sys.exit(0)

    def updateprompt( self ):
        self.prompt = self.promptbase
        if len(self.levels) > 3:
            for l in self.levels[0:3]:
                self.prompt = "["+l+"]" + self.prompt
        else:
            for l in self.levels:
                self.prompt = "["+l+"]" + self.prompt

    #later: add location support for repeater adding
    # http://stackoverflow.com/questions/9532369/where-can-i-find-city-town-location-data-for-location-based-searching
    def do_test( self, line ):
        self.dmrdump = DMRDump()

        for r in self.dmrdump.find(country="United States",state="Massachusetts"):
            print(r['callsign'])
            # mem = repeater_to_memory( r)

        print( self.dmrdump.fieldcount("ipsc_network", country="United States", state="Massachusetts") )
        print( self.dmrdump.fieldcount("state", country="United States") )
        print( self.dmrdump.fieldcount("country" ) )

    def precmd( self, line):
        self.updateprompt()
        return line

    def postcmd( self, stop, line):
        self.updateprompt()
        return stop

    def preloop( self ):
        self.updateprompt()

    def emptyline( self ):
        return


def main(argv):
    d = DMRsh()
    commands = ' '.join(argv[1:]).split(',')
    for c in commands:
        print("> "+ c.strip() )
        d.onecmd( c.strip() )
    d.cmdloop()

    # banks = mb.get_mappings()
    # for b in banks:
        # print(b)
    # print("\n\nCONTACTS:")
    # idx = 0
    # for c in m._memobj.contacts:
        # n = md380.utftoasc( str(c.name ))
        # if n is not '':
            # print("%d\t%s: \t\t%d\t%x"%(idx,n,c.callid, c.flags))
        # idx+=1
    # print("\n\nRX GROUPS")
    # idx = 0
    # for c in m._memobj.rxgrouplist:
        # n = md380.utftoasc( str(c.name ))
        # if n is not '':
            # print("%d:\t%s"%(idx,n))
            # for i in c.contactid:
                # print("\t%d\t%s"% (i, m._memobj.contacts[i].name))
        # idx+=1
    # import pdb; pdb.set_trace()
