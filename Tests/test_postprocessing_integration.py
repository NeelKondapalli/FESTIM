import FESTIM
import fenics
import pytest
import sympy as sp
import numpy as np
from pathlib import Path


def test_run_post_processing(tmpdir):
    '''
    Test the integration of post processing functions.
    Check the derived quantities table sizes, and the value
    of t
    '''
    d = tmpdir.mkdir("Solution_Test")
    parameters = {
        "materials": [{
                "borders": [0, 0.5],
                "E_diff": 4,
                "D_0": 5,
                "id": 1
                },
                {
                "borders": [0.5, 1],
                "E_diff": 5,
                "D_0": 6,
                "id": 2
                }],
        "traps": [{}, {}],
        "exports": {
            "xdmf": {
                    "functions": ['solute', 'T'],
                    "labels":  ['solute', 'temperature'],
                    "folder": str(Path(d))
            },
            "derived_quantities": {
                "surface_flux": [
                    {
                        "field": 'solute',
                        "surfaces": [2]
                    },
                    {
                        "field": 'T',
                        "surfaces": [2]
                    },
                ],
                "average_volume": [
                    {
                        "field": 1,
                        "volumes": [1]
                    }
                ],
                "total_volume": [
                    {
                        "field": 'solute',
                        "volumes": [1, 2]
                    }
                ],
                "total_surface": [
                    {
                        "field": 1,
                        "surfaces": [2]
                    }
                ],
                "maximum_volume": [
                    {
                        "field": 'T',
                        "volumes": [1]
                    }
                ],
                "minimum_volume": [
                    {
                        "field": 'solute',
                        "volumes": [2]
                    }
                ],
                "file": "derived_quantities",
                "folder": str(Path(d)),
                },
                }
    }

    mesh = fenics.UnitIntervalMesh(20)
    V = fenics.VectorFunctionSpace(mesh, 'P', 1, 2)
    W = fenics.FunctionSpace(mesh, 'P', 1)
    u = fenics.Function(V)
    T = fenics.Function(W)

    volume_markers, surface_markers = \
        FESTIM.meshing.subdomains_1D(mesh, parameters["materials"], size=1)

    t = 0
    dt = 1
    transient = True
    append = True
    markers = [volume_markers, surface_markers]

    files = FESTIM.export.define_xdmf_files(parameters["exports"])
    tab = \
        [FESTIM.post_processing.header_derived_quantities(parameters)]
    flux_fonctions = \
        FESTIM.post_processing.create_flux_functions(
            mesh, parameters["materials"], volume_markers)
    for i in range(1, 3):
        t += dt
        derived_quantities_global, dt = \
            FESTIM.post_processing.run_post_processing(
                parameters, transient, u, T, markers, W, t, dt, files,
                append=append, flux_fonctions=flux_fonctions,
                derived_quantities_global=tab)
        append = True
    assert len(derived_quantities_global) == i + 1
    assert derived_quantities_global[i][0] == t


def test_run_post_processing_pure_diffusion(tmpdir):
    '''
    Test the integration of post processing functions.
    In the pure diffusion case
    '''
    d = tmpdir.mkdir("Solution_Test")
    parameters = {
        "materials": [{
                "borders": [0, 0.5],
                "E_diff": 4,
                "D_0": 5,
                "id": 1
                },
                {
                "borders": [0.5, 1],
                "E_diff": 5,
                "D_0": 6,
                "id": 2
                }],
        "traps": [],
        "exports": {
            "xdmf": {
                    "functions": ['solute', 'T'],
                    "labels":  ['solute', 'temperature'],
                    "folder": str(Path(d))
                    },
            "derived_quantities": {
                "average_volume": [
                    {
                        "field": 'solute',
                        "volumes": [2]
                    },
                    {
                        "field": 'T',
                        "volumes": [2]
                    },
                    {
                        "field": 'retention',
                        "volumes": [2]
                    },
                    ],
                "file": "derived_quantities",
                "folder": str(Path(d)),
                },
            }
        }

    mesh = fenics.UnitIntervalMesh(20)
    V = fenics.FunctionSpace(mesh, 'P', 1)
    u = fenics.interpolate(fenics.Constant(10), V)
    T = fenics.interpolate(fenics.Constant(20), V)

    volume_markers, surface_markers = \
        FESTIM.meshing.subdomains_1D(mesh, parameters["materials"], size=1)

    t = 0
    dt = 1
    transient = True
    append = True
    markers = [volume_markers, surface_markers]

    files = FESTIM.export.define_xdmf_files(parameters["exports"])
    tab = \
        [FESTIM.post_processing.header_derived_quantities(parameters)]
    flux_fonctions = \
        FESTIM.post_processing.create_flux_functions(
            mesh, parameters["materials"], volume_markers)
    for i in range(1, 3):
        t += dt
        derived_quantities_global, dt = \
            FESTIM.post_processing.run_post_processing(
                parameters, transient, u, T, markers, V, t, dt, files,
                append=append, flux_fonctions=flux_fonctions,
                derived_quantities_global=tab)
        append = True
        assert len(derived_quantities_global) == i + 1
        assert derived_quantities_global[i][0] == t
        assert derived_quantities_global[i][1] == 10
        assert derived_quantities_global[i][2] == 20
        assert round(derived_quantities_global[i][3]) == 10


def test_run_post_processing_flux(tmpdir):
    '''
    Test run_post_processing() quantitatively
    '''
    d = tmpdir.mkdir("Solution_Test")
    parameters = {
        "materials": [{
                "borders": [0, 0.5],
                "E_diff": 0.4,
                "D_0": 5,
                "thermal_cond": 3,
                "id": 1
                },
                {
                "borders": [0.5, 1],
                "E_diff": 0.5,
                "D_0": 6,
                "thermal_cond": 5,
                "id": 2
                }],
        "traps": [],
        "exports": {
            "derived_quantities": {
                "surface_flux": [
                    {
                        "field": 'solute',
                        "surfaces": [1, 2]
                    },
                    {
                        "field": 'T',
                        "surfaces": [1, 2]
                    }
                    ],
                "file": "derived_quantities",
                "folder": str(Path(d)),
                },
            }
        }

    mesh = fenics.UnitIntervalMesh(20)
    V = fenics.FunctionSpace(mesh, 'P', 1)
    u = fenics.Expression('2*x[0]', degree=1)
    u = fenics.interpolate(u, V)
    T = fenics.Expression('100*x[0] + 200', degree=1)
    T = fenics.interpolate(T, V)

    volume_markers, surface_markers = \
        FESTIM.meshing.subdomains_1D(mesh, parameters["materials"], size=1)

    t = 0
    dt = 1
    transient = True
    append = True
    markers = [volume_markers, surface_markers]

    # files = FESTIM.export.define_xdmf_files(parameters["exports"])
    tab = [FESTIM.post_processing.header_derived_quantities(parameters)]
    flux_fonctions = \
        FESTIM.post_processing.create_flux_functions(
            mesh, parameters["materials"], volume_markers)
    t += dt
    derived_quantities_global, dt = \
        FESTIM.post_processing.run_post_processing(
            parameters, transient, u, T, markers, V, t, dt, None,
            append=append, flux_fonctions=flux_fonctions,
            derived_quantities_global=tab)
    print(derived_quantities_global[0])
    print(derived_quantities_global[1])
    assert np.isclose(derived_quantities_global[1][1], -1*2*5*fenics.exp(-0.4/FESTIM.k_B/T(0)))
    assert np.isclose(derived_quantities_global[1][2], -1*-2*6*fenics.exp(-0.5/FESTIM.k_B/T(1)))
    assert np.isclose(derived_quantities_global[1][3], -1*100*3)
    assert np.isclose(derived_quantities_global[1][4], -1*-100*5)