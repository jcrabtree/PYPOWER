# Copyright (C) 2010-2011 Power System Engineering Research Center (PSERC)
# Copyright (C) 2011 Richard Lincoln
#
# PYPOWER is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# PYPOWER is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY], without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PYPOWER. If not, see <http://www.gnu.org/licenses/>.

"""Modifies generator costs by shifting or scaling (F or X).
"""

import sys

from numpy import zeros, ones, arange, dot, cumsum, flatnonzero as find

from idx_cost import MODEL, NCOST, PW_LINEAR, POLYNOMIAL, COST


def modcost(gencost, alpha, modtype='SCALE_F'):
    """Modifies generator costs by shifting or scaling (F or X).

    For each generator cost F(X) (for real or reactive power) in
    C{gencost}, this function modifies the cost by scaling or shifting
    the function by C{alpha}, depending on the value of C{modtype}, and
    and returns the modified C{gencost}. Rows of C{gencost} can be a mix
    of polynomial or piecewise linear costs.

    C{modtype} takes one of the 4 possible values (let F_alpha(X) denote the
    the modified function)::
        SCALE_F (default) : F_alpha(X)         == F(X) * ALPHA
        SCALE_X           : F_alpha(X * ALPHA) == F(X)
        SHIFT_F           : F_alpha(X)         == F(X) + ALPHA
        SHIFT_X           : F_alpha(X + ALPHA) == F(X)

    @author: Ray Zimmerman (PSERC Cornell)
    @author: Richard Lincoln
    """
    gencost = gencost.copy()

    ng, m = gencost.shape
    if ng != 0:
        ipwl = find(gencost[:, MODEL] == PW_LINEAR)
        ipol = find(gencost[:, MODEL] == POLYNOMIAL)
        c = gencost[ipol, COST:m]

        if modtype == 'SCALE_F':
            gencost[ipol, COST:m]       = alpha * c
            gencost[ipwl, COST+1:m:2]   = alpha * gencost[ipwl, COST + 1:m:2]
        elif modtype == 'SCALE_X':
            for k in range(len(ipol)):
                n = gencost[ipol[k], NCOST].astype(int)
                for i in range(n):
                    gencost[ipol[k], COST + i] = c[k, i] / alpha**(n - i - 1)
            gencost[ipwl, COST:m - 1:2]   = alpha * gencost[ipwl, COST:m - 1:2]
        elif modtype == 'SHIFT_F':
            for k in range(len(ipol)):
                n = gencost[ipol[k], NCOST].astype(int)
                gencost[ipol[k], COST + n - 1] = alpha + c[k, n - 1]
            gencost[ipwl, COST+1:m:2]   = alpha + gencost[ipwl, COST + 1:m:2]
        elif modtype == 'SHIFT_X':
            for k in range(len(ipol)):
                n = gencost[ipol[k], NCOST].astype(int)
                gencost[ipol[k], COST:COST + n] = \
                        polyshift(c[k, :n].T, alpha).T
            gencost[ipwl, COST:m - 1:2]   = alpha + gencost[ipwl, COST:m - 1:2]
        else:
            sys.stderr.write('modcost: "%s" is not a valid modtype\n' % modtype)

    return gencost


def polyshift(c, a):
    """Returns the coefficients of a horizontally shifted polynomial.

    C{d = polyshift(c, a)} shifts to the right by C{a}, the polynomial whose
    coefficients are given in the column vector C{c}.

    Example: For any polynomial with C{n} coefficients in C{c}, and any values
    for C{x} and shift C{a}, the C{f - f0} should be zero::
        x = rand
        a = rand
        c = rand(n, 1);
        f0 = polyval(c, x)
        f  = polyval(polyshift(c, a), x+a)
    """
    n = len(c)
    d = zeros(c.shape)
    A = pow(-a * ones(n), arange(n))
    b = ones(n)
    for k in range(n):
        d[n - k - 1] = dot(b, c[n - k - 1::-1] * A[:n - k])
        b = cumsum(b[:n - k - 1])

    return d
