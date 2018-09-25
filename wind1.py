__copyright__ = "Copyright oemof developer group"
__license__ = "GPLv3"

import os
import pandas as pd

from windpowerlib.modelchain import ModelChain
from windpowerlib.wind_turbine import WindTurbine
from windpowerlib import wind_turbine as wt

import logging
logging.getLogger().setLevel(logging.DEBUG)

def get_weather_data(filename='weather.csv', **kwargs):
    r"""
    Imports weather data from a file.

    The data include wind speed at two different heights in m/s, air
    temperature in two different heights in K, surface roughness length in m
    and air pressure in Pa. The file is located in the example folder of the
    windpowerlib. The height in m for which the data applies is specified in
    the second row.

    Parameters
    ----------
    filename : string
        Filename of the weather data file. Default: 'weather.csv'.

    Other Parameters
    ----------------
    datapath : string, optional
        Path where the weather data file is stored.
        Default: 'windpowerlib/example'.

    Returns
    -------
    weather_df : pandas.DataFrame
        DataFrame with time series for wind speed `wind_speed` in m/s,
        temperature `temperature` in K, roughness length `roughness_length`
        in m, and pressure `pressure` in Pa.
        The columns of the DataFrame are a MultiIndex where the first level
        contains the variable name (e.g. wind_speed) and the second level
        contains the height at which it applies (e.g. 10, if it was
        measured at a height of 10 m).

    """

    if 'datapath' not in kwargs:
        kwargs['datapath'] = os.path.join(os.path.split(
            os.path.dirname(__file__))[0], 'example')
    file = os.path.join(kwargs['datapath'], filename)
    # read csv file
    weather_df = pd.read_csv(file, index_col=0, header=[0, 1])
    # change type of index to datetime and set time zone
    weather_df.index = pd.to_datetime(weather_df.index).tz_localize(
        'UTC').tz_convert('Europe/Berlin')
    # change type of height from str to int by resetting columns
    weather_df.columns = [weather_df.axes[1].levels[0][
                              weather_df.axes[1].labels[0]],
                          weather_df.axes[1].levels[1][
                              weather_df.axes[1].labels[1]].astype(int)]
    return weather_df


# Read weather data from csv
weather = get_weather_data(filename='weather.csv', datapath='')
print(weather[['wind_speed', 'temperature', 'pressure']][0:3])

# get power curves
# get names of wind turbines for which power curves are provided (default)
# set print_out=True to see the list of all available wind turbines
wt.get_turbine_types(print_out=False)

# get power coefficient curves
# write names of wind turbines for which power coefficient curves are provided
# to 'turbines' DataFrame
turbines = wt.get_turbine_types(filename='power_coefficient_curves.csv', print_out=False)
# find all Enercons in 'turbines' DataFrame
print(turbines[turbines["turbine_id"].str.contains("ENERCON")])

# specification of own wind turbine (Note: power coefficient values and
# nominal power have to be in Watt)
myTurbine = {
    'name': 'myTurbine',
    'nominal_power': 3e6,  # in W
    'hub_height': 105,  # in m
    'rotor_diameter': 90,  # in m
    'power_curve': pd.DataFrame(
            data={'power': [p * 1000 for p in [
                      0.0, 26.0, 180.0, 1500.0, 3000.0, 3000.0]],  # in W
                  'wind_speed': [0.0, 3.0, 5.0, 10.0, 15.0, 25.0]})  # in m/s
    }
# initialise WindTurbine object
my_turbine = WindTurbine(**myTurbine)

# specification of wind turbine where power curve is provided
# if you want to use the power coefficient curve change the value of
# 'fetch_curve' to 'power_coefficient_curve'
enerconE126 = {
    'name': 'ENERCON E 126 7500',  # turbine name as in register
    'hub_height': 135,  # in m
    'rotor_diameter': 127,  # in m
    'fetch_curve': 'power_curve'  # fetch power curve
}
# initialise WindTurbine object
e126 = WindTurbine(**enerconE126)

# power output calculation for my_turbine
# initialise ModelChain with default parameters and use run_model
# method to calculate power output
mc_my_turbine = ModelChain(my_turbine).run_model(weather)
# write power output timeseries to WindTurbine object
my_turbine.power_output = mc_my_turbine.power_output

# power output calculation for e126
# own specifications for ModelChain setup
modelchain_data = {
    'wind_speed_model': 'logarithmic',      # 'logarithmic' (default),
                                            # 'hellman' or
                                            # 'interpolation_extrapolation'
    'density_model': 'ideal_gas',           # 'barometric' (default), 'ideal_gas'
                                            #  or 'interpolation_extrapolation'
    'temperature_model': 'linear_gradient', # 'linear_gradient' (def.) or
                                            # 'interpolation_extrapolation'
    'power_output_model': 'power_curve',    # 'power_curve' (default) or
                                            # 'power_coefficient_curve'
    'density_correction': True,             # False (default) or True
    'obstacle_height': 0,                   # default: 0
    'hellman_exp': None}                    # None (default) or None

# initialise ModelChain with own specifications and use run_model method to
# calculate power output
mc_e126 = ModelChain(e126, **modelchain_data).run_model(
    weather)
# write power output timeseries to WindTurbine object
e126.power_output = mc_e126.power_output

# try to import matplotlib
try:
    from matplotlib import pyplot as plt
    # matplotlib inline needed in notebook to plot inline
    %matplotlib inline
except ImportError:
    plt = None

# plot turbine power output
if plt:
    e126.power_output.plot(legend=True, label='Enercon E126')
    my_turbine.power_output.plot(legend=True, label='myTurbine')
    plt.show()

# plot power (coefficient) curves
if plt:
    if e126.power_coefficient_curve is not None:
        e126.power_coefficient_curve.plot(
            x='wind_speed', y='power coefficient', style='*',
            title='Enercon E126 power coefficient curve')
        plt.show()
    if e126.power_curve is not None:
        e126.power_curve.plot(x='wind_speed', y='power', style='*',
                              title='Enercon E126 power curve')
        plt.show()
    if my_turbine.power_coefficient_curve is not None:
        my_turbine.power_coefficient_curve.plot(
            x='wind_speed', y='power coefficient', style='*',
            title='myTurbine power coefficient curve')
        plt.show()
    if my_turbine.power_curve is not None:
        my_turbine.power_curve.plot(x='wind_speed', y='power', style='*',
                                    title='myTurbine power curve')
        plt.show()
