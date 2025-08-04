import networkx as nx
import random
import time

class OpticalNetworkSimulator:
    def __init__(self, wavelengths=4, converters=0):
        self.G = nx.Graph()
        self.wavelengths = wavelengths
        self.link_wavelengths = {}
        self.converters = converters
        self.blocked_count = 0
        self.success_count = 0
        self.total_delay = 0
        self.total_throughput = 0

    def add_node(self, node):
        self.G.add_node(node, failed=False)

    def fail_node(self, node):
        if node in self.G:
            self.G.nodes[node]['failed'] = True

    def repair_node(self, node):
        if node in self.G:
            self.G.nodes[node]['failed'] = False

    def add_link(self, u, v):
        self.G.add_edge(u, v)
        self.link_wavelengths[(u, v)] = [False] * self.wavelengths

    def shortest_path(self, src, dst):
        try:
            G_active = self.G.copy()
            for n in list(self.G.nodes):
                if self.G.nodes[n]['failed']:
                    G_active.remove_node(n)
            return nx.shortest_path(G_active, src, dst)
        except nx.NetworkXNoPath:
            return None

    def assign_wavelength(self, path, allow_conversion=False):
        # Try to find common wavelength along full path
        for w in range(self.wavelengths):
            if all(not self.link_wavelengths[(min(path[i], path[i+1]), max(path[i], path[i+1]))][w]
                   for i in range(len(path)-1)):
                for i in range(len(path)-1):
                    self.link_wavelengths[(min(path[i], path[i+1]), max(path[i], path[i+1]))][w] = True
                return [w] * len(path)

        if allow_conversion and self.converters > 0:
            # Assign wavelengths per hop if converters are available
            wavelength_path = []
            for i in range(len(path)-1):
                for w in range(self.wavelengths):
                    if not self.link_wavelengths[(min(path[i], path[i+1]), max(path[i], path[i+1]))][w]:
                        self.link_wavelengths[(min(path[i], path[i+1]), max(path[i], path[i+1]))][w] = True
                        wavelength_path.append(w)
                        break
            return wavelength_path if len(wavelength_path) == len(path)-1 else None
        return None

    def release_wavelength(self, path, wavelengths):
        for i in range(len(path)-1):
            self.link_wavelengths[(min(path[i], path[i+1]), max(path[i], path[i+1]))][wavelengths[i]] = False

    def simulate_connection(self, src, dst, mode="OCS", allow_conversion=False):
        path = self.shortest_path(src, dst)
        if not path:
            self.blocked_count += 1
            return {"status": "blocked", "reason": "No path"}

        wavelengths = self.assign_wavelength(path, allow_conversion)
        if wavelengths is None:
            self.blocked_count += 1
            return {"status": "blocked", "reason": "No wavelength"}

        delay = 0
        throughput = 0

        if mode == "OCS":
            delay = random.uniform(0.2, 0.5)
            throughput = random.randint(8, 10) * 10
        elif mode == "OBS":
            delay = random.uniform(0.05, 0.2)
            throughput = random.randint(6, 9) * 10
        elif mode == "OPS":
            delay = random.uniform(0.01, 0.05)
            throughput = random.randint(4, 8) * 10

        self.success_count += 1
        self.total_delay += delay
        self.total_throughput += throughput

        return {
            "status": "success",
            "path": path,
            "wavelengths": wavelengths,
            "delay": round(delay, 4),
            "throughput": throughput
        }

    def get_qos(self):
        total_requests = self.success_count + self.blocked_count
        blocking_prob = self.blocked_count / total_requests if total_requests else 0
        avg_delay = self.total_delay / self.success_count if self.success_count else 0
        avg_throughput = self.total_throughput / self.success_count if self.success_count else 0
        return {
            "Blocking Probability": round(blocking_prob, 3),
            "Average Delay": round(avg_delay, 4),
            "Average Throughput": round(avg_throughput, 2)
        }
