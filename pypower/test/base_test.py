# Copyright (C) 2009-2010 Richard Lincoln
#
# Licensed under the Apache License, Version 2.0 [the "License"]
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

from os.path import join, dirname

from scipy.io.mmio import mmread

from numpy import allclose

from pypower import loadcase

DATA_DIR = join(dirname(__file__), "data")

class _BaseTestCase(unittest.TestCase):
    """Abstract PYPOWER test case.
    """

    def __init__(self, methodName='runTest'):
        super(_BaseTestCase, self).__init__(methodName)

        #: Name of the PYPOWER case and the folder in which the MatrixMarket
        #  data exists. Subclasses should set this value.
        self.case_name = ""

        #: Relative tolerance for equality (see allclose notes).
        self.rtol = 1e-05

        #: Absolute tolerance for equality (see allclose notes).
        self.atol = 1e-08

        self.case = None
        self.opf = None


    def test_loadcase(self):
        """Test loading a case.
        """
        path = join(dirname(loadcase.__file__), self.case_name)

        ppc = loadcase.loadcase(path)

        dir = join(DATA_DIR, self.case_name, "loadcase")

        baseMVA_mp = mmread(join(dir, "baseMVA.mtx"))
        self.assertAlmostEqual(ppc["baseMVA"], baseMVA_mp, self.atol)

        if "version" in ppc:
            version_mp = mmread(join(dir, "version.mtx"))
            self.assertEqual(ppc["version"], str(int(version_mp[0][0])))

        bus_mp = mmread(join(dir, "bus.mtx"))
        self.assertTrue(self.equal(ppc["bus"], bus_mp))

        gen_mp = mmread(join(dir, "gen.mtx"))

        self.assertTrue(self.equal(ppc["gen"], gen_mp))

        branch_mp = mmread(join(dir, "branch.mtx"))
        self.assertTrue(self.equal(ppc["branch"], branch_mp))

        if "areas" in ppc:
            areas_mp = mmread(join(dir, "gencost.mtx"))
            self.assertTrue(self.equal(ppc["areas"], areas_mp))

        if "gencost" in ppc:
            gencost_mp = mmread(join(dir, "gencost.mtx"))
            self.assertTrue(self.equal(ppc["gencost"], gencost_mp))


    def equal(self, a, b):
        """Returns True if two arrays are element-wise equal.
        """
        # If the following equation is element-wise True, then allclose returns
        # True.

        # absolute(`a` - `b`) <= (`atol` + `rtol` * absolute(`b`))

        # The above equation is not symmetric in `a` and `b`, so that
        # `allclose(a, b)` might be different from `allclose(b, a)` in
        # some rare cases.
        return allclose(a, b, self.rtol, self.atol)