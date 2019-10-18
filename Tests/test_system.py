import FESTIM
import fenics
import pytest
import sympy as sp
from pathlib import Path


# System tests

def test_run_temperature_stationary(tmpdir):
    '''
    Check that the temperature module works well in 1D stationary
    '''
    d = tmpdir.mkdir("Solution_Test")
    u = 1 + 2*FESTIM.x**2
    size = 1
    parameters = {
        "materials": [
            {
                "thermal_cond": 1,
                "alpha": 1.1e-10,
                "beta": 6*6.3e28,
                "density": 6.3e28,
                "borders": [0, size],
                "E_diff": 0.39,
                "D_0": 4.1e-7,
                "id": 1
                }
                ],
        "traps": [
            ],
        "mesh_parameters": {
                "initial_number_of_cells": 200,
                "size": size,
                "refinements": [
                ],
            },
        "boundary_conditions": [
                    {
                        "surface": [1],
                        "value": 1,
                        "component": 0,
                        "type": "dc"
                    }
            ],
        "temperature": {
            "type": "solve_stationary",
            "boundary_conditions": [
                {
                    "type": "dirichlet",
                    "value": u,
                    "surface": [1, 2]
                }
                ],
            "source_term": [
                {
                    "value": -4,
                    "volume": 1
                }
            ],
            "initial_condition": u
        },
        "source_term": {
            'value': 0
            },
        "solving_parameters": {
            "final_time": 30,
            "initial_stepsize": 0.5,
            "adaptive_stepsize": {
                "stepsize_change_ratio": 1,
                "t_stop": 40,
                "stepsize_stop_max": 0.5,
                "dt_min": 1e-5
                },
            "newton_solver": {
                "absolute_tolerance": 1e10,
                "relative_tolerance": 1e-9,
                "maximum_iterations": 50,
            }
            },
        "exports": {
            "txt": {
                "functions": ['retention'],
                "times": [100],
                "labels": ['retention']
            },
            "xdmf": {
                    "functions": ['T'],
                    "labels":  ['temperature'],
                    "folder": str(Path(d))
            },
            "error": [
                {
                    "computed_solutions": ['T'],
                    "exact_solutions": [u],
                    "norm": 'error_max',
                    "degree": 4
                }
            ]
            },

    }
    output = FESTIM.generic_simulation.run(parameters)
    assert output["error"][0][1] < 1e-9


def test_run_temperature_transient(tmpdir):
    '''
    Check that the temperature module works well in 1D transient
    '''
    d = tmpdir.mkdir("Solution_Test")
    u = 1 + 2*FESTIM.x**2+FESTIM.t
    size = 1
    parameters = {
        "materials": [
            {
                "thermal_cond": 1,
                "rho": 1,
                "heat_capacity": 1,
                "alpha": 1.1e-10,  # lattice constant ()
                "beta": 6*6.3e28,  # number of solute sites per atom (6 for W)
                "density": 6.3e28,
                "borders": [0, size],
                "E_diff": 0.39,
                "D_0": 4.1e-7,
                "id": 1
            }
            ],
        "traps": [
            ],
        "mesh_parameters": {
                "initial_number_of_cells": 200,
                "size": size,
                "refinements": [
                ],
            },
        "boundary_conditions": [
                    {
                        "surface": [1],
                        "value": 1,
                        "component": 0,
                        "type": "dc"
                    }
            ],
        "temperature": {
            "type": "solve_transient",
            "boundary_conditions": [
                {
                    "type": "dirichlet",
                    "value": u,
                    "surface": [1, 2]
                }
                ],
            "source_term": [
                {
                    "value": sp.diff(u, FESTIM.t) - sp.diff(u, FESTIM.x, 2),
                    "volume": 1
                }
            ],
            "initial_condition": u
        },
        "source_term": {
            'value': 0
            },
        "solving_parameters": {
            "final_time": 30,
            "initial_stepsize": 0.5,
            "adaptive_stepsize": {
                "stepsize_change_ratio": 1,
                "t_stop": 40,
                "stepsize_stop_max": 0.5,
                "dt_min": 1e-5
                },
            "newton_solver": {
                "absolute_tolerance": 1e10,
                "relative_tolerance": 1e-9,
                "maximum_iterations": 50,
            }
            },
        "exports": {
            "txt": {
                "functions": ['retention'],
                "times": [100],
                "labels": ['retention']
            },
            "xdmf": {
                    "functions": ['T'],
                    "labels":  ['temperature'],
                    "folder": str(Path(d))
            },
            "error": [
                {
                    "computed_solutions": ['T'],
                    "exact_solutions": [u],
                    "norm": 'error_max',
                    "degree": 4
                }
            ]
            },

    }
    output = FESTIM.generic_simulation.run(parameters)

    assert output["error"][0][1] < 1e-9


def test_run_MMS(tmpdir):
    '''
    Test function run() for several refinements
    '''
    d = tmpdir.mkdir("Solution_Test")
    u = 1 + sp.exp(-4*fenics.pi**2*FESTIM.t)*sp.cos(2*fenics.pi*FESTIM.x)
    v = 1 + sp.exp(-4*fenics.pi**2*FESTIM.t)*sp.cos(2*fenics.pi*FESTIM.x)

    def parameters(h, dt, final_time, u, v):
        size = 1
        v_0 = 1e13
        E_t = 1.5
        T = 700 + 30*FESTIM.x
        density = 1 * 6.3e28
        beta = 6*density
        alpha = 1.1e-10
        n_trap = 1e-1*density
        E_diff = 0.39
        D_0 = 4.1e-7
        k_B = 8.6e-5
        D = D_0 * sp.exp(-E_diff/k_B/T)
        v_i = v_0 * sp.exp(-E_t/k_B/T)
        v_m = D/alpha/alpha/beta

        f = sp.diff(u, FESTIM.t) + sp.diff(v, FESTIM.t) - \
            D * sp.diff(u, FESTIM.x, 2) - \
            sp.diff(D, FESTIM.x)*sp.diff(u, FESTIM.x)
        g = sp.diff(v, FESTIM.t) + v_i*v - v_m * u * (n_trap-v)
        parameters = {
            "materials": [
                {
                    "alpha": alpha,  # lattice constant ()
                    "beta": beta,  # number of solute sites per atom (6 for W)
                    "density": density,
                    "borders": [0, size],
                    "E_diff": E_diff,
                    "D_0": D_0,
                    "id": 1
                    }
                    ],
            "traps": [
                {
                    "energy": E_t,
                    "density": n_trap,
                    "materials": 1,
                    "source_term": g
                }
                ],
            "initial_conditions": [
                {
                    "value": u,
                    "component": 0
                },
                {
                    "value": v,
                    "component": 1
                }
            ],

            "mesh_parameters": {
                    "initial_number_of_cells": round(size/h),
                    "size": size,
                    "refinements": [
                    ],
                },
            "boundary_conditions": [
                    {
                        "surface": [1, 2],
                        "value": u,
                        "component": 0,
                        "type": "dc"
                    },
                    {
                        "surface": [1, 2],
                        "value": v,
                        "component": 1,
                        "type": "dc"
                    }
                ],
            "temperature": {
                    'type': "expression",
                    'value': T
                },
            "source_term": {
                'value': f
                },
            "solving_parameters": {
                "final_time": final_time,
                "initial_stepsize": dt,
                "adaptive_stepsize": {
                    "stepsize_change_ratio": 1,
                    "t_stop": 0,
                    "stepsize_stop_max": dt,
                    "dt_min": 1e-5
                    },
                "newton_solver": {
                    "absolute_tolerance": 1e-10,
                    "relative_tolerance": 1e-9,
                    "maximum_iterations": 50,
                }
                },
            "exports": {
                "txt": {
                    "functions": [],
                    "times": [],
                    "labels": [],
                    "folder": str(Path(d))
                },
                "TDS": {
                    "file": "desorption",
                    "TDS_time": 0,
                    "folder": str(Path(d))
                    },
                "error": [
                    {
                        "computed_solutions": [0, 1],
                        "exact_solutions": [u, v],
                        "norm": 'error_max',
                        "degree": 4
                    }
                ]
                },
        }
        return parameters

    tol_u = 1e-7
    tol_v = 1e-1
    sizes = [1/1600, 1/1700]
    dt = 0.1/50
    final_time = 0.1
    for h in sizes:
        output = FESTIM.generic_simulation.run(
            parameters(h, dt, final_time, u, v))
        error_max_u = output["error"][0][1]
        error_max_v = output["error"][0][2]
        msg = 'Maximum error on u is:' + str(error_max_u) + '\n \
            Maximum error on v is:' + str(error_max_v) + '\n \
            with h = ' + str(h) + '\n \
            with dt = ' + str(dt)
        print(msg)
        assert error_max_u < tol_u and error_max_v < tol_v


def test_run_MMS_steady_state(tmpdir):
    '''
    Test function run() for several refinements in steady state
    '''
    d = tmpdir.mkdir("Solution_Test")
    u = 1 + sp.cos(2*fenics.pi*FESTIM.x)
    v = 1 + sp.cos(2*fenics.pi*FESTIM.x)

    def parameters(h, u, v):
        size = 1
        v_0 = 1e13
        E_t = 1.5
        T = 700 + 30*FESTIM.x
        density = 1
        beta = 6*density
        alpha = 1
        n_trap = 1e-1*density
        E_diff = 0
        D_0 = 1
        k_B = 8.6e-5
        D = D_0 * sp.exp(-E_diff/k_B/T)
        v_i = v_0 * sp.exp(-E_t/k_B/T)
        v_m = D/alpha/alpha/beta
        f = sp.diff(v, FESTIM.t) - D * sp.diff(u, FESTIM.x, 2) - \
            sp.diff(D, FESTIM.x, 1)*sp.diff(u, FESTIM.x, 1)
        g = v_i*v - v_m * u * (n_trap-v)
        parameters = {
            "materials": [
                {
                    "alpha": alpha,  # lattice constant ()
                    "beta": beta,  # number of solute sites pe
                    "density": density,
                    "borders": [0, size],
                    "E_diff": E_diff,
                    "D_0": D_0,
                    "id": 1
                    }
                    ],
            "traps": [
                {
                    "energy": E_t,
                    "density": n_trap,
                    "materials": 1,
                    "source_term": g
                }
                ],
            "mesh_parameters": {
                    "initial_number_of_cells": round(size/h),
                    "size": size,
                    "refinements": [
                    ],
                },
            "boundary_conditions": [
                    {
                        "surface": [1, 2],
                        "value": u,
                        "component": 0,
                        "type": "dc"
                    },
                    {
                        "surface": [1, 2],
                        "value": v,
                        "component": 1,
                        "type": "dc"
                    }
                ],
            "temperature": {
                    'type': "expression",
                    'value': T
                },
            "source_term": {
                'value': f
                },
            "solving_parameters": {
                "newton_solver": {
                    "absolute_tolerance": 1e-10,
                    "relative_tolerance": 1e-9,
                    "maximum_iterations": 50,
                },
                "type": "solve_stationary"
                },
            "exports": {
                "txt": {
                    "functions": [],
                    "times": [],
                    "labels": [],
                    "folder": str(Path(d))
                },
                "xdmf": {
                    "functions": ['solute', '1', 'T'],
                    "labels":  ['solute', '1', 'temp'],
                    "folder": str(Path(d))
                },
                "error": [
                    {
                        "computed_solutions": [0, 1],
                        "exact_solutions": [u, v],
                        "norm": 'error_max',
                        "degree": 4
                    }
                ]
                },
        }
        return parameters

    tol_u = 1e-12
    tol_v = 1e-5
    sizes = [1/1600, 1/1700]
    for h in sizes:
        output = FESTIM.generic_simulation.run(
            parameters(h, u, v))
        error_max_u = output["error"][0][1]
        error_max_v = output["error"][0][2]
        msg = 'Maximum error on u is:' + str(error_max_u) + '\n \
            Maximum error on v is:' + str(error_max_v) + '\n \
            with h = ' + str(h)
        print(msg)
        assert error_max_u < tol_u and error_max_v < tol_v