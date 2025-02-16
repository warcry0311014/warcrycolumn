# QCKColumn
Current Version: 1.0.0 (2025-02-16)

[**Access Live Version Here**](https://qckcolumnapp.streamlit.app/)

<hr>

### Description

**QCKColumn** is a web application built using Streamlit that enables Civil/Structural Engineers to quickly generate plots of interaction diagram for reinforced concrete columns or perform adequacy checks given the axial load and bending moment demands. 

The application attempts to replicate the intuitive user experience of known commercial design software
for analyzing and designing reinforced concrete columns such as **spColumn (by StructurePoint)** and **Tekla Tedds (by Trimble)** while having the reactive experience of using spreadsheets where a change in input quickly returns an output. 

<hr>

### Motivation

Performing detailed calculations for analyzing or designing reinforced concrete columns can be tedious due to needing to establish the column interaction diagram, a graphical representation of the column's response to combined axial load and bending moment. To create a diagram, we need to calculate multiple pairs of nominal and design (allowable) axial load and bending moment which serves as coordinates to the graph. At the minimum, we calculate a pair for each of the following control points/conditions.

+ **Point 1: Pure compression** - The section is in maximum compression and no bending moment.
+ **Point 2: Maximum axial compression with bending moment** - The section is in full compression and the location of the neutral axis, c is outside the section.
+ **Point 3: Zero strain on steel at tension side** - A part of the section is now in tension and the steel reinforcement at tension side is about to resist tensile stress.
+ **Point 4: Stress on steel at tension side equal to half of yield strength** - The steel area
at tension side experiences stress equal to half of its yield strength. 
+ **Point 5: Balanced condition** - The concrete and the steel at tension side simultaneously reach their maximum compressive strain and yield strains respectively. 
+ **Point 6: Tensile-controlled condition** - The steel at tension side yields significantly such that it reaches its yield strength before the concrete crushes.
+ **Point 7: Pure bending** - The section is in full bending where the net axial load is zero.
+ **Point 8: Pure tension** - The section is in maximum tension and its strength fully relies on the steel reinforcement. 

For this reason, civil/structural engineers typically rely on spreadsheet programs or developed engineering software to do this process for them. However these options have their own downsides. Spreadsheets are inflexible for proper documentation, hard to read when the formula gets longer and complex, and no reliable version control (besides cloud storage services). On the other hand, using a ready-to-use developed software often requires investment for licensing and often requires the user to familarize themselves to the assumptions and procedure done.

This project attempts to demonstrate that developing engineering calculation tools through programming is useful in the long run as it offers opportunities for scaling, ease of revision through version control, and automation to many typical engineering workflows.

<hr>

### Scope, limitations, and assumptions

The reference structural code used for developing the application is ACI 318-19. For the current version of the application, the program is limited to working with SI units, input load demands needs to be factored loads, generating interaction diagrams and checks for rectangular concrete tied columns, and no implementation for biaxial moment condition calculations.

For the assumptions, the implementation of the function for creating the interaction diagram is based on the control points / conditions mentioned above. 

<hr>

### Tools/frameworks used

The application is fully written in Python with the following framework/libraries.
1. **Streamlit** - This framework allows to quickly create web applications while only writing Python code. Though its often used for data-related applications, its powerful feature fits well to any engineering applications.
2. **NumPy and Pandas** - Bread and butter libraries for data manipulation, analysis, and calculations.
3. **SciPy** - Primarily used for solving complex equations.

<hr>

### Notable features of the application

1. The application quickly updates for any change in the input.
2. Computed values of axial force and moment can be exported as a CSV file.
3. Resulting coordinate from the input load is plotted on the interaction diagram.
4. Adequacy check for both case of major axis and minor axis bending (separate checks are done for both).
5. Check for reinforcing detailing requirements.

<hr>

### Main files

1. `main.py` - Script that defines the main web application.
2. `structural/columnconc.py` - Script containing the functions for determining the coordinates of the column interaction diagram with its respective helper functions, and for checking to adequacy and detailing requirements.
3. `structural/genconcrete.py` - Script containing functions for general calculations of section properties, material properties, stresses, coefficients defined in the code, and constants.
4. `structural/__init__.py` - Allows `main.py` to call the functions from `columnconc.py` and `genconcrete.py` bounded to the name `structural`. 
5. `.streamlit/config.toml` - Config file for the Streamlit appication settings such as the theme.
6. `static/` - Contain PNG images for the Streamlit application.
6. `pyproject.toml` and `requirements.txt` - File for setting up working environment and installing dependencies. The former is used when using the [`uv` package manager](https://github.com/astral-sh/uv) while the latter is used for `pip`.

<hr>

### Local installation/setup 

1. Fork the repository then clone locally on your machine.

2. Ensure your current working directory is the project folder itself and check if `pyproject.toml` or `requirements.txt` is present in your working directory.

3. **Installation using** `uv`
    + [Download and install `uv`](https://docs.astral.sh/uv/#installation). 
    + In the terminal, run `uv venv` to create a virtual environment. 
    + Activate venv using `<source path> .venv/bin/activate`.
    + Run `uv sync` to sync the dependencies of the environment according to the content of `pyproject.toml`.

    + *Optional* - From `pyproject.toml`, take note of the "optional-dependencies" that are visible at the bottom. Run `uv sync --extra <name>` to install additional packages.

4. **Installation using** `pip`
    + Create a virtual environment and activate it from your working directory.
    + Run `pip install -r requirements.txt`.

5. To launch the application, go to `main/` and run `streamlit run app.py`.

<hr>

### References

1. [Interaction Diagram - Tied Reinforced Concrete Column Design Strength (ACI 318-19) (spColumn v10.00)](https://structurepoint.org/publication/pdf/Interaction-Diagram-Tied-Reinforced-Concrete-Column-Design-Strength-ACI-318-19.pdf)
2. [Engr. Dennis Mercado - How to Draw Your Own Interaction Diagram](https://engrdennisbmercado.wordpress.com/2017/12/18/how-to-draw-your-own-column-interaction-diagram/)
