

from lantz import Feat

from lantz.messagebased import MessageBasedDriver



class AFG3021b(MessageBasedDriver):


    @classmethod
    def from_usbtmc(self, serial_number=None, name=None, **kwargs):

        return super().from_usbtmc(serial_number, '0x0699', '0x0346', name=name, **kwargs)

    @Feat()
    def idn(self):
        return inst.query('*IDN?')


if __name__ == '__main__':
    import argparse
    import lantz.log

    parser = argparse.ArgumentParser(description='Test Kentech HRI')
    parser.add_argument('-i', '--interactive', action='store_true',
                        default=False, help='Show interactive GUI')
    parser.add_argument('-p', '--port', type=str, default='17',
                        help='Serial port to connect to')

    args = parser.parse_args()
    lantz.log.log_to_socket(lantz.log.DEBUG)

    with AFG3021b('USB0::0x0699::0x0346::C033250::INSTR') as inst:
        print(inst.idn)

    with AFG3021b.from_hostname() as inst:
        print(inst.idn)

    with AFG3021b.from_usbtmc(serial_number='C033250') as inst:
        print(inst.idn)
