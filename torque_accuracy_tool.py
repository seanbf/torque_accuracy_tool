import streamlit as st
import pandas as pd
from streamlit.proto.Empty_pb2 import Empty
from src.layout import report_details, limits,  limit_format
from src.utils import load_dataframe, col_removal, determine_transients, sample_transients, transient_removal, round_speeds, torque_error_calc, error_nm_analysis, error_pc_analysis, z_col_or_grid
from src.plotter import demanded_plot, transient_removal_plot, plot_3D
from src.colors import sequential_color_dict, diverging_color_dict, plot_color_set
from src.symbols import symbol_auto_select, speed_rpm_symbols, t_demanded_symbols, t_measured_symbols, t_estimated_signals, vdc_symbols,idc_symbols
page_config = st.set_page_config(
                                page_title              ="Torque Accuracy Tool", 
                                page_icon               ="🎯", 
                                #layout                  ='wide', 
                                initial_sidebar_state   ='auto'
                                )


col_left, col_title, col_right = st.columns(3)
col_title.title("Torque Accuracy Tool 🎯")

st.write("The Torque Accuracy Tool will plot test data, remove transients and provide analysis on the accuracy of **Torque Output** against **Torque Measured**, in each or all operating quadrants, voltages and speeds.")
st.write("The tool can also be used to achieve the same analysis with **Estimated Torque**.")
st.write("As the tool uses averaging within the analysis, there is an option to remove transients from the data so only steady state data is analysed.")

#strings used for readability
t_demanded              = "Torque Demanded [Nm]"
t_estimated             = "Torque Estimated [Nm]"
t_measured              = "Torque Measured [Nm]"
speed                   = "Speed [rpm]"
speed_round             = "Speed [rpm] Rounded"
vdc                     = "DC Voltage"
idc                     = "DC Current"
t_demanded_error_nm     = "Torque Demanded Error [Nm]"
t_demanded_error_pc     = "Torque Demanded Error [%]"
t_estimated_error_nm    = "Torque Estimated Error [Nm]"
t_estimated_error_pc    = "Torque Estimated Error [%]"



st.markdown("---") 



st.header("Upload file(s)")
#Ask for file upload and read.
st.checkbox("Show first 10 rows of Data", key = "Sample Data")

uploaded_file = st.file_uploader(   
                                        label="",
                                        accept_multiple_files=True,
                                        type=['csv', 'xlsx']
                                        )

if uploaded_file == []:
    st.info("Please upload file(s)")
    st.stop()

else:

    dataframe, columns  = load_dataframe(uploaded_files=uploaded_file)
    if st.session_state["Sample Data"] == True:
        st.write(dataframe.head(10))
    columns             = list(columns)

    columns.insert(0, "Not Selected")



st.markdown("---") 



st.header("Report Details - (*Optional*)")
test_dict = report_details()



st.markdown("---") 



st.header("Configure Test Limits")
st.radio("Torque Analysis", ["Output & Estimated","Output"], key = "Analysis Mode")
limits(st.session_state["Analysis Mode"])



st.markdown("---") 



st.header("Configure Signals")
st.write("All signals must be manually selected if auto-select cannot find them.")

st.selectbox(t_measured,list(columns),  key = t_measured, index = symbol_auto_select(columns, t_measured_symbols))

st.selectbox(t_demanded,list(columns), key = t_demanded, index = symbol_auto_select(columns, t_demanded_symbols))

if st.session_state["Analysis Mode"] == "Output & Estimated":
    st.selectbox(t_estimated,list(columns), key = t_estimated, index = symbol_auto_select(columns, t_estimated_signals))

st.selectbox(speed,list(columns), key = speed, index = symbol_auto_select(columns, speed_rpm_symbols))

st.selectbox(vdc,list(columns), key = vdc, index = symbol_auto_select(columns, vdc_symbols))

st.selectbox(idc,list(columns), key = idc, index = symbol_auto_select(columns, idc_symbols))

if any(value == 'Not Selected' for value in st.session_state.values()) == True:
    st.stop()

selected_data = col_removal(dataframe, list(st.session_state.values()))

if st.session_state["Analysis Mode"] == "Output & Estimated":
    selected_data.rename(columns = {        
                                        st.session_state[speed]         :speed,
                                        st.session_state[t_measured]    :t_measured,
                                        st.session_state[t_demanded]    :t_demanded,
                                        st.session_state[t_estimated]   :t_estimated,
                                        st.session_state[vdc]           :vdc,
                                        st.session_state[idc]           :idc
                                    }, inplace = True)
else:
    selected_data.rename(columns = {        
                                        st.session_state[speed]         :speed,
                                        st.session_state[t_measured]    :t_measured,
                                        st.session_state[t_demanded]    :t_demanded,
                                        st.session_state[vdc]           :vdc,
                                        st.session_state[idc]           :idc
                                    }, inplace = True)



st.markdown("---") 



st.header("Remove Transients - (*Optional*)")
with st.spinner("Generating transient removal tool"):

    st.write("Make sure the transient removal process is removing the required data; when there is a step change and time taken until steady state is reached.")
    st.markdown("If this is not achieved, adjust the variable `Dwell Period` using the slider below")
    st.markdown("Scan through torque steps using the `Sample` slider to determine if the `Dwell Period` is appropiate for the range of torque steps.")

    dwell_col, sample_col, t_d_filter_col = st.columns(3)
    dwell_col.slider("Dwell Period", min_value=0, max_value=5000, step=1, value= 500, key = "Dwell Period")
    t_d_filter_col.number_input("Torque Demanded Filter", min_value=0.0,max_value=300.0,step=0.1,value=0.0,help="If torque demand is not as consistent as expected i.e. during derate, apply a threshold to ignore changes smaller than the filter",key = "Torque Demanded Filter")

    Step_index, Stop_index          = determine_transients(selected_data,t_demanded,st.session_state["Torque Demanded Filter"], st.session_state["Dwell Period"]) 
    
    sample_col.slider("Sample", min_value=1, max_value=abs(len(Stop_index)-1), step=1, value= round(abs(len(Stop_index)-1)/2), key = "Sample")


    transient_sample                = sample_transients(Step_index, Stop_index, selected_data, st.session_state)    
    transient_removal_sample_plot   = transient_removal_plot(transient_sample, Step_index, Stop_index, selected_data, st.session_state,  t_demanded, t_estimated, t_measured)

    selected_data = selected_data.drop(['Step_Change'], axis = 1)

    st.plotly_chart(transient_removal_sample_plot)

rem_trans_col1, rem_trans_col2, rem_trans_col3 = st.columns(3)
    
if rem_trans_col2.checkbox("Remove Transients", key = "Remove Transients") == True: 
    with st.spinner("Removing Transients from data"):
        selected_data = transient_removal(selected_data, Step_index, Stop_index)
        st.success(str(len(Stop_index)-1) + " Transients Removed")



st.markdown("---") 



st.header("Round Test Point Variables")  
st.subheader("Speed")
st.number_input("Base", min_value=1, max_value=5000, value=50, step=1, key = "Speed Base")
round_spd_col1, round_spd_col2, round_spd_col3 = st.columns(3)
if round_spd_col2   .checkbox("Round Speed", key = "Round Speed") == True:
    selected_data = round_speeds(selected_data, speed, t_demanded, st.session_state["Speed Base"])
    number_of_rounded_speeds = len((selected_data[speed_round]).unique())
    st.success(str(number_of_rounded_speeds) + " Unique Speed Points Found")
else:
    st.stop()
st.subheader("Voltage")


st.markdown("---") 



st.header("Torque Demanded against Speed - (*Optional*)")
if st.checkbox("Plot Test Data", key = "Plot Test Data") == True:
    st.write("Below is a plot of the data representing Torque Demanded and Speed")
    st.write("This is useful to determine if the data uploaded and rounded represent the correct test cases / behaviour")
    with st.spinner("Generating Demanded Test Point Plot"):
        st.plotly_chart(demanded_plot(selected_data, t_demanded, speed_round))



st.markdown("---") 



st.header("Torque Output Accuracy")
st.write("Minimum, Mean and Maximum errors are absoluted.")
with st.spinner("Calculating errors..."):
    selected_data = torque_error_calc(selected_data, t_demanded, t_estimated, t_measured, t_demanded_error_nm, t_demanded_error_pc, t_estimated_error_nm, t_estimated_error_pc)

st.subheader("Newton Meter Error")
st.write("Limit: " + "`± "+str(st.session_state["Output Limit [Nm]"]) + " Nm`")
with st.spinner("Generating Torque Output [Nm] Accuracy Table"):
    t_demanded_error_table_nm, min_error_demanded_nm, average_error_demanded_nm, max_error_demanded_nm = error_nm_analysis(selected_data, st.session_state["Output Limit [Nm]"], st.session_state["Output Limit [%]"], t_demanded, t_demanded, t_estimated, t_measured, speed_round, vdc, idc, t_demanded_error_nm, t_demanded_error_pc)
    
    t_dem_err_nm_col1, t_dem_err_nm_col2, t_dem_err_nm_col3 = st.columns(3)
    min_error_demanded_nm_display, average_error_demanded_nm_display, max_error_demanded_nm_display = limit_format(min_error_demanded_nm, average_error_demanded_nm, max_error_demanded_nm, "Output", "Nm")

    t_dem_err_nm_col1.subheader("Minimum Error")
    t_dem_err_nm_col1.markdown(min_error_demanded_nm_display, unsafe_allow_html=True)

    t_dem_err_nm_col2.subheader("Mean Error")
    t_dem_err_nm_col2.markdown(average_error_demanded_nm_display, unsafe_allow_html=True)

    t_dem_err_nm_col3.subheader("Maximum Error")
    t_dem_err_nm_col3.markdown(max_error_demanded_nm_display, unsafe_allow_html=True)

    st.write(t_demanded_error_table_nm)

st.subheader("Percentage Error")
with st.spinner("Generating Torque Output [%] Accuracy Table"):
    t_demanded_error_table_pc, min_error_demanded_pc, average_error_demanded_pc, max_error_demanded_pc = error_pc_analysis(selected_data, st.session_state["Output Limit [Nm]"], st.session_state["Output Limit [%]"], t_demanded, t_demanded, t_estimated, t_measured, speed_round, vdc, idc, t_demanded_error_nm, t_demanded_error_pc)
    
    t_dem_err_pc_col1, t_dem_err_pc_col2, t_dem_err_pc_col3 = st.columns(3)

    min_error_demanded_pc_display, average_error_demanded_pc_display, max_error_demanded_pc_display = limit_format(min_error_demanded_pc, average_error_demanded_pc, max_error_demanded_pc, "Output", "%")

    t_dem_err_pc_col1.subheader("Minimum Error")
    t_dem_err_pc_col1.markdown(min_error_demanded_pc_display, unsafe_allow_html=True)

    t_dem_err_pc_col2.subheader("Mean Error")
    t_dem_err_pc_col2.markdown(average_error_demanded_pc_display, unsafe_allow_html=True)

    t_dem_err_pc_col3.subheader("Maximum Error")
    t_dem_err_pc_col3.markdown(max_error_demanded_pc_display, unsafe_allow_html=True)

    st.write(t_demanded_error_table_pc)



st.markdown("---") 



st.header("Torque Estimated Accuracy")
st.write("Minimum, Mean and Maximum errors are absoluted.")
st.subheader("Newton Meter Error")
st.write("Limit: " + "`± "+str(st.session_state["Estimated Limit [Nm]"]) + " Nm`")

with st.spinner("Generating Torque Estimated [Nm] Accuracy Table"):
    t_estimated_error_table_nm, min_error_estimated_nm, average_error_estimated_nm, max_error_estimated_nm = error_nm_analysis(selected_data, st.session_state["Estimated Limit [Nm]"], st.session_state["Estimated Limit [%]"], t_estimated, t_demanded, t_estimated, t_measured, speed_round, vdc, idc, t_estimated_error_nm, t_estimated_error_pc)
    
    t_est_err_nm_col1, t_est_err_nm_col2, t_est_err_nm_col3 = st.columns(3)

    min_error_estimated_nm_display, average_error_estimated_nm_display, max_error_estimated_nm_display = limit_format(min_error_estimated_nm, average_error_estimated_nm, max_error_estimated_nm, "Estimated", "Nm")

    t_est_err_nm_col1.subheader("Minimum Error")
    t_est_err_nm_col1.markdown(min_error_estimated_nm_display, unsafe_allow_html=True)

    t_est_err_nm_col2.subheader("Mean Error")
    t_est_err_nm_col2.markdown(average_error_estimated_nm_display, unsafe_allow_html=True)

    t_est_err_nm_col3.subheader("Maximum Error")
    t_est_err_nm_col3.markdown(max_error_estimated_nm_display, unsafe_allow_html=True)

    st.write(t_estimated_error_table_nm)

st.subheader("Percentage Error")
with st.spinner("Generating Torque Estimated [%] Accuracy Table"):
    st.write("Limit: " + "`± "+str(st.session_state["Estimated Limit [%]"]) + " %`")
    
    t_estimated_error_table_pc, min_error_estimated_pc, average_error_estimated_pc, max_error_estimated_pc = error_pc_analysis(selected_data, st.session_state["Estimated Limit [Nm]"], st.session_state["Estimated Limit [%]"], t_estimated, t_demanded, t_estimated, t_measured, speed_round, vdc, idc, t_estimated_error_nm, t_estimated_error_pc)
    
    t_est_err_pc_col1, t_est_err_pc_col2, t_est_err_pc_col3 = st.columns(3)
    
    min_error_estimated_pc_display, average_error_estimated_pc_display, max_error_estimated_pc_display = limit_format(min_error_estimated_pc, average_error_estimated_pc, max_error_estimated_pc, "Estimated", "%")

    t_est_err_pc_col1.subheader("Minimum Error")
    t_est_err_pc_col1.markdown(min_error_estimated_pc_display, unsafe_allow_html=True)

    t_est_err_pc_col2.subheader("Mean Error")
    t_est_err_pc_col2.markdown(average_error_estimated_pc_display, unsafe_allow_html=True)

    t_est_err_pc_col3.subheader("Maximum Error")
    t_est_err_pc_col3.markdown(max_error_estimated_pc_display, unsafe_allow_html=True)

    st.write(t_estimated_error_table_pc)



st.markdown("---") 



st.header("Torque Demanded Accuracy Plots - *Optional*")
st.subheader("Plot Configuration")
t_d_error_nm_plot1, t_d_error_nm_plot2, t_d_error_nm_plot3, col_preview = st.columns(4)
t_d_error_nm_plot1.selectbox("Chart Type", ["Contour", "Surface","Heatmap","3D Scatter"], key = "T_d_error_chart_type" )
t_d_error_nm_plot2.selectbox("Color Scale", ["Sequential", "Diverging"], key = "T_d_error_chart_scale" )

if st.session_state["T_d_error_chart_scale"] == 'Sequential':
    color_map = list(sequential_color_dict().keys())
else:
    color_map = list(diverging_color_dict().keys())

t_d_error_nm_plot3.selectbox("Color Map", color_map, key = "T_d_error_chart_color" )
if  st.session_state["T_d_error_chart_scale"] == 'Sequential':
    color_palette = sequential_color_dict().get(st.session_state["T_d_error_chart_color"])
else:
    color_palette = diverging_color_dict().get(st.session_state["T_d_error_chart_color"])

colormap_preview = plot_color_set(color_palette, st.session_state["T_d_error_chart_color"])
col_preview.image(colormap_preview, use_column_width = True)

t_d_error_nm_plot4, t_d_error_nm_plot5, t_d_error_nm_plot6 = st.columns(3)
t_d_error_nm_plot4.selectbox("Fill", ["NaN", "0"], key = "T_d_error_chart_fill" )
t_d_error_nm_plot5.selectbox("Method", ["linear", "cubic"], key = "T_d_error_chart_method" )
t_d_error_nm_plot6.number_input("Grid Resolution",  min_value = float(-500.0), max_value = float(500.0), value = float(50.0), step = float(1.0), key = "T_d_error_chart_grid")
st.subheader("Data Overlay")
if st.checkbox("Show Data Overlayed"):
    overlay = True
else:
    overlay = False
t_d_error_nm_ovr1, t_d_error_nm_ovr2 = st.columns(2)
t_d_error_nm_ovr1.slider("Opacity",value=0.5,min_value=0.0, max_value=1.0, step=0.01, key = "T_d_error_overlay_opacity")
t_d_error_nm_ovr2.color_picker("Overlay Color", key = "T_d_error_overlay_color")

st.checkbox("Plot Torque Demanded [Nm] Accuracy Chart", key = "plot_demanded_error_nm")
st.checkbox("Plot Torque Demanded [%] Accuracy Chart", key = "plot_demanded_error_pc")
st.checkbox("Plot Torque Estimated [Nm] Accuracy Chart", key = "plot_estimated_error_nm")
st.checkbox("Plot Torque Estimated [%] Accuracy Chart", key = "plot_estimated_error_pc")


if st.session_state["plot_demanded_error_nm"] == True:
    with st.spinner("Generating Plot"):
        x_td_nm_formatted, y_td_nm_formatted, z_td_nm_formatted = z_col_or_grid(st.session_state["T_d_error_chart_type"],  st.session_state["T_d_error_chart_fill"],  st.session_state["T_d_error_chart_method"],  st.session_state["T_d_error_chart_grid"], selected_data["Torque Demanded [Nm]"], selected_data["Speed [rpm] Rounded"], selected_data["Torque Demanded Error [Nm]"])
        t_d_error_nm_plot = plot_3D(speed_round,t_demanded,t_demanded_error_nm,x_td_nm_formatted, y_td_nm_formatted, z_td_nm_formatted, st.session_state["T_d_error_chart_type"], color_palette, overlay, st.session_state["T_d_error_overlay_opacity"], st.session_state["T_d_error_overlay_color"])
        st.write(t_d_error_nm_plot)

if st.session_state["plot_demanded_error_pc"] == True:
    with st.spinner("Generating Plot"):
        x_td_pc_formatted, y_td_pc_formatted, z_td_pc_formatted = z_col_or_grid(st.session_state["T_d_error_chart_type"],  st.session_state["T_d_error_chart_fill"],  st.session_state["T_d_error_chart_method"],  st.session_state["T_d_error_chart_grid"], selected_data["Torque Demanded [Nm]"], selected_data["Speed [rpm] Rounded"], selected_data["Torque Demanded Error [%]"])
        t_d_error_pc_plot = plot_3D(speed_round,t_demanded,t_demanded_error_pc,x_td_pc_formatted, y_td_pc_formatted, z_td_pc_formatted, st.session_state["T_d_error_chart_type"], color_palette, overlay, st.session_state["T_d_error_overlay_opacity"], st.session_state["T_d_error_overlay_color"])
        st.write(t_d_error_pc_plot)


if st.session_state["plot_estimated_error_nm"] == True:
    with st.spinner("Generating Plot"):
        x_te_nm_formatted, y_te_nm_formatted, z_te_nm_formatted = z_col_or_grid(st.session_state["T_d_error_chart_type"],  st.session_state["T_d_error_chart_fill"],  st.session_state["T_d_error_chart_method"],  st.session_state["T_d_error_chart_grid"], selected_data["Torque Estimated [Nm]"], selected_data["Speed [rpm] Rounded"], selected_data["Torque Estimated Error [Nm]"])
        t_e_error_nm_plot = plot_3D(speed_round,t_estimated,t_estimated_error_nm,x_te_nm_formatted, y_te_nm_formatted, z_te_nm_formatted, st.session_state["T_d_error_chart_type"], color_palette, overlay, st.session_state["T_d_error_overlay_opacity"], st.session_state["T_d_error_overlay_color"])
        st.write(t_e_error_nm_plot)


if st.session_state["plot_estimated_error_pc"] == True:
    with st.spinner("Generating Plot"):
        x_te_pc_formatted, y_te_pc_formatted, z_te_pc_formatted = z_col_or_grid(st.session_state["T_d_error_chart_type"],  st.session_state["T_d_error_chart_fill"],  st.session_state["T_d_error_chart_method"],  st.session_state["T_d_error_chart_grid"], selected_data["Torque Estimated [Nm]"], selected_data["Speed [rpm] Rounded"], selected_data["Torque Estimated Error [%]"])
        t_e_error_pc_plot = plot_3D(speed_round,t_estimated,t_estimated_error_pc, x_te_pc_formatted, y_te_pc_formatted, z_te_pc_formatted, st.session_state["T_d_error_chart_type"], color_palette, overlay, st.session_state["T_d_error_overlay_opacity"], st.session_state["T_d_error_overlay_color"])
        st.write(t_e_error_pc_plot)
#report_table = pd.DataFrame([test_dict])
#report_table = report_table.astype(str)
#report_table = report_table.T