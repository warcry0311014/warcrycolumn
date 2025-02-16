import streamlit as st
import altair as alt
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

import structural as struct


st.set_page_config(
    page_title="QCKColumn",
    page_icon=":material/function:"
)


st.title("QCKColumn")
header_container = st.container(border=True)
header_container.write("A web application for analyzing reinforced concrete tied columns based on ACI 318-19.")

st.subheader("Input")

st.markdown("**Section Properties**")

sp_col1, sp_col2 = st.columns(2)
input_b:int = sp_col1.number_input("Column width, b (mm)", min_value=200, value=250, step=25)
input_h:int = sp_col1.number_input("Column height, h (mm)", min_value=200, value=250, step=25)
input_cover:int = sp_col1.number_input("Concrete clear cover, cc (mm)", min_value=40, value=40, step=5)
sp_col2.image("main/static/gencolumndefault.png", use_container_width=True)

sp_col4, sp_col5 = st.columns(2)
dmain_sizes:tuple = struct.STD_REBAR_SIZES
dtrans_sizes:tuple = struct.STD_REBAR_SIZES[:3]
input_dmain:int = sp_col4.selectbox("Main bar size, d_main (mm)", dmain_sizes, index=dmain_sizes.index(16), placeholder="Choose bar size")
input_dtrans:int = sp_col4.selectbox("Transverse bar size, d_trans (mm)", dtrans_sizes, placeholder="Choose bar size")
input_nbar_b:int = sp_col5.number_input("Number of main bars along width, b", min_value=2, value=2)
input_nbar_h:int = sp_col5.number_input("Number of main bars along height, h", min_value=2, value=2)

n_bar_total = input_nbar_b * 2 + (input_nbar_h - 2) * 2
add_secproperties = struct.get_secproperties(b=input_b, h=input_h, ccover=input_cover, 
                                             d_main=input_dmain, d_trans=input_dtrans,
                                             n_bar_b=input_nbar_b, n_bar_h=input_nbar_h,
                                             n_bar_total=n_bar_total)

add_secproperties_container = st.expander("Additional sectional properties")
with add_secproperties_container:
    st.markdown(f"Gross area of concrete, Ag (mm2): **{add_secproperties["gross_area"]}**")
    st.markdown(f"Total area of steel, As (mm2): **{add_secproperties["steel_area"]}**")
    st.markdown(f"Total number of main bars: **{n_bar_total}**")
    st.markdown(f"Steel ratio (rho): **{add_secproperties["rho"]:.3%}**")
    st.markdown(f"Clear spacing of main bars along b (mm): **{add_secproperties["cspace_b"]:.2f}**")
    st.markdown(f"Clear spacing of main bars along h (mm): **{add_secproperties["cspace_h"]:.2f}**")

st.markdown("**Material Properties**")

mp_col1, mp_col2 = st.columns(2)
input_fc:int = mp_col1.number_input("Concrete compressive strength, fc (MPa)", min_value=17, value=21)
input_fy:int = mp_col2.number_input("Steel yield strength, fy (MPa)", min_value=230, value=420)

add_matproperties = struct.get_matproperties(fc=input_fc, fy=input_fy)

add_matproperties_container = st.expander("Additional material properties")
with add_matproperties_container:
    st.markdown(f"Concrete modulus of elasticity, Ec (MPa): **{add_matproperties["elasticity_concrete"]:.0f}**")
    st.markdown(f"Beta 1 coefficient: **{add_matproperties["beta1"]:.3f}**")
    st.markdown(f"Ultimate strain in concrete: **{add_matproperties["e_ult"]}**")
    st.markdown(f"Steel modulus of elasticity, Ec (MPa): **{add_matproperties["elasticity_steel"]}**")
    st.markdown(f"Yield strain in steel: **{add_matproperties["ystrain"]:.4f}**")
    st.markdown(f"Tensile-controlled steel strain: **{add_matproperties["ystrain"] + add_matproperties["e_ult"]:.4f}**")

st.markdown("**Factored Load Demands**")
ld_col1, ld_col2, ld_col3 = st.columns(3)

input_Pu:float = ld_col1.number_input("Axial, Pu (kN)")
input_Mux:float = ld_col2.number_input("Moment about major axis, Mux (kN-m)")
input_Muy:float = ld_col3.number_input("Moment about minor axis, Muy (kN-m)")


# Obtain list of coordinates for creating interaction diagram
cid_coordinates_x, cid_coordinates_y = [], []
TOTAL_POINTS = 8

for i in range(TOTAL_POINTS):
    plot_result = struct.get_cid_coordinate(
        b=input_b, h=input_h, ccover=input_cover, 
        d_main=input_dmain, d_trans=input_dtrans, 
        n_bar=input_nbar_b, n_bar_total=n_bar_total,
        fc=input_fc, fy=input_fy, point=(i + 1)
    )

    cid_coordinates_x.append(plot_result)

for j in range(TOTAL_POINTS):
    plot_result_y = struct.get_cid_coordinate(
        h=input_b, b=input_h, ccover=input_cover, 
        d_main=input_dmain, d_trans=input_dtrans, 
        n_bar=input_nbar_h, n_bar_total=n_bar_total,
        fc=input_fc, fy=input_fy, point=(j + 1)
    )

    cid_coordinates_y.append(plot_result_y)

pd.set_option("display.float_format", lambda x: "%.3f" % x)
cid_df_x = pd.DataFrame(cid_coordinates_x, columns=["phi_Pn", "phi_Mnx"])
cid_df_y = pd.DataFrame(cid_coordinates_y, columns=["phi_Pn", "phi_Mny"])


# Define charts for interaction diagram
cid_chart_x = (
    alt.Chart(cid_df_x.reset_index())
    .mark_line(point=True, color="blue") 
    .encode(
        x="phi_Mnx",
        y="phi_Pn",
        order=alt.Order("index:O"),
        tooltip=[
            alt.Tooltip("index:O", title="Point"),
            alt.Tooltip("phi_Mnx:Q", title="Moment Capacity (Mx)", format=".3f"),  
            alt.Tooltip("phi_Pn:Q", title="Axial Capacity (P)", format=".3f")     
        ]
    )
)
cid_chart_y = (
    alt.Chart(cid_df_y.reset_index())
    .mark_line(point=True, color="blue") 
    .encode(
        x="phi_Mny",
        y="phi_Pn",
        order=alt.Order("index:O"),
        tooltip=[
            alt.Tooltip("index:O", title="Point"),
            alt.Tooltip("phi_Mny:Q", title="Moment Capacity (My)", format=".3f"),  
            alt.Tooltip("phi_Pn:Q", title="Axial Capacity (P)", format=".3f")     
        ]
    )
)

# Define charts for plotting load demands on interaction diagram
demand_point_x = pd.DataFrame({"phi_Mnx": [abs(input_Mux)], "phi_Pn": [input_Pu]})
demand_point_y = pd.DataFrame({"phi_Mny": [abs(input_Muy)], "phi_Pn": [input_Pu]})
demand_plot_chart_x = (
    alt.Chart(demand_point_x)
    .mark_point(size=50)
    .encode(
        x="phi_Mnx",
        y="phi_Pn",
        tooltip=[
            alt.Tooltip("phi_Mnx:Q", title="Moment Demand (Mux)", format=".3f"),
            alt.Tooltip("phi_Pn:Q", title="Axial Demand (Pu)", format=".3f")
        ]
    )
)
demand_plot_chart_y = (
    alt.Chart(demand_point_y)
    .mark_point(size=50)
    .encode(
        x="phi_Mny",
        y="phi_Pn",
        tooltip=[
            alt.Tooltip("phi_Mny:Q", title="Moment Demand (Muy)", format=".3f"),
            alt.Tooltip("phi_Pn:Q", title="Axial Demand (Pu)", format=".3f")
        ]
    )
)

# Overlay chart of load demand on interaction diagram
combined_cid_chart_x = cid_chart_x + demand_plot_chart_x
combined_cid_chart_y = cid_chart_y + demand_plot_chart_y


st.subheader("Output")

def render_adequacy_status(result_x:dict, result_y:dict) -> str:
    """Helper for rendering message from adequacy check result."""

    if result_x["is_adequate"] and result_y["is_adequate"]:
        return f"{result_x["status"]} - {result_x["summary"]}."
    
    if not result_x["is_adequate"] and not result_y["is_adequate"]:
        return f"{result_x["status"]} - {result_x["summary"]} & {result_y["summary"]}."
    
    return_status = result_x["status"] if result_y["is_adequate"] else result_y["status"]
    return_summary = result_x["summary"] if result_y["is_adequate"] else result_y["summary"]
    return f"{return_status} - {return_summary}."


def render_detail_status(result_detailing:dict) -> str:
    """Helper for rendering message from reinforcement detailing check result."""

    if not result_detailing["is_rho_adequate"]:
        return "NG - Steel ratio is not within allowable limits."
    
    if not result_detailing["is_cspace_adequate"]:
        return "NG - Smallest clear spacing is smaller than required value."
    
    return "OK - Satisfied reinforcement detailing requirements."


if input_Pu == 0 and input_Mux == 0 and input_Muy == 0:
    report_adequacy = "Adequacy: **OK - No input factored load.**"
else:
    adequacy_x = struct.check_col_adequacy(input_Pu=input_Pu, 
                                                     input_Mu=input_Mux, 
                                                     cid_df=cid_df_x,
                                                     col_x=cid_df_x.columns[0],
                                                     col_y=cid_df_x.columns[1])
    
    adequacy_y = struct.check_col_adequacy(input_Pu=input_Pu, 
                                                     input_Mu=input_Muy, 
                                                     cid_df=cid_df_y,
                                                     col_x=cid_df_y.columns[0],
                                                     col_y=cid_df_y.columns[1])
    
    report_adequacy = f"Adequacy: **{render_adequacy_status(adequacy_x, adequacy_y)}**" 

adequacy_detailing = struct.check_detailing(secproperties=add_secproperties, d_main=input_dmain)
report_detailing = f"Reinforcement detailing: **{render_detail_status(adequacy_detailing)}**"

# Present summary of key results for adequacy and detailing check
with st.container(border=True):
    st.markdown(report_adequacy)
    st.markdown(report_detailing)

# Render interaction diagram with plot of load demand
cid_x_tab1, cid_x_tab2 = st.tabs(["Diagram", "Values"])
cid_y_tab1, cid_y_tab2 = st.tabs(["Diagram", "Values"])

with cid_x_tab1:
    st.markdown("**Interaction Diagram - Bending about Major Axis (X)**")
    st.altair_chart(combined_cid_chart_x, use_container_width=True)
with cid_x_tab2:
    st.dataframe(cid_df_x.style.format({"phi_Pn": "{:.3f}", "phi_Mnx": "{:.3f}"}), use_container_width=True)

with cid_y_tab1:
    st.markdown("**Interaction Diagram - Bending about Minor Axis (Y)**")
    st.altair_chart(combined_cid_chart_y, use_container_width=True)
with cid_y_tab2:
    st.dataframe(cid_df_y.style.format({"phi_Pn": "{:.3f}", "phi_Mny": "{:.3f}"}), use_container_width=True)


footer_container = st.container(border=True)
footer_container.markdown("&copy; 2025 [jcdcustodio](https://github.com/jcdcustodio)")