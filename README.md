# Magic The Gathering Price Analytics

## Brief Description

The idea behind this project is to fetch Magic The Gathering cards information (name, set, rarity, current market price, etc), sotre it and ran some code to present/analyze it.

## How to use it

This will discribe how I did the setup and the configuration. By any mins is tested in multiple OS and/or version. It's just the way I solved things for my local Windows computer. Also take in mind that I'm not uploading the venv (virtual environment) for this project. This should be created and configurated in each case.
With that in consideration, to use this you should do the following:

	- Have Python installed.
	- Install JupyterLab.
	- Create a virtual env in the folder to witch you copy this repository to (py -m venv <name_for_my_env>).
	- Activate the virtual env in the folder to witch you copy this repository to (.\<name_for_my_env>\Scripts\activate).
	- Install Node.js in you computer(the reason for this is that once you install jupyter-dash is necessay to be able to build jupyter <it needs to in order to make full ussage of the library>).
	- Install the following python libreries to the virtual env:
		- pandas
		- dash
		- jupyter-dash (to be able to run dash on JupyterLab)
		- jupyterlab "ipywidgets>=7.5” (to be able to run Plotly inside JupyterLab)

Also is important to star jupyterlab from the directory location and with the environment active first.
		