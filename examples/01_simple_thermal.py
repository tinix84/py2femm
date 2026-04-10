"""Example: Submit a pre-built Lua script to py2femm agent.

Usage:
    # From WSL with agent running on Windows:
    python examples/01_simple_thermal.py

    # Or with explicit mode:
    PYFEMM_AGENT_URL=http://localhost:8082 python examples/01_simple_thermal.py
"""

from py2femm.client import FemmClient
from py2femm.client.models import JobResult

# A minimal FEMM heat flow Lua script
LUA_SCRIPT = """\
showconsole()
newdocument(2)
hi_probdef("meters", "planar", 1e-8, 0, 30)

-- Simple aluminum block 50mm x 10mm
hi_addnode(0, 0)
hi_addnode(0.05, 0)
hi_addnode(0.05, 0.01)
hi_addnode(0, 0.01)
hi_addsegment(0, 0, 0.05, 0)
hi_addsegment(0.05, 0, 0.05, 0.01)
hi_addsegment(0.05, 0.01, 0, 0.01)
hi_addsegment(0, 0.01, 0, 0)

-- Material: aluminum (k=200 W/mK)
hi_addmaterial("aluminum", 200, 200, 0)
hi_addblocklabel(0.025, 0.005)
hi_selectlabel(0.025, 0.005)
hi_setblockprop("aluminum", 1, 0, 0)
hi_clearselected()

-- BC: heat flux on bottom (5000 W/m2), convection on top (h=50, T=300K)
hi_addboundprop("source", 1, 0, 5000)
hi_addboundprop("cooling", 2, 0, 0, 300, 50)

hi_selectsegment(0.025, 0)
hi_setsegmentprop("source", 0, 1, 0, 0, "")
hi_clearselected()

hi_selectsegment(0.025, 0.01)
hi_setsegmentprop("cooling", 0, 1, 0, 0, "")
hi_clearselected()

-- Solve
hi_analyze()
hi_loadsolution()

-- Extract results
if py2femm_outfile then
    outfile = openfile(py2femm_outfile, "w")
else
    outfile = openfile("results.csv", "w")
end
write(outfile, "point,x,y,temperature_K\\n")
T1 = ho_getpointvalues(0.025, 0)
write(outfile, string.format("base_center,0.025,0,%.4f\\n", T1[1]))
T2 = ho_getpointvalues(0.025, 0.01)
write(outfile, string.format("top_center,0.025,0.01,%.4f\\n", T2[1]))
closefile(outfile)
"""


def main():
    print("Connecting to py2femm agent...")
    try:
        client = FemmClient()
    except ConnectionError as e:
        print(f"Error: {e}")
        print("\nMake sure the py2femm agent is running on Windows.")
        print("  1. Run setup_femm.bat (one-time)")
        print("  2. Run start_femm_agent.bat")
        return

    print(f"Agent mode: {client._mode}")
    print("Submitting Lua script...")

    result = client.run(LUA_SCRIPT, timeout=120)

    if result.error:
        print(f"Error: {result.error}")
        return

    print(f"Completed in {result.elapsed_s:.1f}s")
    print()

    # Parse results
    job_result = JobResult(csv_data=result.csv_data)
    df = job_result.to_dataframe()
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
