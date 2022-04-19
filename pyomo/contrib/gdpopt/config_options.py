#  ___________________________________________________________________________
#
#  Pyomo: Python Optimization Modeling Objects
#  Copyright 2017 National Technology and Engineering Solutions of Sandia, LLC
#  Under the terms of Contract DE-NA0003525 with National Technology and
#  Engineering Solutions of Sandia, LLC, the U.S. Government retains certain
#  rights in this software.
#  This software is distributed under the 3-clause BSD License.
#  ___________________________________________________________________________

from pyomo.common.config import (ConfigBlock, ConfigList, ConfigValue,
                                 In, NonNegativeFloat, NonNegativeInt,
                                 PositiveInt)
from pyomo.contrib.gdpopt.master_initialize import valid_init_strategies
from pyomo.contrib.gdpopt.nlp_initialization import (
    restore_vars_to_original_values)
from pyomo.contrib.gdpopt.util import _DoNothing
from pyomo.opt import SolverFactory, UnknownSolver
from pyomo.solvers.plugins.solvers.persistent_solver import PersistentSolver

def _valid_solvers(val):
    # TODO: Can we change this so that people pass in their SolverFactory,
    # because I can't do this--it'll generate an error when pyomo.environ is
    # imported withot the right solvers present. And then I can support this for
    # strings, but deprecate it and warn that there's no error checking in that
    # case... It would simplify the passing solver args stuff too, actually.
    opt = SolverFactory(val)
    if isinstance(opt, UnknownSolver):
        raise ValueError("Expected a valid name for a solver. Received '%s'"
                         % val)
    elif isinstance(opt, PersistentSolver):
        raise ValueError("GDPopt does not currently support the '%s' solver. "
                         "The only supported persistent solvers are those in "
                         "the APPSI package." % val)
    # There's still stuff that could have gone wrong that we won't find out
    # until we call solve, but what can you do?
    return val

def _add_OA_configs(CONFIG):
    CONFIG.declare("init_strategy", ConfigValue(
        default="set_covering", domain=In(valid_init_strategies.keys()),
        description="Initialization strategy to use.",
        doc="""
        Selects the initialization strategy to use when generating
        the initial cuts to construct the master problem."""
    ))
    CONFIG.declare("custom_init_disjuncts", ConfigList(
        # domain=ComponentSets of Disjuncts,
        default=None,
        description="List of disjunct sets to use for initialization."
    ))
    CONFIG.declare("max_slack", ConfigValue(
        default=1000, domain=NonNegativeFloat,
        description="Upper bound on slack variables for OA"
    ))
    CONFIG.declare("OA_penalty_factor", ConfigValue(
        default=1000, domain=NonNegativeFloat,
        description="""
        Penalty multiplication term for slack variables on the
        objective value."""
    ))
    CONFIG.declare("set_cover_iterlim", ConfigValue(
        default=8, domain=NonNegativeInt,
        description="Limit on the number of set covering iterations."
    ))
    CONFIG.declare("master_problem_transformation", ConfigValue(
        default='gdp.bigm',
        description="""
        Name of the transformation to use to transform the
        master problem from a GDP to an algebraic model."""
    ))
    CONFIG.declare("call_before_master_solve", ConfigValue(
        default=_DoNothing,
        description="callback hook before calling the master problem solver",
        doc="""
        Callback called right before the MILP master problem is solved.
        Takes two arguments: The master problem and the GDPopt utility block on
        the master problem.

        Note that unless you are *very* confident in what you are doing, the
        problem should not be modified in this callback: it should be used
        to interrogate the problem only.
        """
    ))
    CONFIG.declare("call_after_master_solve", ConfigValue(
        default=_DoNothing,
        description="callback hook after a solution of the master problem",
        doc="""
        Callback called right after the MILP master problem is solved.
        Takes two arguments: The master problem and the GDPopt utility block on
        the master problem.

        Note that unless you are *very* confident in what you are doing, the
        problem should not be modified in this callback: it should be used
        to interrogate the problem only.
        """
    ))
    CONFIG.declare("subproblem_initialization_method", ConfigValue(
        default=restore_vars_to_original_values, # Historical default
        description=""""
        callback to specify custom routines to initialize the
        (MI)NLP subproblems.""",
        doc="""
        Callback to specify custom routines for initializing the (MI)NLP
        subproblems. This method is called after the master problem solution
        is fixed in the subproblem and before the subproblem is solved (or
        pre-solved).

        Accepts two arguments: the subproblem GDPopt utility
        block and the master problem GDPopt utility block. The master problem
        contains the most recent master problem solution.

        The return of this method will be unused: The method should directly
        set the value of the variables on the subproblem
        """
    ))
    CONFIG.declare("call_before_subproblem_solve", ConfigValue(
        default=_DoNothing,
        description="callback hook before calling the subproblem solver",
        doc="""
        Callback called right before the (MI)NLP subproblem is solved.
        Takes two arguments: The subproblem and the GDPopt utility block on
        the subproblem.

        Note that unless you are *very* confident in what you are doing, the
        subproblem should not be modified in this callback: it should be used
        to interrogate the problem only.

        To initialize the problem before it is solved, please specify a method
        in the 'subproblem_initialization_method' argument.
        """
    ))
    CONFIG.declare("call_after_subproblem_solve", ConfigValue(
        default=_DoNothing,
        description="""
        callback hook after a solution of the
        "nonlinear subproblem""",
        doc="""
        Callback called right after the (MI)NLP subproblem is solved.
        Takes two arguments: The subproblem and the GDPopt utility block on
        the subproblem.

        Note that unless you are *very* confident in what you are doing, the
        subproblem should not be modified in this callback: it should be used
        to interrogate the problem only.
        """
    ))
    CONFIG.declare("call_after_subproblem_feasible", ConfigValue(
        default=_DoNothing,
        description="""
        callback hook after feasible solution of
        the nonlinear subproblem""",
        doc="""
        Callback called right after the (MI)NLP subproblem is solved,
        if it was feasible. Takes two arguments: The subproblem and the GDPopt
        utility block on the subproblem.

        Note that unless you are *very* confident in what you are doing, the
        subproblem should not be modified in this callback: it should be used
        to interrogate the problem only.
        """
    ))
    CONFIG.declare("round_discrete_vars", ConfigValue(
        default=True,
        description="""flag to round subproblem discrete variable values to the
        nearest integer. Rounding is done before fixing disjuncts."""
    ))
    CONFIG.declare("force_subproblem_nlp", ConfigValue(
        default=False,
        description="""Force subproblems to be NLP, even if discrete variables
        exist."""
    ))
    CONFIG.declare("mip_presolve", ConfigValue(
        default=True,
        description="""
        Flag to enable or diable GDPopt MIP presolve.
        Default=True.""",
        domain=bool
    ))
    CONFIG.declare("subproblem_presolve", ConfigValue(
        default=True,
        description="""
        Flag to enable or disable subproblem presolve.
        Default=True.""",
        domain=bool
    ))
    CONFIG.declare("max_fbbt_iterations", ConfigValue(
        default=3,
        description="""
        Maximum number of feasibility-based bounds tightening
        iterations to do during NLP subproblem preprocessing.""",
        domain=PositiveInt
    ))
    CONFIG.declare("tighten_nlp_var_bounds", ConfigValue(
        default=False,
        description="""
        Whether or not to do feasibility-based bounds tightening
        on the variables in the NLP subproblem before solving it.""",
        domain=bool
    ))
    CONFIG.declare("calc_disjunctive_bounds", ConfigValue(
        default=False,
        description="""
        Calculate special disjunctive variable bounds for GLOA.
        False by default.""",
        domain=bool
    ))
    CONFIG.declare("obbt_disjunctive_bounds", ConfigValue(
        default=False,
        description="""
        Use optimality-based bounds tightening rather than feasibility-based
        bounds tightening to compute disjunctive variable bounds. False by
        default.""",
        domain=bool
    ))

def _add_BB_configs(CONFIG):
    CONFIG.declare("check_sat", ConfigValue(
        default=False,
        domain=bool,
        description="""
        When True, GDPopt-LBB will check satisfiability
        at each node via the pyomo.contrib.satsolver interface"""
    ))
    CONFIG.declare("solve_local_rnGDP", ConfigValue(
        default=False,
        domain=bool,
        description="""
        When True, GDPopt-LBB will solve a local MINLP at each node."""
    ))


def _add_mip_solver_configs(CONFIG):
    CONFIG.declare("mip_solver", ConfigValue(
        default="gurobi",
        domain=_valid_solvers,
        description="""
        Mixed integer linear solver to use. Note that no persisent solvers
        other than the auto-persistent solvers in the APPSI package are
        supported."""
    ))
    CONFIG.declare("mip_solver_args", ConfigBlock(
        description="""
        Keyword arguments to send to the MILP subsolver solve() invocation""",
        implicit=True))


def _add_nlp_solver_configs(CONFIG):
    CONFIG.declare("nlp_solver", ConfigValue(
        default="ipopt",
        domain=_valid_solvers,
        description="""
        Nonlinear solver to use. Note that no persisent solvers
        other than the auto-persistent solvers in the APPSI package are
        supported."""))
    CONFIG.declare("nlp_solver_args", ConfigBlock(
        description="""
        Keyword arguments to send to the NLP subsolver solve() invocation""",
        implicit=True))
    CONFIG.declare("minlp_solver", ConfigValue(
        default="baron",
        domain=_valid_solvers,
        description="""
        MINLP solver to use. Note that no persisent solvers
        other than the auto-persistent solvers in the APPSI package are
        supported."""
    ))
    CONFIG.declare("minlp_solver_args", ConfigBlock(
        description="""
        Keyword arguments to send to the MINLP subsolver solve() invocation""",
        implicit=True))
    CONFIG.declare("local_minlp_solver", ConfigValue(
        default="bonmin",
        domain=_valid_solvers,
        description="""
        MINLP solver to use. Note that no persisent solvers
        other than the auto-persistent solvers in the APPSI package are
        supported."""
    ))
    CONFIG.declare("local_minlp_solver_args", ConfigBlock(
        description="""
        Keyword arguments to send to the local MINLP subsolver solve()
        invocation""",
        implicit=True))


def _add_tolerance_configs(CONFIG):
    CONFIG.declare("bound_tolerance", ConfigValue(
        default=1E-6, domain=NonNegativeFloat,
        description="Tolerance for bound convergence."
    ))
    CONFIG.declare("small_dual_tolerance", ConfigValue(
        default=1E-8,
        description="""
        When generating cuts, small duals multiplied by expressions can
        cause problems. Exclude all duals  smaller in absolue value than the
        following."""
    ))
    CONFIG.declare("integer_tolerance", ConfigValue(
        default=1E-5,
        description="Tolerance on integral values."
    ))
    CONFIG.declare("constraint_tolerance", ConfigValue(
        default=1E-6,
        description="""
        Tolerance on constraint satisfaction.

        Increasing this tolerance corresponds to being more conservative in
        declaring the model or an NLP subproblem to be infeasible.
        """
    ))
    CONFIG.declare("variable_tolerance", ConfigValue(
        default=1E-8,
        description="Tolerance on variable bounds."
    ))
    CONFIG.declare("zero_tolerance", ConfigValue(
        default=1E-15,
        description="Tolerance on variable equal to zero."))
