#
# Unit Tests for pyomo.opt.base.convert
#
#

import os
from os.path import abspath, dirname
pyomodir = dirname(abspath(__file__))+os.sep+".."+os.sep+".."+os.sep
currdir = dirname(abspath(__file__))+os.sep

import re
from nose.tools import nottest
import pyomo.opt
from pyomo.opt import ProblemFormat, ConverterError
import pyomo
import pyutilib.th as unittest
import pyutilib.services
import pyomo.util.plugin
import pyutilib.common
import xml
import filecmp

old_tempdir = pyutilib.services.TempfileManager.tempdir

class MockArg(object):

    def __init__(self):
        pass

    def valid_problem_types(self):
        return [ProblemFormat.pyomo]

    def write(self,filename="", format=None):
        pass

class MockArg2(MockArg):

    def valid_problem_types(self):
        return [ProblemFormat.nl]

    def write(self,filename="", format=None):
        OUTPUT=open(filename,"w")
        INPUT=open(currdir+"test4.nl")
        for line in INPUT:
            print >>OUTPUT, line,
        OUTPUT.close()
        INPUT.close()

class MockArg3(MockArg):

    def valid_problem_types(self):
        return [ProblemFormat.mod]

    def write(self,filename="", format=None):
        pass

class MockArg4(MockArg):

    def write(self,filename="", format=None):
        OUTPUT=open(filename,"w")
        INPUT=open(currdir+"test4.nl")
        for line in INPUT:
            print >>OUTPUT, line,
        OUTPUT.close()
        INPUT.close()


class OptConvertDebug(unittest.TestCase):

    def setUp(self):
        pyutilib.services.TempfileManager.tempdir = currdir

    def tearDown(self):
        pyutilib.services.TempfileManager.clear_tempfiles()
        pyutilib.services.TempfileManager.tempdir = old_tempdir
        #
        # Reset all options
        #
        #for ep in pyomo.util.plugin.ExtensionPoint(pyomo.util.plugin.IOption):
            #ep.reset()
        pass

    def test_nl_nl1(self):
        """ Convert from NL to NL """
        ans = pyomo.opt.convert_problem( ("test4.nl",), None, [ProblemFormat.nl])
        self.assertEqual(ans[0],("test4.nl",))

    def test_nl_nl2(self):
        """ Convert from NL to NL """
        ans = pyomo.opt.convert_problem( ("test4.nl","tmp.nl"), None, [ProblemFormat.nl])
        self.assertEqual(ans[0],("test4.nl","tmp.nl"))

    def test_error1(self):
        """ No valid problem types """
        try:
            pyomo.opt.convert_problem( ("test4.nl","tmp.nl"), ProblemFormat.nl, [])
            self.fail("Expected ConverterError exception")
        except ConverterError:
            pass

    def test_error2(self):
        """ Target problem type is not valid """
        try:
            pyomo.opt.convert_problem( ("test4.nl","tmp.nl"), ProblemFormat.nl, [ProblemFormat.mps])
            self.fail("Expected ConverterError exception")
        except ConverterError:
            pass

    def test_error3(self):
        """ Empty argument list """
        try:
            pyomo.opt.convert_problem( (), None, [ProblemFormat.mps])
            self.fail("Expected ConverterError exception")
        except ConverterError:
            pass

    def test_error4(self):
        """ Unknown source type """
        try:
            pyomo.opt.convert_problem( ("prob.foo",), None, [ProblemFormat.mps])
            self.fail("Expected ConverterError exception")
        except ConverterError:
            pass

    def test_error5(self):
        """ Unknown source type """
        try:
            pyomo.opt.convert_problem( ("prob.lp",), ProblemFormat.nl, [ProblemFormat.nl])
            self.fail("Expected ConverterError exception")
        except ConverterError:
            pass

    def test_error6(self):
        """ Cannot use pico_convert with more than one file """
        try:
            ans = pyomo.opt.convert_problem( (currdir+"test4.nl","foo"), None, [ProblemFormat.cpxlp])
            self.fail("Expected ConverterError exception")
        except ConverterError:
            pass

    def test_error8(self):
        """ Error when source file cannot be found """
        try:
            ans = pyomo.opt.convert_problem( (currdir+"unknown.nl",), None, [ProblemFormat.cpxlp])
            self.fail("Expected ConverterError exception")
        except pyutilib.common.ApplicationError:
            if pyutilib.services.registered_executable("pico_convert").enabled():
                self.fail("Expected ApplicationError because pico_convert is not available")
            return
        except ConverterError:
            pass

    def test_error9(self):
        """ The Opt configuration has not been initialized """
        cmd = pyutilib.services.registered_executable("pico_convert")
        if not cmd is None:
            cmd.disable()
        try:
            ans = pyomo.opt.convert_problem( (currdir+"test4.nl",), None, [ProblemFormat.cpxlp])
            self.fail("This test didn't fail, but pico_convert should not be defined.")
        except ConverterError:
            pass
        if not cmd is None:
            cmd.enable()

    def test_error10(self):
        """ GLPSOL can only convert file data """
        try:
            arg = MockArg3()
            ans = pyomo.opt.convert_problem( (arg,ProblemFormat.cpxlp,arg), None, [ProblemFormat.cpxlp])
            self.fail("This test didn't fail, but glpsol cannot handle objects.")
        except ConverterError:
            pass

    def test_error11(self):
        """ Cannot convert MOD that contains data """
        try:
            ans = pyomo.opt.convert_problem( (currdir+"test3.mod",currdir+"test5.dat"), None, [ProblemFormat.cpxlp])
            self.fail("Expected ConverterError exception because we provided a MOD file with a 'data;' declaration")
        except pyutilib.common.ApplicationError:
            if pyutilib.registered_executable("glpsol").enabled():
                self.fail("Expected ApplicationError because glpsol is not available")
            return
        except ConverterError:
            pass

if __name__ == "__main__":
    unittest.main()
