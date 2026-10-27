import math
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

# Load wi29 coordinates
with open(r"C:\Users\3540312\.gemini\antigravity-ide\brain\53738352-ba24-4292-aa62-31cffbfea16b\.system_generated\steps\4\content.md", "r") as f:
    lines = f.readlines()

coords = []
reading = False
for line in lines:
    line = line.strip()
    if line == "NODE_COORD_SECTION":
        reading = True
        continue
    if line == "EOF" or line.startswith("EOF"):
        break
    if reading and line:
        parts = line.split()
        if len(parts) >= 3:
            coords.append([float(parts[1]), float(parts[2])])

cities = np.array(coords)
n = len(cities)
print(f"Number of cities: {n}")

# TSPLIB EUC_2D distance matrix
dist_matrix = np.zeros((n, n))
for i in range(n):
    for j in range(n):
        dist_matrix[i, j] = round(math.sqrt((cities[i][0] - cities[j][0])**2 + (cities[i][1] - cities[j][1])**2))

# Let's solve TSP using iterative subtour elimination (DFJ formulation)
# Variables: x[i, j] for 0 <= i < j < n (symmetric TSP)
edges = []
edge_map = {}
idx = 0
for i in range(n):
    for j in range(i + 1, n):
        edges.append((i, j))
        edge_map[(i, j)] = idx
        idx += 1

num_edges = len(edges)
c = np.array([dist_matrix[i, j] for i, j in edges])

# Degree constraints: for each node i, sum_{j != i} x[min(i,j), max(i,j)] == 2
A_rows = []
b_l = []
b_u = []
for i in range(n):
    row = np.zeros(num_edges)
    for j in range(n):
        if i != j:
            e = (min(i, j), max(i, j))
            row[edge_map[e]] = 1.0
    A_rows.append(row)
    b_l.append(2.0)
    b_u.append(2.0)

import scipy.sparse as sp

# Iterative solver with subtour elimination
subtour_constraints = []
subtour_b_u = []

integrality = np.ones(num_edges) # all binary
bounds = Bounds(lb=0.0, ub=1.0)

for step in range(100):
    all_A = A_rows + subtour_constraints
    all_b_l = b_l + [0.0] * len(subtour_constraints)
    all_b_u = b_u + subtour_b_u
    
    A_csr = sp.csr_matrix(np.array(all_A))
    constraints = LinearConstraint(A_csr, all_b_l, all_b_u)
    
    res = milp(c=c, integrality=integrality, bounds=bounds, constraints=constraints)
    if not res.success:
        print("MILP failed:", res.status)
        break
        
    # Check connected components
    adj = {i: [] for i in range(n)}
    selected_edges = []
    for e_idx, val in enumerate(res.x):
        if val > 0.5:
            u, v = edges[e_idx]
            adj[u].append(v)
            adj[v].append(u)
            selected_edges.append((u, v))
            
    # Find components
    visited = [False] * n
    comps = []
    for start in range(n):
        if not visited[start]:
            comp = []
            q = [start]
            visited[start] = True
            while q:
                curr = q.pop()
                comp.append(curr)
                for nxt in adj[curr]:
                    if not visited[nxt]:
                        visited[nxt] = True
                        q.append(nxt)
            comps.append(comp)
            
    if len(comps) == 1:
        print(f"Optimal tour found! Cost = {res.fun}")
        # Reconstruct tour sequence
        tour = [0]
        curr = 0
        prev = -1
        while len(tour) < n:
            for nxt in adj[curr]:
                if nxt != prev:
                    tour.append(nxt)
                    prev = curr
                    curr = nxt
                    break
        print("Tour (0-indexed):", tour)
        print("Tour (1-indexed):", [x + 1 for x in tour])
        break
    else:
        # Add subtour elimination constraint for each small component:
        # sum_{e in E(S)} x[e] <= |S| - 1
        for comp in comps:
            if len(comp) < n:
                row = np.zeros(num_edges)
                S = set(comp)
                for u in S:
                    for v in S:
                        if u < v:
                            row[edge_map[(u, v)]] = 1.0
                subtour_constraints.append(row)
                subtour_b_u.append(len(S) - 1.0)
