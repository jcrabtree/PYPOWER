# Copyright (C) 1996-2011 Power System Engineering Research Center (PSERC)
# Copyright (C) 2011 Richard Lincoln
#
# PYPOWER is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# PYPOWER is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PYPOWER. If not, see <http://www.gnu.org/licenses/>.

"""Parses and initializes OPF input arguments.
"""

from sys import stderr

from numpy import array
from scipy.sparse import issparse

from ppoption import ppoption
from loadcase import loadcase


def opf_args(*args):
    """Parses and initializes OPF input arguments.

    Returns the full set of initialized OPF input arguments, filling in
    default values for missing arguments. See Examples below for the
    possible calling syntax options.

    Input arguments options::

        opf_args(ppc)
        opf_args(ppc, ppopt)
        opf_args(ppc, userfcn, ppopt)
        opf_args(ppc, A, l, u)
        opf_args(ppc, A, l, u, ppopt)
        opf_args(ppc, A, l, u, ppopt, N, fparm, H, Cw)
        opf_args(ppc, A, l, u, ppopt, N, fparm, H, Cw, z0, zl, zu)

        opf_args(baseMVA, bus, gen, branch, areas, gencost)
        opf_args(baseMVA, bus, gen, branch, areas, gencost, ppopt)
        opf_args(baseMVA, bus, gen, branch, areas, gencost, userfcn, ppopt)
        opf_args(baseMVA, bus, gen, branch, areas, gencost, A, l, u)
        opf_args(baseMVA, bus, gen, branch, areas, gencost, A, l, u, ppopt)
        opf_args(baseMVA, bus, gen, branch, areas, gencost, A, l, u, ...
                                    ppopt, N, fparm, H, Cw)
        opf_args(baseMVA, bus, gen, branch, areas, gencost, A, l, u, ...
                                    ppopt, N, fparm, H, Cw, z0, zl, zu)

    The data for the problem can be specified in one of three ways:
      1. a string (ppc) containing the file name of a PYPOWER case
      which defines the data matrices baseMVA, bus, gen, branch, and
      gencost (areas is not used at all, it is only included for
      backward compatibility of the API).
      2. a dict (ppc) containing the data matrices as fields.
      3. the individual data matrices themselves.

    The optional user parameters for user constraints (C{A, l, u}), user costs
    (C{N, fparm, H, Cw}), user variable initializer (z0), and user variable
    limits (C{zl, zu}) can also be specified as fields in a case dict,
    either passed in directly or defined in a case file referenced by name.

    When specified, C{A, l, u} represent additional linear constraints on the
    optimization variables, C{l <= A*[x z] <= u}. If the user specifies an C{A}
    matrix that has more columns than the number of "C{x}" (OPF) variables,
    then there are extra linearly constrained "C{z}" variables. For an
    explanation of the formulation used and instructions for forming the
    C{A} matrix, see the MATPOWER manual.

    A generalized cost on all variables can be applied if input arguments
    C{N}, C{fparm}, C{H} and C{Cw} are specified.  First, a linear
    transformation of the optimization variables is defined by means of
    C{r = N * [x z]}. Then, to each element of r a function is applied as
    encoded in the C{fparm} matrix (see Matpower manual). If the resulting
    vector is named C{w}, then C{H} and C{Cw} define a quadratic cost on
    C{w}: C{(1/2)*w'*H*w + Cw * w}.
    C{H} and C{N} should be sparse matrices and C{H} should also be symmetric.

    The optional C{ppopt} vector specifies PYPOWER options. See L{ppoption}
    for details and default values.

    @author: Ray Zimmerman (PSERC Cornell)
    @author: Carlos E. Murillo-Sanchez (PSERC Cornell & Universidad
    Autonoma de Manizales)
    @author: Richard Lincoln
    """
#    nargin = len([arg for arg in [baseMVA, bus, gen, branch, areas, gencost,
#                                  Au, lbu, ubu, ppopt, N, fparm, H, Cw,
#                                  z0, zl, zu] if arg is not None])
    nargin = len(args)

    userfcn = array([])
    ## passing filename or dict
    if isinstance(args[0], basestring) or isinstance(args[0], dict):
        # ----opf( baseMVA,     bus,   gen, branch, areas, gencost,    Au, lbu,  ubu, ppopt,  N, fparm, H, Cw, z0, zl, zu)
        # 12  opf(casefile,      Au,   lbu,    ubu, ppopt,       N, fparm,    H,  Cw,    z0, zl,    zu)
        # 9   opf(casefile,      Au,   lbu,    ubu, ppopt,       N, fparm,    H,  Cw)
        # 5   opf(casefile,      Au,   lbu,    ubu, ppopt)
        # 4   opf(casefile,      Au,   lbu,    ubu)
        # 3   opf(casefile, userfcn, ppopt)
        # 2   opf(casefile,   ppopt)
        # 1   opf(casefile)
        if nargin in [1, 2, 3, 4, 5, 9, 12]:
            casefile = args[0]
            if nargin == 12:
                baseMVA, bus, gen, branch, areas, gencost, Au, lbu,  ubu, ppopt,  N, fparm = args
                zu    = fparm
                zl    = N
                z0    = ppopt
                Cw    = ubu
                H     = lbu
                fparm = Au
                N     = gencost
                ppopt = areas
                ubu   = branch
                lbu   = gen
                Au    = bus
            elif nargin == 9:
                baseMVA, bus, gen, branch, areas, gencost, Au, lbu, ubu = args
                zu    = array([])
                zl    = array([])
                z0    = array([])
                Cw    = ubu
                H     = lbu
                fparm = Au
                N     = gencost
                ppopt = areas
                ubu   = branch
                lbu   = gen
                Au    = bus
            elif nargin == 5:
                baseMVA, bus, gen, branch, areas = args
                zu    = array([])
                zl    = array([])
                z0    = array([])
                Cw    = array([])
                H     = None
                fparm = array([])
                N     = None
                ppopt = areas
                ubu   = branch
                lbu   = gen
                Au    = bus
            elif nargin == 4:
                baseMVA, bus, gen, branch = args
                zu    = array([])
                zl    = array([])
                z0    = array([])
                Cw    = array([])
                H     = None
                fparm = array([])
                N     = None
                ppopt = ppoption()
                ubu   = branch
                lbu   = gen
                Au    = bus
            elif nargin == 3:
                baseMVA, bus, gen = args
                userfcn = bus
                zu    = array([])
                zl    = array([])
                z0    = array([])
                Cw    = array([])
                H     = None
                fparm = array([])
                N     = None
                ppopt = gen
                ubu   = array([])
                lbu   = array([])
                Au    = None
            elif nargin == 2:
                baseMVA, bus = args
                zu    = array([])
                zl    = array([])
                z0    = array([])
                Cw    = array([])
                H     = None
                fparm = array([])
                N     = None
                ppopt = bus
                ubu   = array([])
                lbu   = array([])
                Au    = None
            elif nargin == 1:
                zu    = array([])
                zl    = array([])
                z0    = array([])
                Cw    = array([])
                H     = None
                fparm = array([])
                N     = None
                ppopt = ppoption()
                ubu   = array([])
                lbu   = array([])
                Au    = None
        else:
            stderr.write('opf_args: Incorrect input arg order, number or type\n')

        ppc = loadcase(casefile)
        baseMVA, bus, gen, branch, gencost = \
            ppc['baseMVA'], ppc['bus'], ppc['gen'], ppc['branch'], ppc['gencost']
        if 'areas' in ppc:
            areas = ppc['areas']
        else:
            areas = array([])
        if Au is None and 'A' in ppc:
            Au, lbu, ubu = ppc["A"], ppc["l"], ppc["u"]
        if N is None and 'N' in ppc:  ## these two must go together
            N, Cw = ppc["N"], ppc["Cw"]
        if H is None and 'H' in ppc:  ## will default to zeros
            H = ppc["H"]
        if (fparm is None or len(fparm) == 0) and 'fparm' in ppc:  ## will default to [1 0 0 1]
            fparm = ppc["fparm"]
        if (z0 is None or len(z0) == 0) and 'z0' in ppc:
            z0 = ppc["z0"]
        if (zl is None or len(zl) == 0) and 'zl' in ppc:
            zl = ppc["zl"]
        if (zu is None or len(zu) == 0) and 'zu' in ppc:
            zu = ppc["zu"]
        if (userfcn is None or len(userfcn) == 0) and 'userfcn' in ppc:
            userfcn = ppc['userfcn']
    else: ## passing individual data matrices
        # ----opf(baseMVA, bus, gen, branch, areas, gencost,      Au, lbu, ubu, ppopt, N, fparm, H, Cw, z0, zl, zu)
        # 17  opf(baseMVA, bus, gen, branch, areas, gencost,      Au, lbu, ubu, ppopt, N, fparm, H, Cw, z0, zl, zu)
        # 14  opf(baseMVA, bus, gen, branch, areas, gencost,      Au, lbu, ubu, ppopt, N, fparm, H, Cw)
        # 10  opf(baseMVA, bus, gen, branch, areas, gencost,      Au, lbu, ubu, ppopt)
        # 9   opf(baseMVA, bus, gen, branch, areas, gencost,      Au, lbu, ubu)
        # 8   opf(baseMVA, bus, gen, branch, areas, gencost, userfcn, ppopt)
        # 7   opf(baseMVA, bus, gen, branch, areas, gencost, ppopt)
        # 6   opf(baseMVA, bus, gen, branch, areas, gencost)
        if nargin in [6, 7, 8, 9, 10, 14, 17]:
            if nargin == 17:
                baseMVA, bus, gen, branch, areas, gencost, Au, lbu, ubu, ppopt,  N, fparm, H, Cw, z0, zl, zu = args
            elif nargin == 14:
                baseMVA, bus, gen, branch, areas, gencost, Au, lbu, ubu, ppopt,  N, fparm, H, Cw = args
                zu = array([])
                zl = array([])
                z0 = array([])
            elif nargin == 10:
                baseMVA, bus, gen, branch, areas, gencost, Au, lbu, ubu, ppopt = args
                zu = array([])
                zl = array([])
                z0 = array([])
                Cw = array([])
                H = None
                fparm = array([])
                N = None
            elif nargin == 9:
                baseMVA, bus, gen, branch, areas, gencost, Au, lbu, ubu = args
                zu = array([])
                zl = array([])
                z0 = array([])
                Cw = array([])
                H = None
                fparm = array([])
                N = None
                ppopt = ppoption()
            elif nargin == 8:
                baseMVA, bus, gen, branch, areas, gencost, userfcn, ppopt = args
                zu = array([])
                zl = array([])
                z0 = array([])
                Cw = array([])
                H = None
                fparm = array([])
                N = None
                ubu = array([])
                lbu = array([])
                Au = None
            elif nargin == 7:
                baseMVA, bus, gen, branch, areas, gencost, ppopt = args
                zu = array([])
                zl = array([])
                z0 = array([])
                Cw = array([])
                H = None
                fparm = array([])
                N = None
                ubu = array([])
                lbu = array([])
                Au = None
            elif nargin == 6:
                baseMVA, bus, gen, branch, areas, gencost = args
                zu = array([])
                zl = array([])
                z0 = array([])
                Cw = array([])
                H = None
                fparm = array([])
                N = None
                ppopt = ppoption()
                ubu = array([])
                lbu = array([])
                Au = None
        else:
            stderr.write('opf_args: Incorrect input arg order, number or type\n')

    if N is not None:
        nw = N.shape[0]
    else:
        nw = 0

    if nw:
        if Cw.shape[0] != nw:
            stderr.write('opf_args.m: dimension mismatch between N and Cw in '
                         'generalized cost parameters\n')
        if len(fparm) > 0 and fparm.shape[0] != nw:
            stderr.write('opf_args.m: dimension mismatch between N and fparm '
                         'in generalized cost parameters\n')
        if (H is not None) and (H.shape[0] != nw | H.shape[0] != nw):
            stderr.write('opf_args.m: dimension mismatch between N and H in '
                         'generalized cost parameters\n')
        if Au is not None:
            if Au.shape[0] > 0 and N.shape[1] != Au.shape[1]:
                stderr.write('opf_args.m: A and N must have the same number '
                             'of columns\n')
        ## make sure N and H are sparse
        if not issparse(N):
            stderr.write('opf_args.m: N must be sparse in generalized cost '
                         'parameters\n')
        if not issparse(H):
            stderr.write('opf_args.m: H must be sparse in generalized cost parameters\n')

    if Au is not None and not issparse(Au):
        stderr.write('opf_args.m: Au must be sparse\n')
    if ppopt == None or len(ppopt) == 0:
        ppopt = ppoption()

    return baseMVA, bus, gen, branch, gencost, Au, lbu, ubu, \
        ppopt, N, fparm, H, Cw, z0, zl, zu, userfcn, areas


def opf_args2(*args):
    """Parses and initializes OPF input arguments.
    """
    baseMVA, bus, gen, branch, gencost, Au, lbu, ubu, \
        ppopt, N, fparm, H, Cw, z0, zl, zu, userfcn, areas = opf_args(*args)

    ppc = args[0] if isinstance(args[0], dict) else {}

    ppc['baseMVA'] = baseMVA
    ppc['bus'] = bus
    ppc['gen'] = gen
    ppc['branch'] = branch
    ppc['gencost'] = gencost

    if areas is not None and len(areas) > 0:
        ppc["areas"] = areas
    if lbu is not None and len(lbu) > 0:
        ppc["A"], ppc["l"], ppc["u"] = Au, lbu, ubu
    if Cw is not None and len(Cw) > 0:
        ppc["N"], ppc["Cw"] = N, Cw
        if len(fparm) > 0:
            ppc["fparm"] = fparm
        #if len(H) > 0:
        ppc["H"] = H
    if z0 is not None and len(z0) > 0:
        ppc["z0"] = z0
    if zl is not None and len(zl) > 0:
        ppc["zl"] = zl
    if zu is not None and len(zu) > 0:
        ppc["zu"] = zu
    if userfcn is not None and len(userfcn) > 0:
        ppc["userfcn"] = userfcn

    return ppc, ppopt
