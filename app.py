import streamlit as st
from simulator import OpticalNetworkSimulator
from pyvis.network import Network
import tempfile, os, random, time

# Streamlit page config
st.set_page_config(page_title="Live Optical Switching Simulator", layout="wide")
st.title("🔵 Live Optical Switching & Wavelength Allocation Simulator")

# Initialize simulator
if "sim" not in st.session_state:
    st.session_state.sim = OpticalNetworkSimulator(wavelengths=4, converters=1)
if "traffic_running" not in st.session_state:
    st.session_state.traffic_running = False

sim = st.session_state.sim

# Sidebar: Network Setup
st.sidebar.header("Network Setup")
node_name = st.sidebar.text_input("Add Node")
if st.sidebar.button("Add Node"):
    sim.add_node(node_name)

if len(sim.G.nodes) >= 2:
    u = st.sidebar.selectbox("Link Start", sim.G.nodes)
    v = st.sidebar.selectbox("Link End", sim.G.nodes)
    if st.sidebar.button("Add Link"):
        sim.add_link(u, v)

# Failure simulation
st.sidebar.header("Failure Simulation")
fail_node = st.sidebar.selectbox("Fail Node", ["None"] + list(sim.G.nodes))
if st.sidebar.button("Fail"):
    if fail_node != "None":
        sim.fail_node(fail_node)

repair_node = st.sidebar.selectbox("Repair Node", ["None"] + list(sim.G.nodes))
if st.sidebar.button("Repair"):
    if repair_node != "None":
        sim.repair_node(repair_node)

# Simulation settings
st.sidebar.header("Simulation Settings")
mode = st.sidebar.selectbox("Switching Mode", ["OCS", "OBS", "OPS"])
allow_conversion = st.sidebar.checkbox("Enable Sparse Wavelength Conversion")
traffic_speed = st.sidebar.slider("Traffic Speed (seconds/request)", 0.1, 2.0, 1.0)

# Manual simulation
if len(sim.G.nodes) >= 2:
    src = st.sidebar.selectbox("Source", sim.G.nodes)
    dst = st.sidebar.selectbox("Destination", sim.G.nodes)
    if st.sidebar.button("Run Single Simulation"):
        result = sim.simulate_connection(src, dst, mode=mode, allow_conversion=allow_conversion)
        st.sidebar.write(result)

# Live traffic controls
if st.sidebar.button("Start Live Traffic"):
    st.session_state.traffic_running = True
if st.sidebar.button("Stop Live Traffic"):
    st.session_state.traffic_running = False

# Draw network with wavelength usage
def draw_network():
    net = Network(height="500px", width="100%", bgcolor="#222222", font_color="white")
    for node in sim.G.nodes:
        color = "red" if sim.G.nodes[node].get("failed", False) else "green"
        net.add_node(node, label=node, color=color)
    
    for u, v in sim.G.edges:
        # Get wavelength usage for this link
        wl_state = sim.link_wavelengths.get((u, v)) or sim.link_wavelengths.get((v, u))
        if wl_state:
            active_wl = [f"λ{w}" for w, used in enumerate(wl_state) if used]
            usage_count = sum(wl_state)
        else:
            active_wl = []
            usage_count = 0
        
        # Edge color based on utilization
        if usage_count == 0:
            edge_color = "white"
        elif usage_count < sim.wavelengths // 2:
            edge_color = "yellow"
        else:
            edge_color = "orange"
        
        net.add_edge(u, v, label=",".join(active_wl) if active_wl else "Free", color=edge_color)
    
    tmp_dir = tempfile.mkdtemp()
    path = os.path.join(tmp_dir, "graph.html")
    net.save_graph(path)
    return path

# Live traffic loop
if st.session_state.traffic_running and len(sim.G.nodes) > 1:
    src, dst = random.sample(list(sim.G.nodes), 2)
    sim.simulate_connection(src, dst, mode=mode, allow_conversion=allow_conversion)
    time.sleep(traffic_speed)
    st.experimental_rerun()

# Display QoS metrics
st.subheader("📊 QoS Metrics")
st.write(sim.get_qos())

# Display network graph
html_path = draw_network()
with open(html_path, "r", encoding="utf-8") as f:
    st.components.v1.html(f.read(), height=500)
