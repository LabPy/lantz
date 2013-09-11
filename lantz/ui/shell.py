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

class PatchedCmd(cmd.Cmd):

    use_rawinput = True

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


class LantzShell(PatchedCmd):
    """Base Shell shell for interactive testing.
    """

    intro = '\nWelcome to the Lantz shell. Type help or ? to list commands.\n'
    prompt = '(lantz) '

    def postcmd(self, stop, line):
        print()
        return stop

    def do_visa(self, args):
        """Open the visa shell."""

        VisaShell().cmdloop()

    def do_usbtmc(self, args):
        """Open resource by number, resource name or alias: open 3"""

        USBTMCShell().cmdloop()

    def do_exit(self, arg):
        """Exit the shell session."""

        print('Bye!\n')
        sys.exit(0)


class InterfaceShell(PatchedCmd):
    """Base Shell shell for interactive testing.
    """

    intro = '\nWelcome to the Lantz shell. Type help or ? to list commands.\n'
    prompt = '(lantz) '

    use_rawinput = True

    def __init__(self, library_path=None):
        super().__init__()
        self.default_prompt = self.prompt
        self.resources = []
        self.current = None

    def do_list(self, args):
        """List all connected resources."""
        raise NotImplemented

    def do_open(self, args):
        raise NotImplemented

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
        self.prompt = self.default_prompt

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

        return True

    def do_EOF(self, arg):
        """.
        """
        return True


class VisaShell(InterfaceShell):
    """VISA shell for interactive testing.
    """

    from lantz import visa

    intro = '\nWelcome to the VISA shell. Type help or ? to list commands.\n'
    prompt = '(visa) '


    def __init__(self, library_path=None):
        super().__init__()
        self.resource_manager = self.visa.ResourceManager(library_path)

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
            self.current = self.visa.VisaDriver(args)
            self.current.initialize()
            print('{} has been opened.\n'
                  'You can talk to the device using "send", "recv" or "query.\n'
                  '\\n is added and expected at the end of each message'.format(args))
            self.prompt = '(open) '
        except Exception as e:
            print(e)

    def do_exit(self, arg):
        super().do_exit(arg)
        del self.resource_manager
        return True


class USBTMCShell(InterfaceShell):
    """VISA shell for interactive testing.
    """

    from lantz.usb import DeviceInfo
    from lantz.drivers import usbtmc

    intro = '\nWelcome to the USBTMC shell. Type help or ? to list commands.\n'
    prompt = '(usbtmc) '

    def do_list(self, args):
        """List all connected resources."""

        self.resources = [str(self.DeviceInfo.from_device(dev))
                          for dev in self.usbtmc.find_tmc_devices()]
        for ndx, resource in enumerate(self.resources):
            print('({:2d}) {}'.format(ndx, resource))

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
                args = self.resources[int(args)]
            except IndexError:
                print('Not a valid resource number. Use the command "list".')
                return

        try:
            self.current = self.usbtmc.USBTMCDriver(serial_number=args.serial_number)
            self.current.initialize()
            print('{} has been opened.\n'
                  'You can talk to the device using "send", "recv" or "query.\n'
                  '\\n is added and expected at the end of each message'.format(args))
            self.prompt = '(open) '
        except Exception as e:
            print(e)


def main():
    LantzShell().cmdloop()

