# -*- coding: utf-8 -*-
"""try_PSD_plot.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1CHlv06w5ai4k5sSoHiCbVgJMSoabvRdc

This code is generating the power spectra density like Weatherbench2 webpage
Weatherbench2 PSD plot:https://sites.research.google/weatherbench/spectra/
        
PSD code by Weatherbench2:https://github.com/google-research/weatherbench2/blob/main/scripts/compute_zonal_energy_spectrum.py
"""

import os
import numpy as np
import pandas as pd
import xarray as xr
import dask.array as da
import datetime as dt
from dask.distributed import Client
from dask_jobqueue import SLURMCluster
import panel as pn
import hvplot.xarray
import cartopy.crs as ccrs
import matplotlib.pyplot as plt

# Generate a synthetic dataset: Dimensions (lat=180, lon=360, time=10)
lat = np.linspace(-90, 90, 180)
lon = np.linspace(0, 360, 360)
time = np.arange(10)
data = np.random.rand(len(lat), len(lon), len(time))  # Random data

# Create an xarray DataArray
da = xr.DataArray(data, coords={"lat": lat, "lon": lon, "time": time}, dims=["lat", "lon", "time"])
da

def compute_zonal_energy_spectrum(da):
    # Restrict latitudes to 30 < |lat| < 60
    lat_mask = (da["lat"] > 30) | (da["lat"] < -30)
    lat_mask &= (da["lat"] < 60) & (da["lat"] > -60)
    da = da.sel(lat=lat_mask)

    # Get longitude spacing and circumference (approximation)
    lon_spacing = 360 / da.sizes["lon"]
    circumference = 2 * np.pi * 6371e3 * np.cos(np.radians(da["lat"]))  # Earth's radius = 6371 km

    # Compute DFT along longitude (zonal)
    dft = np.fft.fft(da, axis=1) / da.sizes["lon"]  # Normalize by L
    dft_amplitude = np.abs(dft)  # Amplitude of Fourier coefficients

    # Compute energy spectrum (S_k)
    energy_spectrum = 2 * (dft_amplitude ** 2)  # Factor of 2 for k > 0
    energy_spectrum[..., 0] /= 2  # For k=0, no doubling
    energy_spectrum = energy_spectrum[..., : da.sizes["lon"] // 2]  # Keep k = 0 to L/2

    # Align circumference_da to match energy_spectrum dimensions
    circumference_da = xr.DataArray(
        circumference, dims=["lat"], coords={"lat": da["lat"]}
    )
    # Expand the circumference to match energy_spectrum dimensions
    circumference_da_expanded = circumference_da.broadcast_like(
        da.isel(lon=slice(0, energy_spectrum.shape[1]))
    )

    # Scale the energy spectrum with the circumference
    scaled_spectrum = energy_spectrum * circumference_da_expanded
    psd_mean = scaled_spectrum.mean(dim="lat")  # Average across selected latitudes

    return psd_mean

# Apply the function to calculate PSD
psd = compute_zonal_energy_spectrum(da)

psd

# Time-averaged PSD
#psd_time_avg = psd.mean(dim="time")
psd_time_avg = psd.sel(time=1)

# Plot the Power Spectral Density (PSD) in WeatherBench2 style
plt.figure(figsize=(12, 8))
plt.loglog(wavenumbers, psd_time_avg, label="PSD (Time-averaged)", linewidth=2, color="blue")

# Customize the plot
plt.xlabel("Wavenumber", fontsize=14)
plt.ylabel("Power Spectral Density", fontsize=14)
plt.title("Zonal Energy Spectrum (30° < |lat| < 60°)", fontsize=16, pad=15)
plt.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.7)
plt.tick_params(axis="both", which="major", labelsize=12)
plt.legend(fontsize=12, loc="upper right")
plt.tight_layout()

# Show the plot
plt.show()

"""Try with real data"""

dirpath = '/fs/scratch/PYS0343/luisvela/FP_data/ops/data/output/20241213/00'
filename = 'spire-ai.20241213.00z.global.ens_members.0450.nc'
filepath = os.path.join(dirpath, filename)
print('Opening File at:', filepath)

# Load
ds = xr.open_dataset(filepath, engine='h5netcdf').compute()
z500=ds.z.isel(ensemble_member=1,pressure_level=1)

z500

def compute_zonal_energy_spectrum1(da):
    # Restrict latitudes to 30 < |lat| < 60
    lat_mask = (da["latitude"] > 30) | (da["latitude"] < -30)
    lat_mask &= (da["latitude"] < 60) & (da["latitude"] > -60)
    da = da.sel(latitude=lat_mask)

    # Get longitude spacing and circumference (approximation)
    lon_spacing = 360 / da.sizes["longitude"]
    circumference = 2 * np.pi * 6371e3 * np.cos(np.radians(da["latitude"]))  # Earth's radius = 6371 km

    # Compute DFT along longitude (zonal)
    dft = np.fft.fft(da, axis=1) / da.sizes["longitude"]  # Normalize by L
    dft_amplitude = np.abs(dft)  # Amplitude of Fourier coefficients

    # Compute energy spectrum (S_k)
    energy_spectrum = 2 * (dft_amplitude ** 2)  # Factor of 2 for k > 0
    energy_spectrum[..., 0] /= 2  # For k=0, no doubling
    energy_spectrum = energy_spectrum[..., : da.sizes["longitude"] // 2]  # Keep k = 0 to L/2

    # Align circumference_da to match energy_spectrum dimensions
    circumference_da = xr.DataArray(
        circumference, dims=["latitude"], coords={"latitude": da["latitude"]}
    )
    # Expand the circumference to match energy_spectrum dimensions
    circumference_da_expanded = circumference_da.broadcast_like(
        da.isel(longitude=slice(0, energy_spectrum.shape[1]))
    )

    # Scale the energy spectrum with the circumference
    scaled_spectrum = energy_spectrum * circumference_da_expanded
    psd_mean = scaled_spectrum.mean(dim="latitude")  # Average across selected latitudes

    return psd_mean

psd1 = compute_zonal_energy_spectrum1(z500)

psd1

psd = psd1
#wavenumbers = np.arange(psd.sizes["longitude"] // 2)
wavenumbers = np.arange(psd.sizes["longitude"])
# Plot the Power Spectral Density (PSD) in WeatherBench2 style
plt.figure(figsize=(12, 8))
plt.loglog(wavenumbers, psd, label="spire-ai.20241213.00z.global.0450.ens_members=1.z500", linewidth=2, color="blue")

# Customize the plot
plt.xlabel("Wavenumber", fontsize=14)
plt.ylabel("Power Spectral Density", fontsize=14)
plt.title("Zonal Energy Spectrum (30° < |lat| < 60°)", fontsize=16, pad=15)
plt.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.7)
plt.tick_params(axis="both", which="major", labelsize=12)
plt.legend(fontsize=12, loc="upper right")
plt.tight_layout()

# Show the plot
plt.show()

wavenumbers

psd.sizes["longitude"]

