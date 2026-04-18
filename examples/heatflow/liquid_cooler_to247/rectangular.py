from __future__ import annotations

from py2femm.femm_problem import FemmProblem
from py2femm.general import LengthUnit
from py2femm.geometry import Geometry, Line, Node
from py2femm.heatflow import HeatFlowConvection, HeatFlowHeatFlux, HeatFlowMaterial

from .config import LiquidCoolerConfig, compute_h


def build_rectangular(cfg: LiquidCoolerConfig) -> FemmProblem:
    """Build 2D planar heat-flow model with rectangular milled channels."""
    problem = FemmProblem(out_file="liquid_cooler_rectangular.csv")
    problem.heat_problem(
        units=LengthUnit.MILLIMETERS,
        type="planar",
        precision=1e-8,
        depth=cfg.l_cp,
        minangle=30,
    )

    b_cp = cfg.b_cp
    h_cp = cfg.h_cp
    ch_w = cfg.ch_w
    ch_h = cfg.ch_h
    cy_ch = h_cp / 2

    geo = Geometry()

    # Cooler outer rectangle
    _add_rect(geo, 0.0, 0.0, b_cp, h_cp)

    # Rectangular channel voids (no block labels inside)
    channel_xs = [cfg.s_t / 2 + i * cfg.s_t for i in range(cfg.n_channels)]
    for cx in channel_xs:
        _add_rect(geo, cx - ch_w / 2, cy_ch - ch_h / 2, cx + ch_w / 2, cy_ch + ch_h / 2)

    # Device stacks above cooler
    for i, dev in enumerate(cfg.devices):
        xl = i * cfg.device_pitch
        xr = xl + dev.bp_w
        x_si_l = xl + (dev.bp_w - dev.a_si) / 2
        x_si_r = x_si_l + dev.a_si
        y_tt = h_cp + dev.d_tim
        y_ct = y_tt + dev.h_cu
        y_st = y_ct + dev.a_si
        _add_rect(geo, xl,     h_cp,  xr,     y_tt)
        _add_rect(geo, xl,     y_tt,  xr,     y_ct)
        _add_rect(geo, x_si_l, y_ct,  x_si_r, y_st)

    problem.create_geometry(geo)

    # Materials
    mat_al = HeatFlowMaterial(material_name="Aluminum", kx=160.0, ky=160.0, qv=0.0, kt=0.0)
    mat_si = HeatFlowMaterial(material_name="Silicon",  kx=130.0, ky=130.0, qv=0.0, kt=0.0)
    mat_cu = HeatFlowMaterial(material_name="Copper",   kx=385.0, ky=385.0, qv=0.0, kt=0.0)
    for mat in (mat_al, mat_si, mat_cu):
        problem.add_material(mat)

    # Al block label: below channel base, clear of all channel voids
    al_label_y = (h_cp / 2 - ch_h / 2) * 0.5
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
    dh_mm = 2 * ch_w * ch_h / (ch_w + ch_h)
    h_conv = compute_h(cfg, dh_mm=dh_mm)
    convection = HeatFlowConvection(name="CoolantConvection", Tinf=cfg.t_inlet, h=h_conv)
    convection.Tset = 0
    convection.qs = 0
    convection.beta = 0
    problem.add_boundary(convection)

    # Convection on all 4 walls of each rectangular channel
    for cx in channel_xs:
        xl_ch = cx - ch_w / 2
        xr_ch = cx + ch_w / 2
        yb_ch = cy_ch - ch_h / 2
        yt_ch = cy_ch + ch_h / 2
        for seg in [
            Line(Node(xl_ch, yb_ch), Node(xr_ch, yb_ch)),  # bottom
            Line(Node(xr_ch, yb_ch), Node(xr_ch, yt_ch)),  # right
            Line(Node(xr_ch, yt_ch), Node(xl_ch, yt_ch)),  # top
            Line(Node(xl_ch, yt_ch), Node(xl_ch, yb_ch)),  # left
        ]:
            problem.set_boundary_definition_segment(seg.selection_point(), convection, elementsize=0.5)

    # Heat flux per device
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

    problem.lua_script.append(f"ho_selectblock({b_cp / 2:.4f}, {al_label_y:.4f})")
    problem.lua_script.append("T_h_surface = ho_blockintegral(0)")
    problem.lua_script.append("ho_clearblock()")
    problem.lua_script.append('write(file_out, "T_h_surface = ", T_h_surface, "\\n")')

    return problem


def _add_rect(geo: Geometry, x0: float, y0: float, x1: float, y1: float) -> None:
    bl, br, tr, tl = Node(x0, y0), Node(x1, y0), Node(x1, y1), Node(x0, y1)
    geo.add_line(Line(bl, br))
    geo.add_line(Line(br, tr))
    geo.add_line(Line(tr, tl))
    geo.add_line(Line(tl, bl))
