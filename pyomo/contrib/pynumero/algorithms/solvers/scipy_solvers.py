from pyomo.core.base.objective import Objective
from pyomo.common.modeling import unique_component_name
from pyomo.contrib.pynumero.interfaces.pyomo_nlp import PyomoNLP
from pyomo.contrib.pynumero.algorithms.solvers.square_solver_base import (
    _SquareNlpSolverBase,
)

import scipy as sp


class ScipyRootSolver(object):

    def solve(model):

        active_objs = list(model.component_data_objects(Objective, active=True))
        if len(active_objs) == 0:
            obj_name = unique_component_name(model, "_obj")
            obj = pyo.Objective(expr=0.0)
            model.add_component(name, obj)

        nlp = PyomoNLP(model)

        if len(active_objs) == 0:
            model.del_component(obj_name)
        
        # Call to solve(nlp)

        # Transfer values back to Pyomo model


class FsolveNlpSolver(_SquareNlpSolverBase):

    def solve(self, x0=None):
        if x0 is None:
            x0 = self._nlp.get_primals()
        sp.optimize.fsolve(
            self.evaluate_function,
            x0,
            fprime=self.evaluate_jacobian,
        )


class RootNlpSolver(_SquareNlpSolverBase):

    def solve(self, x0=None):
        if x0 is None:
            x0 = self._nlp.get_primals()
        sp.optimize.root(
            self.evaluate_function,
            x0,
            jac=self.evaluate_jacobian,
        )
