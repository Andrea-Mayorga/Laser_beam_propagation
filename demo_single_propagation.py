"""
Student starting point: run one fixed optical configuration.

This script is not an optimizer. It saves target-plane plots and a multi-page
PDF of beam planes so the student can see what the model is doing.
"""
import matplotlib.pyplot as plt
from datetime import datetime

from beam_conditioning_core import (
    FieldGrid,
    thorlabs_AC254_030_A,
    thorlabs_AC254_050_A,
    thorlabs_AC127_050_A,
    thorlabs_AC127_025_A_ML,
    build_two_lens_common_focus_layout,
    build_system_from_layout,
    default_input_apertures,
    plot_intensity,
    plot_encircled_energy,
    save_plane_snapshots_pdf,
)
from student_common import OUTPUT_DIR, student_default_input_field, print_result_summary


def main():
        # Important numerical limitation:
    #
    # This code uses one fixed transverse grid for all planes. That means the same
    # dx and same field of view are used at the input apertures, lenses, focus plane,
    # pinhole plane, and target plane.
    #
    # This is simple, but it can be inefficient or inaccurate when the beam becomes
    # very small at a focus or when a small pinhole is inserted.
    #
    # Rule of thumb:
    #     pinhole_radius_mm should be at least ~20*dx for exploratory work
    #     and preferably ~50*dx for low-tail studies.
    #
    # For N=4096, size_mm=9:
    #     dx = 9/4096 = 0.0022 mm = 2.2 um
    #     20*dx = 44 um
    #     50*dx = 110 um
    #
    # Therefore, pinholes with radii of 10--25 um are not well resolved on this grid.
    # A future version should use zoom/resampled propagation near the focus.
    grid = FieldGrid(N=1024, size_mm=12.0, wavelength_mm=520e-6)

    #print(f"longitud de onda1 =  {grid.wavelength_mm}")

    lens1 = thorlabs_AC254_030_A()
    lens2 = thorlabs_AC254_050_A()
    lens3 = thorlabs_AC127_050_A()
    lens4 = thorlabs_AC127_025_A_ML()
    U0 = student_default_input_field(grid)
    input_apertures = default_input_apertures()

    layout = build_two_lens_common_focus_layout(
        lens1=lens2,
        lens2=lens1,
        lens1_V1_z_mm=40.0,
        pinhole_z_offset_mm=0.0,
        lens2_z_offset_mm=0.0,
    )

    system = build_system_from_layout(
        grid=grid,
        layout=layout,
        input_apertures=input_apertures,
        pinhole_radius_mm=None,
        downstream_apertures=[],
        z_target_mm=1000.0,
        target_radius_mm=1.5,
    )

### Inicio de la moficicacion de Andrea 11 de Junio
#     
    # =====================================================
    # Create unique output directory for this simulation
    # =====================================================

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    run_name = (
        f"{timestamp}"
        #f"_lam{grid.wavelength_mm*1e6:.0f}nm"
        f"N{grid.N}"
        f"_gr.size{grid.size_mm}"
    )

    run_dir = OUTPUT_DIR / run_name
    run_dir.mkdir(parents=True, exist_ok=True)

### Fin de la modificacion Andrea 11 de Junio

#Inicio de la 2da modificacion Andrea 11 de Junio:

    result = system.propagate(U0, capture_planes=True)

    # =====================================================
    # Save simulation parameters
    # =====================================================

    with open(run_dir / "parameters.txt", "w") as f:
        f.write("SIMULATION PARAMETERS\n")
        #f.write(f"SIMULATION PARAMETERS - {run_dir}\n")
        f.write("=====================\n\n")

        f.write(f"Wavelength [nm] = {grid.wavelength_mm*1e6:.3f}\n")
        f.write(f"N = {grid.N}\n")
        f.write(f"Grid size [mm] = {grid.size_mm:.6f}\n")
        f.write(f"dx [mm] = {grid.dx:.8f}\n\n")

        f.write(f"Lens 1 = {layout.lens1.name}\n")
        f.write(f"Lens 2 = {layout.lens2.name}\n\n")

        #f.write(f"Lens 1 = {lens1.name}\n")
        #f.write(f"Lens 2 = {lens2.name}\n\n")

        f.write(f"EFL Lens1 [mm] = {layout.lens1_props['EFL']:.6f}\n")
        f.write(f"EFL Lens2 [mm] = {layout.lens2_props['EFL']:.6f}\n")

        f.write(f"Magnification = {layout.magnification:.6f}\n")
        f.write(f"Lens separation [mm] = {layout.lens_separation_mm:.6f}\n\n")

        f.write(f"Lens1 V1 z [mm] = {layout.lens1_V1_z_mm:.6f}\n")
        f.write(f"Lens2 V1 z [mm] = {layout.lens2_V1_z_mm:.6f}\n")
        f.write(f"Pinhole z [mm] = {layout.pinhole_z_mm:.6f}\n\n")

        f.write(f"Target z [mm] = {system.z_target_mm:.6f}\n")
        f.write(f"Target radius [mm] = {system.target_radius_mm:.6f}\n")

    # =====================================================
    # Save simulation results
    # =====================================================

    with open(run_dir / "results.txt", "w") as f:

        f.write("SIMULATION RESULTS\n")
        f.write("==================\n\n")

        f.write(f"Throughput = {result.throughput:.10f}\n")
        f.write(
            f"Fraction outside target = "
            f"{result.fraction_outside_target:.10e}\n"
        )
        f.write(
            f"RMS radius [mm] = "
            f"{result.rms_radius_mm:.10f}\n"

        #f.write("Spot diameter at z= 1m [mm] = "
        #f"{result.rms_radius_mm:.10f*2*np.sqrt(2)}\n"
        #)    
        )
#Fin de la 2da modificacion de Andrea 11 de Junio

    print("\nSingle fixed propagation")
    print("------------------------")
    print(f"Grid: N={grid.N}, size={grid.size_mm:.3f} mm, dx={grid.dx:.5f} mm")
    print(f"Wavelength = {grid.wavelength_mm*1e6:.1f} nm")
    print(f"L1 = {layout.lens1.name}, EFL = {layout.lens1_props['EFL']:.4f} mm")
    print(f"L2 = {layout.lens2.name}, EFL = {layout.lens2_props['EFL']:.4f} mm")
    print(f"Magnification f2/f1 = {layout.magnification:.4f}")
    print(f"Lens separation V3_1 to V1_2 = {layout.lens_separation_mm:.4f} mm")
    print(f"Common focus / optional pinhole z = {layout.pinhole_z_mm:.4f} mm")

    print("\nInput apertures:")
    for ap in input_apertures:
        print(f"    {ap.name}: z={ap.z_mm:.3f} mm, r={ap.radius_mm:.4f} mm")

    if len(input_apertures) >= 2:
        dz = input_apertures[1].z_mm - input_apertures[0].z_mm
        dr = input_apertures[1].radius_mm - input_apertures[0].radius_mm
        print(f"Approx. aperture-defined angular scale: dr/dz = {dr/dz:.3e} rad = {1e3*dr/dz:.3f} mrad")

    print()
    print_result_summary("fixed layout", result)

    print("\nElement log:")
    for line in result.log:
        print("  " + line)

    plot_intensity(
        result.U,
        grid,
        title="Single fixed propagation: target plane",
        target_radius_mm=1.5,
        savepath=str(run_dir / "single_target_plane.png"),
        #savepath=str(OUTPUT_DIR / "single_target_plane.png"), #Original savepath
    )

    plot_encircled_energy(
        result.U,
        grid,
        savepath=str(run_dir / "single_encircled_energy.png"),
        #savepath=str(OUTPUT_DIR / "single_encircled_energy.png"), #Original savepath
    )

    save_plane_snapshots_pdf(
        result,
        filename=str(run_dir / "single_beam_planes.pdf"),
        #filename=str(OUTPUT_DIR / "single_beam_planes.pdf"), #Original filename
        target_radius_mm=1.5,
    )

    plt.close("all")


if __name__ == "__main__":
    main()
