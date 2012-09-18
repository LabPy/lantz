#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
    lantz-visa-shell
    ~~~~~~~~~~~~~~~~

    VISA shell for interactive testing.

    :copyright: (c) 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import sys
import cmd

from lantz import visa

class App(cmd.Cmd):
    """VISA shell for interactive testing.
    """

    intro = '\nWelcome to the VISA shell. Type help or ? to list commands.\n'
    prompt = '(visa) '

    use_rawinput = True

    def __init__(self, library_path=None):
        super().__init__()
        self.resource_manager = visa.ResourceManager(library_path)
        self.resources = []
        self.current = None

    def postcmd(self, stop, line):
        print()

    def do_list(self, args):
        """List all connected resources."""

        resources = self.resource_manager.list_resources_info('?*')

        self.resources = []
        for ndx, (resource, value) in enumerate(resources.items()):
            if not args:
                print('({:2d}) {}'.format(ndx, resource))
                if value.alias:
                    print('     alias: {}'.format(value.alias))

            self.resources.append((resource, value.alias or None))

    def do_open(self, args):
        """Open resource by number, resource name or alias: open 3"""

        if not args:
            print('A resource name must be specified.')
            return

        if self.current:
            print('You can only open one resource at a time. Please close the current one first.')
            return

        if args.isdigit():
            try:
                args = self.resources[int(args)][1]
            except IndexError:
                print('Not a valid resource number. Use the command "list".')
                return

        try:
            self.current = visa.VisaDriver(args)
            self.current.initialize()
            print('{} has been opened.\n'
                  'You can talk to the device using "send", "recv" or "query.\n'
                  '\\n is added and expected at the end of each message'.format(args))
            self.prompt = '(open) '
        except Exception as e:
            print(e)

    def complete_open(self, text, line, begidx, endidx):
        if not self.resources:
            self.do_list('do not print')
        return [item[0] for item in self.resources if item[0].startswith(text)] + \
               [item[1] for item in self.resources if item[1] and item[1].startswith(text)]

    def do_close(self, args):
        """Close resource in use."""

        if not self.current:
            print('There are no resources in use. Use the command "open".')
            return

        self.current.finalize()
        print('The resource has been closed.')
        self.current = None
        self.prompt = '(visa) '

    def do_query(self, args):
        """Query resource in use: query *IDN? """

        if not self.current:
            print('There are no resources in use. Use the command "open".')
            return

        try:
            print('Response: {}'.format(self.current.query(args)))
        except Exception as e:
            print(e)

    def do_recv(self, args):
        """Receive from the resource in use."""

        if not self.current:
            print('There are no resources in use. Use the command "open".')
            return

        try:
            print(self.current.recv())
        except Exception as e:
            print(e)

    def do_send(self, args):
        """Send to the resource in use: send *IDN? """

        if not self.current:
            print('There are no resources in use. Use the command "open".')
            return

        try:
            self.current.send(args)
        except Exception as e:
            print(e)

    def do_exit(self, arg):
        """Exit the shell session."""

        if self.current:
            self.current.finalize()
        del self.resource_manager

        print('Bye!\n')
        sys.exit(0)

    def do_EOF(self, arg):
        """.
        """
        return True


    # This has been patched to enable autocompletion on Mac OSX
    def cmdloop(self, intro=None):
        """Repeatedly issue a prompt, accept input, parse an initial prefix
        off the received input, and dispatch to action methods, passing them
        the remainder of the line as argument.
        """

        self.preloop()
        if self.use_rawinput and self.completekey:
            try:
                import readline
                self.old_completer = readline.get_completer()
                readline.set_completer(self.complete)

                if 'libedit' in readline.__doc__:
                    # readline linked to BSD libedit
                    if self.completekey == 'tab':
                        key = '^I'
                    else:
                        key = self.completekey
                    readline.parse_and_bind('bind %s rl_complete' % (key,))
                else:
                    # readline linked to the real readline
                    readline.parse_and_bind(self.completekey + ': complete')

            except ImportError:
                pass
        try:
            if intro is not None:
                self.intro = intro
            if self.intro:
                self.stdout.write(str(self.intro)+"\n")
            stop = None
            while not stop:
                if self.cmdqueue:
                    line = self.cmdqueue.pop(0)
                else:
                    if self.use_rawinput:
                        try:
                            line = input(self.prompt)
                        except EOFError:
                            line = 'EOF'
                    else:
                        self.stdout.write(self.prompt)
                        self.stdout.flush()
                        line = self.stdin.readline()
                        if not len(line):
                            line = 'EOF'
                        else:
                            line = line.rstrip('\r\n')
                line = self.precmd(line)
                stop = self.onecmd(line)
                stop = self.postcmd(stop, line)
            self.postloop()
        finally:
            if self.use_rawinput and self.completekey:
                try:
                    import readline
                    readline.set_completer(self.old_completer)
                except ImportError:
                    pass


if __name__ == '__main__':
    App().cmdloop()
