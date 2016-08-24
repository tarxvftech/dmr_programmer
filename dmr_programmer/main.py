#!/usr/bin/env python

import os
import sys
import cmd
import glob
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
    This is the DMR Programmer shell. It supports tab completion most times.
    You can load data from a radio or file, edit the values, save them, and sync them back.

    Type "help" and press enter to get started.

    Typical workflow:
        select <model>
        load <radio image file> (or) sync in
        to_csv <somename>
        edit somename*.csv
            an editor launches to change the various files
        save <radio image file> (and/or) sync out

    
    """
    # base = sys.argv[1]
    # image = base + ".img"
    def parse( self, line ):
        return line.split(' ')

    def do_edit( self, line ):
        try:
            os.system("$EDITOR %s"%(line))
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

    def do_configure( self, line ):
        args = self.parse(line)
        #possible first args:
        #   contact
        #   rxgroup
        #   channel
        #   bank
    def do_add( self, line ):
        args = self.parse(line)
        #possible first args:
        #   contact
        #   rxgroup
        #   channel
        #   bank


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

    def do_rm( self, line ):
        try:
            os.system("rm %s"%(line))
        except Exception as e:
            print(e)

    def do_eval( self, line ):
        try:
            print(eval(line))
        except Exception as e:
            print(e)

    def do_EOF( self, arg ):
        return True

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
