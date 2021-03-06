import numpy as np

from openmdao.main.api import Component
from openmdao.main.datatypes.api import Int, Float, Array


class Thrust(Component):

    # inputs
    Ns    = Int(iotype='in',   desc='number of elements')
    yN    = Array(iotype='in', desc='node locations')
    dr    = Array(iotype='in', desc='length of each element')
    r     = Array(iotype='in', desc='radial location of each element')
    ycmax = Float(iotype='in')
    Cl    = Array(iotype='in', desc='lift coefficient distribution')
    c     = Array(iotype='in', desc='chord distribution')
    rho   = Float(iotype='in', desc='air density')
    Omega = Float(iotype='in', desc='rotor angular velocity')

    # outputs
    dT = Array(iotype='out', desc='Thrust')
    chordFrac = Array(iotype='out')

    def execute(self):
        self.chordFrac = np.ones((self.Ns, 1))
        self.dT = np.zeros((self.Ns, 1))

        # Compute multiplyer for partial element
        for index, element in enumerate(self.yN):
            if element < self.ycmax:
                sTrans = index  # determine transitional partial element
        self.chordFrac[sTrans] = self.yN[sTrans+1] - self.ycmax  \
                               / (self.yN[sTrans+1] - self.yN[sTrans])

        # Compute thrust assuming small angles
        for s in range(self.Ns):
            self.dT[s] = self.chordFrac[s] * 0.5 * self.rho \
                       * (self.Omega * self.r[s])**2        \
                       * self.Cl[s] * self.c[s] * self.dr[s]


class ActuatorDiskInducedVelocity(Component):
    '''
    Compute induced velocity using annual-ring actuator disk theory
    '''

    # inputs
    Ns  = Int(iotype='in',   desc='number of elements')
    r   = Array(iotype='in', desc='radial location of each element')
    dr  = Array(iotype='in', desc='length of each element')
    R   = Float(iotype='in', desc='rotor radius')
    b   = Int(iotype='in', desc='number of blades')
    h   = Float(iotype='in', desc='height of rotor')
    vc  = Float(iotype='in', desc='vertical velocity')
    rho = Float(iotype='in', desc='air density')
    dT  = Array(iotype='in', desc='thrust')

    # outputs
    vi  = Array(iotype='out', desc='induced downwash distribution')

    def execute(self):
        self.vi = np.zeros((self.Ns, 1))

        for s in range(self.Ns):
            sq = 0.25 * self.vc**2 + \
                 0.25 * self.b * self.dT[s] / (np.pi * self.rho * self.r[s] * self.dr[s])
            self.vi[s] = -0.5*self.vc + np.sqrt(sq)

        # Add ground effect Cheesemen & Benett's
        self.vi /= (1. + (self.R / self.h / 4.) ** 2)
