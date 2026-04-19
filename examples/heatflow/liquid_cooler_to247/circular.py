from __future__ import annotations

from py2femm.femm_problem import FemmProblem
from py2femm.general import LengthUnit
from py2femm.geometry import CircleArc, Geometry, Line, Node
from py2femm.heatflow import HeatFlowConvection, HeatFlowHeatFlux, HeatFlowMaterial

from ._geometry import add_rect
from .config import LiquidCoolerConfig, compute_h


def build_circular(cfg: LiquidCoolerConfig) -> FemmProblem:
    """Build 2D planar heat-flow model with circular drilled channels (Waffler §4.4.2)."""
    problem = FemmProblem(out_file="liquid_cooler_circular.csv")
    problem.heat_problem(
        units=LengthUnit.MILLIMETERS,
        type="planar",
        precision=1e-8,
        depth=cfg.l_cp,
        minangle=30,
    )

    b_cp = cfg.b_cp
    h_cp = cfg.h_cp
    r = cfg.d_t / 2
    cy_ch = h_cp / 2

    geo = Geometry()

    # Cooler outer rectangle
    add_rect(geo, 0.0, 0.0, b_cp, h_cp)

    # Circular channels: two 180° arcs per channel form a complete circle void
    channel_xs = [cfg.s_t / 2 + i * cfg.s_t for i in range(cfg.n_channels)]
    for cx in channel_xs:
        top_n = Node(cx, cy_ch + r)
        bot_n = Node(cx, cy_ch - r)
        ctr_n = Node(cx, cy_ch)
        geo.add_arc(CircleArc(top_n, ctr_n, bot_n))  # right half
        geo.add_arc(CircleArc(bot_n, ctr_n, top_n))  # left half

    # Device stacks above cooler
    for i, dev in enumerate(cfg.devices):
        xl = i * cfg.device_pitch
        xr = xl + dev.bp_w
        x_si_l = xl + (dev.bp_w - dev.a_si) / 2
        x_si_r = x_si_l + dev.a_si
        y_tt = h_cp + dev.d_tim
        y_ct = y_tt + dev.h_cu
        y_st = y_ct + dev.a_si
        add_rect(geo, xl,    h_cp,  xr,    y_tt)   # TIM
        add_rect(geo, xl,    y_tt,  xr,    y_ct)   # Cu baseplate
        add_rect(geo, x_si_l, y_ct, x_si_r, y_st)  # Si die

    problem.create_geometry(geo)

    # Materials
    mat_al = HeatFlowMaterial(material_name="Aluminum", kx=160.0, ky=160.0, qv=0.0, kt=0.0)
    mat_si = HeatFlowMaterial(material_name="Silicon",  kx=130.0, ky=130.0, qv=0.0, kt=0.0)
    mat_cu = HeatFlowMaterial(material_name="Copper",   kx=385.0, ky=385.0, qv=0.0, kt=0.0)
    for mat in (mat_al, mat_si, mat_cu):
        problem.add_material(mat)

    # Al block label: halfway between bottom edge and channel base, clear of all channels
    al_label_y = (h_cp / 2 - r) * 0.5  # halfway between bottom and channel base
    problem.define_block_label(Node(cfg.s_t * 0.1, al_label_y), mat_al)

    for i, dev in enumerate(cfg.devices):
        xl = i * cfg.device_pitch
        xc = xl + dev.bp_w / 2
        mat_tim = HeatFlowMaterial(
            material_name=f"TIM_{i}", kx=dev.k_tim, ky=dev.k_tim, qv=0.0, kt=0.0
        )
        problem.add_material(mat_tim)
        y_tt = h_cp + dev.d_tim
        y_ct = y_tt + dev.h_cu
        problem.define_block_label(Node(xc, h_cp + dev.d_tim / 2),  mat_tim)
        problem.define_block_label(Node(xc, y_tt + dev.h_cu / 2),   mat_cu)
        problem.define_block_label(Node(xc, y_ct + dev.a_si / 2),   mat_si)

    # Boundary Conditions
    h_conv = compute_h(cfg)
    convection = HeatFlowConvection(name="CoolantConvection", Tinf=cfg.t_inlet, h=h_conv)
    convection.Tset = 0
    convection.qs = 0
    convection.beta = 0
    problem.add_boundary(convection)

    for i, dev in enumerate(cfg.devices):
        qs = -dev.p_loss / (dev.a_si * 1e-3 * cfg.l_cp * 1e-3)
        hf = HeatFlowHeatFlux(name=f"HeatFlux_{i}", qs=qs)
        hf.Tset = 0
        hf.Tinf = 0
        hf.h = 0
        hf.beta = 0
        problem.add_boundary(hf)
        xl_si = i * cfg.device_pitch + (dev.bp_w - dev.a_si) / 2
        xr_si = xl_si + dev.a_si
        y_st = h_cp + dev.d_tim + dev.h_cu + dev.a_si
        seg = Line(Node(xl_si, y_st), Node(xr_si, y_st))
        problem.set_boundary_definition_segment(seg.selection_point(), hf, elementsize=0.5)

    # Assign convection to circular channel walls via raw Lua
    # (set_arc_segment_prop has no heat flow case in femm_problem.py)
    for cx in channel_xs:
        for sel_x in (cx + r * 0.999, cx - r * 0.999):
            problem.lua_script.append(f"hi_selectarcsegment({sel_x:.6f}, {cy_ch:.6f})")
            problem.lua_script.append(f"hi_setarcsegmentprop(1, '{convection.name}', 0, 0)")
            problem.lua_script.append("hi_clearselected()")

    # Analysis
    problem.make_analysis("planar")

    # Post-processing
    for i, dev in enumerate(cfg.devices):
        xl = i * cfg.device_pitch
        xc = xl + dev.bp_w / 2
        y_st = h_cp + dev.d_tim + dev.h_cu + dev.a_si
        y_j    = y_st - dev.a_si * 0.1
        y_case = h_cp + dev.d_tim + dev.h_cu * 0.9

        problem.lua_script.append(f"T_j_{i} = ho_getpointvalues({xc:.4f}, {y_j:.4f})")
        problem.lua_script.append(f'write(file_out, "T_j_{i} = ", T_j_{i}, "\\n")')
        problem.lua_script.append(f"T_case_{i} = ho_getpointvalues({xc:.4f}, {y_case:.4f})")
        problem.lua_script.append(f'write(file_out, "T_case_{i} = ", T_case_{i}, "\\n")')

    problem.lua_script.append(f"ho_selectblock({cfg.s_t * 0.1:.4f}, {al_label_y:.4f})")
    problem.lua_script.append("T_h_surface = ho_blockintegral(0)")
    problem.lua_script.append("ho_clearblock()")
    problem.lua_script.append('write(file_out, "T_h_surface = ", T_h_surface, "\\n")')

    return problem
