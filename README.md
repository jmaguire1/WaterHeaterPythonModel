# WaterHeaterPythonModel
Water Heater Python Model
===============

This project includes an electric water heater model in Python. This model is based on the EnergyPlus single node water heater model.

## Table of Contents

* [Directory Layout] (#directory-layout)
* [Running the Water Heater](#running-the-model)
* [TODOs](#todo)
* [Development](#development)
<!--* [Outputs](#outputs)-->

## Directory Layout

Currently a bit of a mess, the main model is "annual_ewh_run.py". Data files (draw profile, mains temp, and ambient temp" are in the "data files" folder.

## Running the Model

To run the model, open and run "annual_ewh_run.py". Everything should run automatically and output results to "ElecWHOutput.csv"

This will apply the measures to the OpenStudio seed model specified in the .osw, run the EnergyPlus simulation, and produce output. 

## TODOs

* [Draw Profile] - For mixed flows, iterate and use the current water heater temperature rather than last timestep's temperature
* [Validation] - Get a better match on water heater consumed and delivered energy consumption to EnergyPlus (currently 10% difference)
* [Multinode model] - Allow the model to work for n nodes (12 is pretty typical for a stratified tank). We'll also need to add master/slave element controls.
