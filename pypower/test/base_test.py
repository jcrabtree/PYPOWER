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

from pypower import idx_bus, idx_gen, idx_brch, loadcase, ext2int, bustypes

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

        #: Number of decimal places to round to for float equality.
        self.places = 7

        self.case = None
        self.opf = None


    def test_loadcase(self):
        """Test loading a case.
        """
        path = join(dirname(loadcase.__file__), self.case_name)

        ppc = loadcase.loadcase(path)

        self.compare_case(ppc, "loadcase")


    def test_ext2int(self):
        """Test conversion from external to internal indexing.
        """
        path = join(dirname(loadcase.__file__), self.case_name)
        ppc = loadcase.loadcase(path)
        ppc = ext2int.ext2int(ppc)

        self.compare_case(ppc, "ext2int")


    def test_bustypes(self):
        """Test bus index lists.
        """
        path = join(dirname(loadcase.__file__), self.case_name)

        ppc = loadcase.loadcase(path)
        ppc = ext2int.ext2int(ppc)
        ref, pv, pq = bustypes.bustypes(ppc["bus"], ppc["gen"])

        path = join(DATA_DIR, self.case_name, "bustypes")
        ref_mp = mmread(join(path, "ref.mtx"))
        pv_mp = mmread(join(path, "pv.mtx"))
        pq_mp = mmread(join(path, "pq.mtx"))

        # Adjust for MATLAB 1 (one) based indexing.
        ref += 1
        pv += 1
        pq += 1

        self.assertTrue(self.equal(ref, ref_mp.T))
        self.assertTrue(self.equal(pv, pv_mp.T))
        self.assertTrue(self.equal(pq, pq_mp.T))


    def compare_case(self, ppc, dir):
        """Compares the given case against MATPOWER data in the given directory.
        """
        # Adjust for MATLAB 1 (one) based indexing.
        ppc["bus"][:, idx_bus.BUS_I] += 1
        ppc["gen"][:, idx_gen.GEN_BUS] += 1
        ppc["branch"][:, idx_brch.F_BUS] += 1
        ppc["branch"][:, idx_brch.T_BUS] += 1

        path = join(DATA_DIR, self.case_name, dir)

        baseMVA_mp = mmread(join(path, "baseMVA.mtx"))
        self.assertAlmostEqual(ppc["baseMVA"], baseMVA_mp[0][0], self.places)

        if "version" in ppc:
            version_mp = mmread(join(path, "version.mtx"))
            self.assertEqual(ppc["version"], str(int(version_mp[0][0])))

        bus_mp = mmread(join(path, "bus.mtx"))
        self.assertTrue(self.equal(ppc["bus"], bus_mp), dir)

        gen_mp = mmread(join(path, "gen.mtx"))
        self.assertTrue(self.equal(ppc["gen"], gen_mp), dir)

        branch_mp = mmread(join(path, "branch.mtx"))
        self.assertTrue(self.equal(ppc["branch"], branch_mp), dir)

        if "areas" in ppc:
            areas_mp = mmread(join(path, "gencost.mtx"))
            self.assertTrue(self.equal(ppc["areas"], areas_mp), dir)

        if "gencost" in ppc:
            gencost_mp = mmread(join(path, "gencost.mtx"))
            self.assertTrue(self.equal(ppc["gencost"], gencost_mp), dir)


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
