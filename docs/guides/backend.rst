

Refactoring for reusability
---------------------------

Finally we will add a couple of lines to allow the user to define the host
and port number of the TCP function generator. We will also refactor the
code to extract the function that perform the actual frequency scan apart::

    import time

    def scan_frequency(inst, start, stop, step, wait):
        """Scan frequency in an instrument.

        :param start: Start frequency.
        :type start: Quantity
        :param stop: Stop frequency.
        :type stop: Quantity
        :param step: Step frequency.
        :type step: Quantity
        :param wait: Waiting time.
        :type wait: Quantity

        """
        in_secs = wait.to('seconds').magnitude
        current = start
        while current < stop:
            inst.frequency = current
            time.sleep(in_secs)
            current += step


    if __name__ == '__main__':
        import argparse

        from lantz import Q_

        from mydriver import LantzSignalGeneratorTCP

        parser = argparse.ArgumentParser()

        # Configure
        parser.add_argument('-H', '--host', type=str, default='localhost',
                            help='TCP hostname')
        parser.add_argument('-p', '--port', type=int, default=5678,
                            help='TCP port')

        parser.add_argument('start', type=float,
                            help='Start frequency [Hz]')
        parser.add_argument('stop', type=float,
                            help='Stop frequency [Hz]')
        parser.add_argument('step', type=float,
                            help='Step frequency [Hz]')
        parser.add_argument('wait', type=float,
                            help='Waiting time at each step [s]')

        args = parser.parse_args()

        Hz = Q_(1, 'Hz')
        sec = Q_(1, 'sec')

        def print_change(new, old):
            print('Changed from {} to {}'.format(old, new))

        with LantzSignalGeneratorTCP(args.host, args.port) as inst:
            print(inst.idn)

            inst.frequency_changed.connect(print_change)

            scan_frequency(inst, args.start * Hz, args.stop * Hz,
                           args.step * Hz, args.wait * sec)


The first change you will notice is that we have now used a Quantity for the
time. It might be meaningless as the script ask for the waiting time in
seconds and the function used to wait (`time.sleep`) expects the time in
seconds. But using a Quantity allows the caller of the function how the
waiting is implemented.

Also notice that we have removed the print statement from inside the function
to be able to reuse it in other applications. For example, we might want to use
it in a silent command line application or in a GUI application.
To know that the frequency has changed we have connected a reporting function
(`print_change`) to a signal (`frequency_changed`). Lantz will call the
function every time that the frequency changes. Every Feat has an associated
signal that can be accessed by appending `_changed` to the name.
