#!/usr/bin/env python3
"""
Customizable single propagation script.

Allows you to change grid parameters, lenses, and other settings easily.
"""

import matplotlib.pyplot as plt
import numpy as np

from pathlib import Path

from beam_conditioning_core import (
    FieldGrid,
    thorlabs_AC254_030_A,
    thorlabs_AC254_050_A,
    CementedDoublet,
    build_two_lens_common_focus_layout,
    build_system_from_layout,
    default_input_apertures,
    plot_intensity,
    plot_encircled_energy,
    save_plane_snapshots_pdf,
    elliptical_gaussian_field,
    gaussian_field,
    top_hat_field,
    dirty_gaussian_field,
)

# ============================================================================
# CONFIGURATION - CHANGE THESE VALUES AS NEEDED
# ============================================================================

# Grid parameters
N = 2048                    # Grid points (power of 2 is best: 512, 1024, 2048, 4096)
grid_size_mm = 12.0         # Field of view in mm
wavelength_nm = 520         # Wavelength in nm (405, 520, 633, etc.)

# Lens configuration
# Option 1: Use predefined lenses
USE_LENS1_NAME = "AC254-050-A-ML"  # "AC254-030-A" or "AC254-050-A-ML"
USE_LENS2_NAME = "AC254-030-A"      # "AC254-030-A" or "AC254-050-A-ML"

# Option 2: Or create custom lenses (uncomment and fill)
# CUSTOM_LENS1 = CementedDoublet(
#     R1=20.89, R2=-16.73, R3=-79.80,
#     n1=1.67003, n2=1.80518,
#     t12=12.0, t23=2.0,
#     aperture_radius=12.7,
#     name="my_custom_lens_1"
# )
# CUSTOM_LENS2 = CementedDoublet(...)

# Input beam configuration
INPUT_BEAM_TYPE = "elliptical_gaussian"  # "gaussian", "elliptical_gaussian", "top_hat", "dirty_gaussian"

# Gaussian parameters (for gaussian and elliptical_gaussian)
WAIST_RADIUS_MM = 0.35      # For circular Gaussian
WX_MM = 0.15                # For elliptical Gaussian (X direction)
WY_MM = 0.50                # For elliptical Gaussian (Y direction)
TILT_X_MRAD = 0.2           # Tilt in mrad
TILT_Y_MRAD = 0.0

# Top-hat parameters (for top_hat)
TOP_HAT_RADIUS_MM = 0.50

# Dirty Gaussian parameters (for dirty_gaussian)
DIRTY_AMPLITUDE_NOISE = 0.10
DIRTY_PHASE_NOISE_RAD = 0.25
DIRTY_SEED = 1

# Layout parameters
LENS1_V1_Z_MM = 40.0        # Position of lens 1 vertex 1
PINHOLE_Z_OFFSET_MM = 0.0   # Offset from nominal focus
LENS2_Z_OFFSET_MM = 0.0     # Offset of lens 2 from nominal position

# Pinhole configuration
PINHOLE_RADIUS_MM = None     # Set to a float (e.g., 0.050) to enable, None to disable

# Downstream apertures (after lens 2)
DOWNSTREAM_APERTURE_RADIUS_MM = None  # Set to a float to enable, None to disable
DOWNSTREAM_APERTURES_COUNT = 5        # Number of apertures (0 for none)

# Target parameters
Z_TARGET_MM = 1000.0        # Distance to target plane
TARGET_RADIUS_MM = 1.5      # Radius of target (diameter = 3 mm)

# Output
OUTPUT_DIR = Path("output_custom")
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================================
# END OF CONFIGURATION
# ============================================================================


def get_lens_by_name(name: str) -> CementedDoublet:
    """Get a predefined lens by name."""
    lenses = {
        "AC254-030-A": thorlabs_AC254_030_A(),
        "AC254-050-A-ML": thorlabs_AC254_050_A(),
    }
    if name not in lenses:
        raise ValueError(f"Unknown lens: {name}. Available: {list(lenses.keys())}")
    return lenses[name]


def create_input_field(grid: FieldGrid) -> np.ndarray:
    """Create the input field based on configuration."""
    if INPUT_BEAM_TYPE == "gaussian":
        return gaussian_field(
            grid,
            waist_radius_mm=WAIST_RADIUS_MM,
            tilt_x_mrad=TILT_X_MRAD,
            tilt_y_mrad=TILT_Y_MRAD,
        )
    elif INPUT_BEAM_TYPE == "elliptical_gaussian":
        return elliptical_gaussian_field(
            grid,
            wx_mm=WX_MM,
            wy_mm=WY_MM,
            tilt_x_mrad=TILT_X_MRAD,
            tilt_y_mrad=TILT_Y_MRAD,
        )
    elif INPUT_BEAM_TYPE == "top_hat":
        return top_hat_field(
            grid,
            radius_mm=TOP_HAT_RADIUS_MM,
            tilt_x_mrad=TILT_X_MRAD,
        )
    elif INPUT_BEAM_TYPE == "dirty_gaussian":
        return dirty_gaussian_field(
            grid,
            waist_radius_mm=WAIST_RADIUS_MM,
            amplitude_noise=DIRTY_AMPLITUDE_NOISE,
            phase_noise_rad=DIRTY_PHASE_NOISE_RAD,
            seed=DIRTY_SEED,
        )
    else:
        raise ValueError(f"Unknown beam type: {INPUT_BEAM_TYPE}")


def main():
    # Create grid
    wavelength_mm = wavelength_nm * 1e-6
    grid = FieldGrid(N=N, size_mm=grid_size_mm, wavelength_mm=wavelength_mm)

    # Get lenses
    lens1 = get_lens_by_name(USE_LENS1_NAME)
    lens2 = get_lens_by_name(USE_LENS2_NAME)

    print("\n" + "=" * 60)
    print("CUSTOM SINGLE PROPAGATION")
    print("=" * 60)
    print(f"\nGrid: {N} x {N}, size={grid_size_mm} mm, dx={grid.dx:.5f} mm")
    print(f"Wavelength: {wavelength_nm} nm")
    print(f"\nLens 1: {lens1.name} (EFL = {lens1.properties()['EFL']:.2f} mm)")
    print(f"Lens 2: {lens2.name} (EFL = {lens2.properties()['EFL']:.2f} mm)")
    print(f"Magnification: {lens2.properties()['EFL'] / lens1.properties()['EFL']:.3f}")
    print(f"\nInput beam: {INPUT_BEAM_TYPE}")

    # Create input field
    U0 = create_input_field(grid)
    input_apertures = default_input_apertures()

    # Build layout
    layout = build_two_lens_common_focus_layout(
        lens1=lens1,
        lens2=lens2,
        lens1_V1_z_mm=LENS1_V1_Z_MM,
        pinhole_z_offset_mm=PINHOLE_Z_OFFSET_MM,
        lens2_z_offset_mm=LENS2_Z_OFFSET_MM,
    )

    # Create downstream apertures if enabled
    downstream_apertures = []
    if DOWNSTREAM_APERTURE_RADIUS_MM is not None and DOWNSTREAM_APERTURES_COUNT > 0:
        from beam_conditioning_core import make_regular_downstream_apertures
        downstream_apertures = make_regular_downstream_apertures(
            z_start_mm=layout.lens2_V3_z_mm + 10.0,
            z_stop_mm=Z_TARGET_MM - 10.0,
            spacing_mm=Z_TARGET_MM / (DOWNSTREAM_APERTURES_COUNT + 1),
            radius_mm=DOWNSTREAM_APERTURE_RADIUS_MM,
            name_prefix="downstream",
        )

    # Build system
    system = build_system_from_layout(
        grid=grid,
        layout=layout,
        input_apertures=input_apertures,
        pinhole_radius_mm=PINHOLE_RADIUS_MM,
        downstream_apertures=downstream_apertures,
        z_target_mm=Z_TARGET_MM,
        target_radius_mm=TARGET_RADIUS_MM,
    )

    # Propagate
    print("\nPropagating...")
    result = system.propagate(U0, capture_planes=True)

    # Print results
    print("\n" + "-" * 40)
    print("RESULTS")
    print("-" * 40)
    print(f"Throughput: {result.throughput:.6f} ({result.throughput*100:.2f}%)")
    print(f"Fraction outside {TARGET_RADIUS_MM} mm radius: {result.fraction_outside_target:.3e}")
    print(f"Inside target: {(1.0 - result.fraction_outside_target)*100:.5f}%")
    print(f"RMS radius at target: {result.rms_radius_mm:.4f} mm")
    print(f"Input power: {result.input_power:.3e}")
    print(f"Output power: {result.output_power:.3e}")

    print("\nElement log:")
    for line in result.log:
        print(f"  {line}")

    # Save plots
    print("\nSaving plots...")
    plot_intensity(
        result.U,
        grid,
        title=f"Target plane at z={Z_TARGET_MM} mm\n{lens1.name} → {lens2.name}",
        target_radius_mm=TARGET_RADIUS_MM,
        throughput=result.throughput,
        savepath=str(OUTPUT_DIR / "target_plane_intensity.png"),
    )

    plot_encircled_energy(
        result.U,
        grid,
        savepath=str(OUTPUT_DIR / "encircled_energy.png"),
    )

    save_plane_snapshots_pdf(
        result,
        filename=str(OUTPUT_DIR / "beam_planes.pdf"),
        target_radius_mm=TARGET_RADIUS_MM,
    )

    print(f"\nOutput saved to: {OUTPUT_DIR}")
    print("=" * 60)

    # Optionally show plots
    plt.show()


if __name__ == "__main__":
    main()