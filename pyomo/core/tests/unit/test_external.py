#  ___________________________________________________________________________
#
#  Pyomo: Python Optimization Modeling Objects
#  Copyright 2017 National Technology and Engineering Solutions of Sandia, LLC
#  Under the terms of Contract DE-NA0003525 with National Technology and
#  Engineering Solutions of Sandia, LLC, the U.S. Government retains certain
#  rights in this software.
#  This software is distributed under the 3-clause BSD License.
#  ___________________________________________________________________________
#
import os
import shutil
from io import StringIO

import pyomo.common.unittest as unittest

from pyomo.common.getGSL import find_GSL
from pyomo.common.tempfiles import TempfileManager
from pyomo.environ import ConcreteModel, Var, Objective, SolverFactory, value
from pyomo.core.base.external import (PythonCallbackFunction,
                                      ExternalFunction,
                                      AMPLExternalFunction)
from pyomo.core.base.units_container import pint_available, units
from pyomo.opt import check_available_solvers

def _g(*args):
    return len(args)

def _h(*args):
    return 2 + sum(args)

class TestPythonCallbackFunction(unittest.TestCase):
    def test_call_countArgs(self):
        m = ConcreteModel()
        m.f = ExternalFunction(_g)
        self.assertIsInstance(m.f, PythonCallbackFunction)
        self.assertEqual(value(m.f()), 0)
        self.assertEqual(value(m.f(2)), 1)
        self.assertEqual(value(m.f(2,3)), 2)

    def test_call_sumfcn(self):
        m = ConcreteModel()
        m.f = ExternalFunction(_h)
        self.assertIsInstance(m.f, PythonCallbackFunction)
        self.assertEqual(value(m.f()), 2.0)
        self.assertEqual(value(m.f(1)), 3.0)
        self.assertEqual(value(m.f(1,2)), 5.0)

    def test_getname(self):
        m = ConcreteModel()
        m.f = ExternalFunction(_h)
        self.assertIsInstance(m.f, PythonCallbackFunction)
        self.assertEqual(m.f.name, "f")
        self.assertEqual(m.f.local_name, "f")
        self.assertEqual(m.f.getname(), "f")
        self.assertEqual(m.f.getname(True), "f")

        M = ConcreteModel()
        M.m = m
        self.assertEqual(M.m.f.name, "m.f")
        self.assertEqual(M.m.f.local_name, "f")
        self.assertEqual(M.m.f.getname(), "f")
        self.assertEqual(M.m.f.getname(True), "m.f")

    def test_extra_kwargs(self):
        m = ConcreteModel()
        with self.assertRaises(ValueError):
            m.f = ExternalFunction(_g, this_should_raise_error='foo')

    def test_pprint(self):
        m = ConcreteModel()
        m.h = ExternalFunction(_g)

        out = StringIO()
        m.pprint(ostream=out)
        self.assertEqual(out.getvalue().strip(), """
1 ExternalFunction Declarations
    h : function=_g, units=None, arg_units=None

1 Declarations: h
        """.strip())

        if not pint_available:
            return
        m.i = ExternalFunction(function=_h,
                               units=units.kg, arg_units=[units.m, units.s])
        out = StringIO()
        m.pprint(ostream=out)
        self.assertEqual(out.getvalue().strip(), """
2 ExternalFunction Declarations
    h : function=_g, units=None, arg_units=None
    i : function=_h, units=kg, arg_units=['m', 's']

2 Declarations: h i
        """.strip())


class TestAMPLExternalFunction(unittest.TestCase):
    def assertListsAlmostEqual(self, first, second, places=7, msg=None):
        self.assertEqual(len(first), len(second))
        msg = "lists %s and %s differ at item " % (
            first, second)
        for i,a in enumerate(first):
            self.assertAlmostEqual(a, second[i], places, msg + str(i))

    def test_getname(self):
        m = ConcreteModel()
        m.f = ExternalFunction(library="junk.so", function="junk")
        self.assertIsInstance(m.f, AMPLExternalFunction)
        self.assertEqual(m.f.name, "f")
        self.assertEqual(m.f.local_name, "f")
        self.assertEqual(m.f.getname(), "f")
        self.assertEqual(m.f.getname(True), "f")

        M = ConcreteModel()
        M.m = m
        self.assertEqual(M.m.f.name, "m.f")
        self.assertEqual(M.m.f.local_name, "f")
        self.assertEqual(M.m.f.getname(), "f")
        self.assertEqual(M.m.f.getname(True), "m.f")

    def test_load_local_asl_library(self):
        DLL = find_GSL()
        if not DLL:
            self.skipTest("Could not find the amplgsl.dll library")

        LIB = 'test_pyomo_external_gsl.dll'

        model = ConcreteModel()
        model.gamma = ExternalFunction(
            library=LIB, function="gsl_sf_gamma")
        model.x = Var(initialize=3, bounds=(1e-5,None))
        model.o = Objective(expr=model.gamma(model.x))

        with TempfileManager.new_context() as tempfile:
            dname = tempfile.mkdtemp()
            shutil.copyfile(DLL, os.path.join(dname, LIB))
            # Without changing directories, the load should fail
            with self.assertRaises(OSError):
                value(model.o)
            # Changing directories should pick up the library
            try:
                orig_dir = os.getcwd()
                os.chdir(dname)
                self.assertAlmostEqual(value(model.o), 2.0, 7)
            finally:
                os.chdir(orig_dir)

    def test_eval_gsl_function(self):
        DLL = find_GSL()
        if not DLL:
            self.skipTest("Could not find the amplgsl.dll library")
        model = ConcreteModel()
        model.gamma = ExternalFunction(
            library=DLL, function="gsl_sf_gamma")
        model.bessel = ExternalFunction(
            library=DLL, function="gsl_sf_bessel_Jnu")
        model.x = Var(initialize=3, bounds=(1e-5,None))
        model.o = Objective(expr=model.gamma(model.x))
        self.assertAlmostEqual(value(model.o), 2.0, 7)

        f = model.bessel.evaluate((0.5, 2.0,))
        self.assertAlmostEqual(f, 0.5130161365618272, 7)

    def test_eval_fgh_gsl_function(self):
        DLL = find_GSL()
        if not DLL:
            self.skipTest("Could not find the amplgsl.dll library")
        model = ConcreteModel()
        model.gamma = ExternalFunction(
            library=DLL, function="gsl_sf_gamma")
        model.beta = ExternalFunction(
            library=DLL, function="gsl_sf_beta")
        model.bessel = ExternalFunction(
            library=DLL, function="gsl_sf_bessel_Jnu")

        f,g,h = model.gamma.evaluate_fgh((2.0,))
        self.assertAlmostEqual(f, 1.0, 7)
        self.assertListsAlmostEqual(g, [0.422784335098467], 7)
        self.assertListsAlmostEqual(h, [0.8236806608528794], 7)

        f,g,h = model.beta.evaluate_fgh((2.5, 2.0,), fixed=[1,1])
        self.assertAlmostEqual(f, 0.11428571428571432, 7)
        self.assertListsAlmostEqual(g, [0.0, 0.0], 7)
        self.assertListsAlmostEqual(h, [0.0, 0.0, 0.0], 7)

        f,g,h = model.beta.evaluate_fgh((2.5, 2.0,), fixed=[0,1])
        self.assertAlmostEqual(f, 0.11428571428571432, 7)
        self.assertListsAlmostEqual(
            g, [-0.07836734693877555, 0.0], 7)
        self.assertListsAlmostEqual(
            h, [0.08135276967930034, 0.0, 0.0], 7)

        f,g,h = model.beta.evaluate_fgh((2.5, 2.0,))
        self.assertAlmostEqual(f, 0.11428571428571432, 7)
        self.assertListsAlmostEqual(
            g, [-0.07836734693877555, -0.11040989614412142], 7)
        self.assertListsAlmostEqual(
            h, [0.08135276967930034, 0.0472839170086535, 0.15194654464270113],
            7)

        f,g,h = model.beta.evaluate_fgh((2.5, 2.0,), fgh=1)
        self.assertAlmostEqual(f, 0.11428571428571432, 7)
        self.assertListsAlmostEqual(
            g, [-0.07836734693877555, -0.11040989614412142], 7)
        self.assertIsNone(h)

        f,g,h = model.beta.evaluate_fgh((2.5, 2.0,), fgh=0)
        self.assertAlmostEqual(f, 0.11428571428571432, 7)
        self.assertIsNone(g)
        self.assertIsNone(h)

        f,g,h = model.bessel.evaluate_fgh((2.5, 2.0,), fixed=[1,0])
        self.assertAlmostEqual(f, 0.223924531469, 7)
        self.assertListsAlmostEqual(g, [0.0, 0.21138811435101745], 7)
        self.assertListsAlmostEqual(h, [0.0, 0.0, 0.02026349177575621], 7)

        # Note: Not all AMPL-GSL functions honor the fixed flag
        # (notably, gamma and bessel do not as of 12/2021).  We will
        # test that our interface corrects that

        f,g,h = model.gamma.evaluate_fgh((2.0,), fixed=[1])
        self.assertAlmostEqual(f, 1.0, 7)
        self.assertListsAlmostEqual(g, [0.0], 7)
        self.assertListsAlmostEqual(h, [0.0], 7)

        f,g,h = model.bessel.evaluate_fgh((2.5, 2.0,), fixed=[1,1])
        self.assertAlmostEqual(f, 0.223924531469, 7)
        self.assertListsAlmostEqual(g, [0.0, 0.0], 7)
        self.assertListsAlmostEqual(h, [0.0, 0.0, 0.0], 7)


    @unittest.skipIf(not check_available_solvers('ipopt'),
                     "The 'ipopt' solver is not available")
    def test_solve_gsl_function(self):
        DLL = find_GSL()
        if not DLL:
            self.skipTest("Could not find the amplgsl.dll library")
        model = ConcreteModel()
        model.z_func = ExternalFunction(library=DLL, function="gsl_sf_gamma")
        model.x = Var(initialize=3, bounds=(1e-5,None))
        model.o = Objective(expr=model.z_func(model.x))
        opt = SolverFactory('ipopt')
        res = opt.solve(model, tee=True)
        self.assertAlmostEqual(value(model.o), 0.885603194411, 7)

    @unittest.skipIf(not check_available_solvers('ipopt'),
                     "The 'ipopt' solver is not available")
    def test_clone_gsl_function(self):
        DLL = find_GSL()
        if not DLL:
            self.skipTest("Could not find the amplgsl.dll library")
        m = ConcreteModel()
        m.z_func = ExternalFunction(library=DLL, function="gsl_sf_gamma")
        self.assertIsInstance(m.z_func, AMPLExternalFunction)
        m.x = Var(initialize=3, bounds=(1e-5,None))
        m.o = Objective(expr=m.z_func(m.x))

        opt = SolverFactory('ipopt')

        # Test a simple clone...
        model2 = m.clone()
        res = opt.solve(model2, tee=True)
        self.assertAlmostEqual(value(model2.o), 0.885603194411, 7)

        # Trigger the library to be loaded.  This tests that the CDLL
        # objects that are created when the SO/DLL are loaded do not
        # interfere with cloning the model.
        self.assertAlmostEqual(value(m.o), 2)
        model3 = m.clone()
        res = opt.solve(model3, tee=True)
        self.assertAlmostEqual(value(model3.o), 0.885603194411, 7)

    def test_pprint(self):
        m = ConcreteModel()
        m.f = ExternalFunction(library="junk.so", function="junk")

        out = StringIO()
        m.pprint(ostream=out)
        self.assertEqual(out.getvalue().strip(), """
1 ExternalFunction Declarations
    f : function=junk, library=junk.so, units=None, arg_units=None

1 Declarations: f
        """.strip())

        if not pint_available:
            return
        m.g = ExternalFunction(library="junk.so", function="junk",
                               units=units.kg, arg_units=[units.m, units.s])
        out = StringIO()
        m.pprint(ostream=out)
        self.assertEqual(out.getvalue().strip(), """
2 ExternalFunction Declarations
    f : function=junk, library=junk.so, units=None, arg_units=None
    g : function=junk, library=junk.so, units=kg, arg_units=['m', 's']

2 Declarations: f g
        """.strip())


if __name__ == "__main__":
    unittest.main()
