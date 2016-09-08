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


# IDEAS:
    # Talkgroup centric banks
    #   a bunch of repeaters all txgroup'd for one tg
    # repeater centric banks
    #   a bunch of talkgroups on a single repeater
    # hybrid banks
    #   a bunch of repeaters in a bank, with two memories each, a bunch of rx tgs and a single tx tg for each timeslot
    #       
    #   To fully automate, TGs need to have a consistently parsable format. Doesn't exist right now.
    #
    #   later: add location support for repeater adding
    #       http://stackoverflow.com/questions/9532369/where-can-i-find-city-town-location-data-for-location-based-searching

def mkdir_p(path):
    """http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python"""
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


class DMRsh( cmd.Cmd, object ):
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
    def __init__(self):
        super( DMRsh, self).__init__()
        self.dmrdump = DMRDump()
        self.objects = {
                "contact":["name","callid","flags"],
                "rxgroup":["name","cidxs"],
                "contacts":["name","callid","flags"],
                "rxgroups":["name","cidxs"],
                "channel":[p for p in dir(DMRMemory) if isinstance(getattr(DMRMemory,p), property)],
                "bank":cc.MTOBankModel,
                "repeater":["callsign","country","state","city","locator",
                            "frequency","color_code","offset","ipsc_network",
                            ],
                "repeaters":["callsign","country","state","city","locator",
                            "frequency","color_code","offset","ipsc_network",
                            ],
                "settings":["dmrid"],
                }
        self.myobjects = {
                "contact":"contacts",
                "rxgroup":"rxgroups",
                "contacts":"contacts",
                "rxgroups":"rxgroups",
                "channel":"memories", #?
                "bank": "get_bank_model", #?
                "repeater": "dmrdump",
                "repeaters": "dmrdump",
                "settings":None, #TODO
                }
                    # "contacts","rxgroups","channels","banks"]
        self.actions = {
                "add": self.fn_add,
                "show":self.fn_show,
                "configure": self.fn_configure,
                "delete": self.fn_delete,
                "count": self.fn_count,
                "fieldcount": self.fn_fieldcount,
                }

    def parse( self, line ):
        return line.split(' ')

    def do_edit( self, line ):
        args = self.parse( line )
        filename = args[0]
        try:
            os.system("$EDITOR %s_*.csv"%(filename))
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

    def do_dmrid( self, line):
        args = self.parse( line )
        #temporary
        if len(args) > 0 and args[0] != '':
            self.model._memobj.general.dmrid.set_value( int( args[0]))
            print("Set DMR ID to: ", self.model._memobj.general.dmrid)
        else:
            print("DMR ID is: ", self.model._memobj.general.dmrid)


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
        # print( "SELECTME",selectme, "SETME",setme )
        return (bo, selectme, setme)


    def fn_add(self, ctx):
        bo, selectme, setme = self.base_parse(ctx)
        # bos = getattr(self.model, self.myobjects[ bo ])
        print(bo, selectme)
        if bo.lower() in ["repeater","repeaters"]:
            self.model.add_memories_from_repeater( self.dmrdump, **selectme)

    def fn_fetch(self, ctx):
        bo, selectme, setme = self.base_parse(ctx)
        try:
            bos = getattr(self.model, self.myobjects[ bo ])
        except AttributeError as e:
            pass
        try:
            bos = getattr(self, self.myobjects[ bo ])
        except AttributeError as e:
            pass

        if len(selectme.keys()) > 0:
            # print( selectme)
            these = bos.find( **selectme )
        else:
            these = bos
        return these

    def fn_count( self, ctx):
        these = self.fn_fetch(ctx)
        print("Rows: %d"%len(these))

    def fn_fieldcount( self, ctx):
        bo, selectme, setme = self.base_parse(ctx)
        bos = getattr(self, self.myobjects[ bo ]) #only meant for repeaters, TODO, will except if used on other things
        counts = bos.fieldcount( *setme.keys(), **selectme)

        print("For filter: %s"%( str(selectme)) )
        for field,fcounts in counts.items():
            print(field)
            print("\tCount\tValue")
            for n,c in sorted(fcounts.items(), key=lambda x: x[1]):
                print("\t%d\t%s"%( c, n))

    def fn_show( self, ctx):
        these = self.fn_fetch(ctx)
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

    def default( self,line ):
        args = self.parse(line)

        def fieldlookup(oname, tok):
            if not oname or oname.strip().lower() not in self.objects:
                return False
            o = self.objects[ oname ]

            if tok in o or "_"+tok in o:
                return True

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
                t = "ATTR" if fieldlookup(bo, tok) else False
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

                # print(tok)
                ctx.append( tok )
                lasttok = tok

            if not self.model:
                print("Select a radio and load an image first.")
                return
            else:
                if ctx[0][0] == "ACT":
                    self.actions[ ctx[0][1] ]( ctx )
                else:
                    print("Not sure what to do: ")
                    print( ctx )
        else:
            try:
                os.system(line)
            except Exception as e:
                print(e)

                
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
        print(eval(line))
        # try:
            # print(eval(line))
        # except Exception as e:
            # print(e)

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


    def precmd( self, line):
        self.updateprompt()
        return line

    def postcmd( self, stop, line):
        self.updateprompt()
        return stop

    def preloop( self ):
        try:
            fh = open("my.script","r")
            for line in fh:
                if not line.strip().startswith('#'):
                    self.onecmd( line.strip() )
        except:
            pass

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
