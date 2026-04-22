from __future__ import annotations

from py2femm.femm_problem import FemmProblem
from py2femm.general import LengthUnit
from py2femm.geometry import Geometry, Line, Node
from py2femm.heatflow import HeatFlowConvection, HeatFlowHeatFlux, HeatFlowMaterial

from ._geometry import add_rect
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
    fin_w = cfg.fin_w
    cy_ch = h_cp / 2

    max_ch_w = cfg.s_t - fin_w
    if max_ch_w <= 0:
        raise ValueError(f"s_t ({cfg.s_t}) must be > fin_w ({fin_w})")
    if ch_w > max_ch_w:
        raise ValueError(
            f"ch_w ({ch_w}) exceeds available width {max_ch_w} (s_t - fin_w)"
        )

    geo = Geometry()

    # Cooler outer rectangle
    add_rect(geo, 0.0, 0.0, b_cp, h_cp)

    # Rectangular channel voids — filter to channels fully inside [0, b_cp]
    channel_xs = [
        cx
        for cx in (cfg.s_t / 2 + i * cfg.s_t for i in range(cfg.n_channels))
        if cx - ch_w / 2 >= 0.0 and cx + ch_w / 2 <= b_cp
    ]
    for cx in channel_xs:
        add_rect(geo, cx - ch_w / 2, cy_ch - ch_h / 2, cx + ch_w / 2, cy_ch + ch_h / 2)

    # Device stacks above cooler
    for i, dev in enumerate(cfg.devices):
        xl = i * cfg.device_pitch
        xr = xl + dev.bp_w
        x_si_l = xl + (dev.bp_w - dev.a_si) / 2
        x_si_r = x_si_l + dev.a_si
        y_tt = h_cp + dev.d_tim
        y_ct = y_tt + dev.h_cu
        y_st = y_ct + dev.a_si
        add_rect(geo, xl,     h_cp,  xr,     y_tt)
        add_rect(geo, xl,     y_tt,  xr,     y_ct)
        add_rect(geo, x_si_l, y_ct,  x_si_r, y_st)

    problem.create_geometry(geo)

    # Materials
    mat_al    = HeatFlowMaterial(material_name="Aluminum", kx=160.0, ky=160.0, qv=0.0, kt=0.0)
    mat_si    = HeatFlowMaterial(material_name="Silicon",  kx=130.0, ky=130.0, qv=0.0, kt=0.0)
    mat_cu    = HeatFlowMaterial(material_name="Copper",   kx=385.0, ky=385.0, qv=0.0, kt=0.0)
    mat_fluid = HeatFlowMaterial(material_name="Coolant",  kx=0.6,   ky=0.6,   qv=0.0, kt=0.0)
    for mat in (mat_al, mat_si, mat_cu, mat_fluid):
        problem.add_material(mat)

    # Al block label: below channel base, clear of all channel voids
    al_label_y = (h_cp / 2 - ch_h / 2) * 0.5
    problem.define_block_label(Node(cfg.s_t * 0.1, al_label_y), mat_al)

    # Coolant label at the centre of each rectangular channel
    for cx in channel_xs:
        problem.define_block_label(Node(cx, cy_ch), mat_fluid)

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
    h_conv = compute_h(cfg, dh_mm=dh_mm, area_mm2=ch_w * ch_h)
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

    problem.lua_script.append(f"ho_selectblock({cfg.s_t * 0.1:.4f}, {al_label_y:.4f})")
    problem.lua_script.append("T_h_surface = ho_blockintegral(0)")
    problem.lua_script.append("ho_clearblock()")
    problem.lua_script.append('write(file_out, "T_h_surface = ", T_h_surface, "\\n")')

    # Temperature grid dump (bitmap requires visible window — grid works headless)
    from .circular import _emit_temperature_grid
    y_top = h_cp + max(d.d_tim + d.h_cu + d.a_si for d in cfg.devices)
    _emit_temperature_grid(problem, x_min=0.0, x_max=b_cp,
                           y_min=0.0, y_max=y_top, nx=40, ny=20)

    problem.close()
    return problem
