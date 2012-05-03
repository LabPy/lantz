from ni6733 import SinglePulse

nidaq = SinglePulse()
nidaq.run(0.0001, 0.0001)
nidaq.digiout(0, 0)
