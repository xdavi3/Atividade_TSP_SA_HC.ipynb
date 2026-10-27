import os
import math
import time
import json
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Set style for publication quality plots
plt.rcParams['figure.dpi'] = 150
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8

# 1. Load wi29 dataset
wi29_raw = """
1 20833.3333 17100.0000
2 20900.0000 17066.6667
3 21300.0000 13016.6667
4 21600.0000 14150.0000
5 21600.0000 14966.6667
6 21600.0000 16500.0000
7 22183.3333 13133.3333
8 22583.3333 14300.0000
9 22683.3333 12716.6667
10 23616.6667 15866.6667
11 23700.0000 15933.3333
12 23883.3333 14533.3333
13 24166.6667 13250.0000
14 25149.1667 12365.8333
15 26133.3333 14500.0000
16 26150.0000 10550.0000
17 26283.3333 12766.6667
18 26433.3333 13433.3333
19 26550.0000 13850.0000
20 26733.3333 11683.3333
21 27026.1111 13051.9444
22 27096.1111 13415.8333
23 27153.6111 13203.3333
24 27166.6667 9833.3333
25 27233.3333 10450.0000
26 27233.3333 11783.3333
27 27266.6667 10383.3333
28 27433.3333 12400.0000
29 27462.5000 12992.2222
"""

coords = []
for line in wi29_raw.strip().split("\n"):
    parts = line.strip().split()
    if len(parts) == 3:
        coords.append([float(parts[1]), float(parts[2])])

cities = np.array(coords)
num_cities = len(cities)
OPTIMAL_DISTANCE = 27603.0
OPTIMAL_TOUR = [0, 1, 5, 9, 10, 11, 14, 18, 17, 16, 20, 21, 22, 28, 27, 25, 19, 24, 26, 23, 15, 13, 12, 8, 6, 2, 3, 7, 4]

# Distance functions
def calculate_distance(city_a, city_b):
    dx = city_a[0] - city_b[0]
    dy = city_a[1] - city_b[1]
    return round(math.sqrt(dx**2 + dy**2))

def generate_distance_matrix(cities):
    n = len(cities)
    matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            matrix[i, j] = calculate_distance(cities[i], cities[j])
    return matrix

dist_matrix = generate_distance_matrix(cities)

def total_distance(route, distance_matrix):
    total = 0
    n = len(route)
    for i in range(n - 1):
        total += distance_matrix[route[i], route[i + 1]]
    total += distance_matrix[route[-1], route[0]]
    return total

# Neighborhood structures
def swap_neighbor(route):
    new_route = list(route)
    n = len(new_route)
    i, j = random.sample(range(n), 2)
    new_route[i], new_route[j] = new_route[j], new_route[i]
    return new_route

def two_opt_neighbor(route):
    new_route = list(route)
    n = len(new_route)
    i, j = sorted(random.sample(range(n), 2))
    new_route[i:j+1] = new_route[i:j+1][::-1]
    return new_route

# Simulated Annealing
def simulated_annealing(cities, distance_matrix, initial_temperature=2000.0, cooling_rate=0.998, iterations=5000, nrep=30, neighbor_fn=swap_neighbor, seed=None, track_history=False):
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
        
    n = len(cities)
    current_route = list(np.random.permutation(n))
    current_distance = total_distance(current_route, distance_matrix)
    
    best_route = list(current_route)
    best_distance = current_distance
    
    temperature = initial_temperature
    
    history = {
        'iteration': [],
        'current_dist': [],
        'best_dist': [],
        'temp': [],
        'accept_prob': []
    } if track_history else None
    
    start_time = time.time()
    
    for it in range(iterations):
        for _ in range(nrep):
            new_route = neighbor_fn(current_route)
            new_distance = total_distance(new_route, distance_matrix)
            
            delta = current_distance - new_distance
            if delta > 0:
                p = 1.0
            else:
                p = math.exp(delta / temperature) if temperature > 1e-12 else 0.0
                
            if random.random() < p:
                current_route = new_route
                current_distance = new_distance
                
                if current_distance < best_distance:
                    best_route = list(current_route)
                    best_distance = current_distance
                    
        temperature *= cooling_rate
        
        if track_history and it % 10 == 0:
            history['iteration'].append(it)
            history['current_dist'].append(current_distance)
            history['best_dist'].append(best_distance)
            history['temp'].append(temperature)
            history['accept_prob'].append(p)
            
    elapsed = time.time() - start_time
    return best_route, best_distance, elapsed, history

# Hill-Climbing (Stochastic First-Choice)
def hill_climbing(cities, distance_matrix, max_evaluations=150000, max_stagnant=15000, neighbor_fn=swap_neighbor, seed=None, track_history=False):
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
        
    n = len(cities)
    current_route = list(np.random.permutation(n))
    current_distance = total_distance(current_route, distance_matrix)
    
    best_route = list(current_route)
    best_distance = current_distance
    
    history = {
        'evaluation': [],
        'best_dist': []
    } if track_history else None
    
    start_time = time.time()
    stagnant_count = 0
    
    for eval_count in range(max_evaluations):
        new_route = neighbor_fn(current_route)
        new_distance = total_distance(new_route, distance_matrix)
        
        if new_distance < current_distance:
            current_route = new_route
            current_distance = new_distance
            best_route = list(current_route)
            best_distance = current_distance
            stagnant_count = 0
        else:
            stagnant_count += 1
            if stagnant_count >= max_stagnant:
                break
                
        if track_history and eval_count % 500 == 0:
            history['evaluation'].append(eval_count)
            history['best_dist'].append(best_distance)
            
    elapsed = time.time() - start_time
    return best_route, best_distance, elapsed, history

# Run 30 repetitions for statistical robustness
N_RUNS = 30
seeds = [1000 + i * 37 for i in range(N_RUNS)]

results = {
    'SA_Swap': [],
    'SA_2opt': [],
    'HC_Swap': [],
    'HC_2opt': []
}

print(f"Running benchmark with {N_RUNS} repetitions...")

# Run SA Swap
for s in seeds:
    b_route, b_dist, el, _ = simulated_annealing(cities, dist_matrix, initial_temperature=2000, cooling_rate=0.998, iterations=4000, nrep=25, neighbor_fn=swap_neighbor, seed=s)
    gap = ((b_dist - OPTIMAL_DISTANCE) / OPTIMAL_DISTANCE) * 100.0
    results['SA_Swap'].append({'seed': s, 'distance': b_dist, 'time': el, 'gap_percent': gap, 'route': b_route})

# Run SA 2-opt
for s in seeds:
    b_route, b_dist, el, _ = simulated_annealing(cities, dist_matrix, initial_temperature=2000, cooling_rate=0.998, iterations=4000, nrep=25, neighbor_fn=two_opt_neighbor, seed=s)
    gap = ((b_dist - OPTIMAL_DISTANCE) / OPTIMAL_DISTANCE) * 100.0
    results['SA_2opt'].append({'seed': s, 'distance': b_dist, 'time': el, 'gap_percent': gap, 'route': b_route})

# Run HC Swap
for s in seeds:
    b_route, b_dist, el, _ = hill_climbing(cities, dist_matrix, max_evaluations=150000, max_stagnant=15000, neighbor_fn=swap_neighbor, seed=s)
    gap = ((b_dist - OPTIMAL_DISTANCE) / OPTIMAL_DISTANCE) * 100.0
    results['HC_Swap'].append({'seed': s, 'distance': b_dist, 'time': el, 'gap_percent': gap, 'route': b_route})

# Run HC 2-opt
for s in seeds:
    b_route, b_dist, el, _ = hill_climbing(cities, dist_matrix, max_evaluations=150000, max_stagnant=15000, neighbor_fn=two_opt_neighbor, seed=s)
    gap = ((b_dist - OPTIMAL_DISTANCE) / OPTIMAL_DISTANCE) * 100.0
    results['HC_2opt'].append({'seed': s, 'distance': b_dist, 'time': el, 'gap_percent': gap, 'route': b_route})

print("Benchmark completed. Computing summary statistics...")

summary = []
for algo, data in results.items():
    dists = [d['distance'] for d in data]
    times = [d['time'] for d in data]
    gaps = [d['gap_percent'] for d in data]
    
    summary.append({
        'Algoritmo': algo,
        'Melhor Custo (Min)': np.min(dists),
        'Custo Médio': np.mean(dists),
        'Desvio Padrão (Custo)': np.std(dists),
        'Pior Custo (Max)': np.max(dists),
        'Gap Médio (%)': np.mean(gaps),
        'Menor Gap (%)': np.min(gaps),
        'Tempo Médio (s)': np.mean(times),
        'Desvio Padrão (Tempo)': np.std(times)
    })

df_summary = pd.DataFrame(summary)
print(df_summary.to_string(index=False))

# Save summary to CSV
df_summary.to_csv("benchmark_summary.csv", index=False)

# Convert routes and numpy types for JSON serialization
results_serializable = {}
for k, v in results.items():
    results_serializable[k] = []
    for item in v:
        results_serializable[k].append({
            'seed': int(item['seed']),
            'distance': float(item['distance']),
            'time': float(item['time']),
            'gap_percent': float(item['gap_percent']),
            'route': [int(x) for x in item['route']]
        })

with open("benchmark_results.json", "w") as f:
    json.dump(results_serializable, f, indent=2)

# Generate detailed plots
output_dir = "plots"
os.makedirs(output_dir, exist_ok=True)

# 1. Plot comparison of tours (Initial, HC Swap, SA Swap/2opt, Optimal)
best_sa_run = min(results['SA_Swap'], key=lambda x: x['distance'])
best_hc_run = min(results['HC_Swap'], key=lambda x: x['distance'])
random.seed(42)
initial_route = list(np.random.permutation(num_cities))
initial_dist = total_distance(initial_route, dist_matrix)

fig, axes = plt.subplots(2, 2, figsize=(14, 12))

def plot_tour_on_ax(ax, route, title, dist, color_line, optimal_ref=None):
    c_seq = cities[route + [route[0]]]
    ax.scatter(cities[:, 0], cities[:, 1], color='#e74c3c', s=60, zorder=5, edgecolors='black', linewidth=0.5)
    for idx, (x, y) in enumerate(cities):
        ax.annotate(str(idx + 1), (x, y), textcoords="offset points", xytext=(0, 6), ha='center', fontsize=8, fontweight='bold', color='#2c3e50')
    ax.plot(c_seq[:, 0], c_seq[:, 1], color=color_line, linewidth=2, alpha=0.85, label=f'Distância: {dist:,.0f}')
    ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
    ax.set_xlabel('Coordenada X (Longitude)', fontsize=10)
    ax.set_ylabel('Coordenada Y (Latitude)', fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(loc='upper right', framealpha=0.9)

plot_tour_on_ax(axes[0, 0], initial_route, "1. Rota Inicial Aleatória", initial_dist, '#7f8c8d')
plot_tour_on_ax(axes[0, 1], best_hc_run['route'], f"2. Melhor Rota Hill-Climbing (Swap)", best_hc_run['distance'], '#e67e22')
plot_tour_on_ax(axes[1, 0], best_sa_run['route'], f"3. Melhor Rota Simulated Annealing", best_sa_run['distance'], '#27ae60')
plot_tour_on_ax(axes[1, 1], OPTIMAL_TOUR, f"4. Solução Ótima Conhecida (Benchmark)", OPTIMAL_DISTANCE, '#2980b9')

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "comparacao_rotas.png"), dpi=200)
plt.close()

# 2. Boxplots of metrics
fig, axes = plt.subplots(1, 3, figsize=(16, 5))

algo_labels = ['SA (Swap)', 'SA (2-opt)', 'HC (Swap)', 'HC (2-opt)']
colors = ['#2ecc71', '#27ae60', '#e67e22', '#d35400']

# Custo
costs_data = [[d['distance'] for d in results[k]] for k in ['SA_Swap', 'SA_2opt', 'HC_Swap', 'HC_2opt']]
bplot1 = axes[0].boxplot(costs_data, tick_labels=algo_labels, patch_artist=True)
for patch, color in zip(bplot1['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
axes[0].axhline(OPTIMAL_DISTANCE, color='red', linestyle='--', label=f'Ótimo ({OPTIMAL_DISTANCE:,.0f})')
axes[0].set_title("Distribuição do Comprimento da Rota", fontweight='bold')
axes[0].set_ylabel("Distância Total")
axes[0].legend()
axes[0].grid(True, linestyle=':', alpha=0.6)

# Gap (%)
gap_data = [[d['gap_percent'] for d in results[k]] for k in ['SA_Swap', 'SA_2opt', 'HC_Swap', 'HC_2opt']]
bplot2 = axes[1].boxplot(gap_data, tick_labels=algo_labels, patch_artist=True)
for patch, color in zip(bplot2['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
axes[1].set_title("Gap Relativo ao Valor Ótimo (%)", fontweight='bold')
axes[1].set_ylabel("Gap (%)")
axes[1].grid(True, linestyle=':', alpha=0.6)

# Tempo (s)
time_data = [[d['time'] for d in results[k]] for k in ['SA_Swap', 'SA_2opt', 'HC_Swap', 'HC_2opt']]
bplot3 = axes[2].boxplot(time_data, tick_labels=algo_labels, patch_artist=True)
for patch, color in zip(bplot3['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
axes[2].set_title("Tempo de Execução (segundos)", fontweight='bold')
axes[2].set_ylabel("Segundos (s)")
axes[2].grid(True, linestyle=':', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "boxplots_comparativos.png"), dpi=200)
plt.close()

# 3. Convergence curve single run history comparison
print("Tracking detailed history for convergence plot...")
_, _, _, sa_hist = simulated_annealing(cities, dist_matrix, initial_temperature=2000, cooling_rate=0.998, iterations=5000, nrep=30, neighbor_fn=swap_neighbor, seed=42, track_history=True)
_, _, _, hc_hist = hill_climbing(cities, dist_matrix, max_evaluations=150000, max_stagnant=15000, neighbor_fn=swap_neighbor, seed=42, track_history=True)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Simulated Annealing convergence
ax1.plot(sa_hist['iteration'], sa_hist['current_dist'], label='Solução Corrente', color='#bdc3c7', alpha=0.7)
ax1.plot(sa_hist['iteration'], sa_hist['best_dist'], label='Melhor Encontrada (SA)', color='#27ae60', linewidth=2)
ax1.axhline(OPTIMAL_DISTANCE, color='red', linestyle='--', label=f'Ótimo Global ({OPTIMAL_DISTANCE:,.0f})')
ax1.set_title("Convergência do Simulated Annealing (wi29)", fontweight='bold')
ax1.set_xlabel("Iterações de Resfriamento")
ax1.set_ylabel("Distância")
ax1.legend()
ax1.grid(True, linestyle=':', alpha=0.6)

# Hill Climbing convergence
ax2.plot(hc_hist['evaluation'], hc_hist['best_dist'], label='Melhor Encontrada (HC)', color='#e67e22', linewidth=2)
ax2.axhline(OPTIMAL_DISTANCE, color='red', linestyle='--', label=f'Ótimo Global ({OPTIMAL_DISTANCE:,.0f})')
ax2.set_title("Convergência do Hill-Climbing (wi29)", fontweight='bold')
ax2.set_xlabel("Avaliações de Vizinhança")
ax2.set_ylabel("Distância")
ax2.legend()
ax2.grid(True, linestyle=':', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "curvas_convergencia.png"), dpi=200)
plt.close()

# 4. Teacher's 4-panel dashboard plot for SA
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(13, 9))

# Path
best_sa_seq = cities[best_sa_run['route'] + [best_sa_run['route'][0]]]
ax1.plot(best_sa_seq[:, 0], best_sa_seq[:, 1], color='#2980b9', linewidth=2)
ax1.scatter(cities[:, 0], cities[:, 1], color='#e74c3c', s=45, zorder=5)
ax1.set_title("Melhor Caminho Encontrado (SA)", fontweight='bold')
ax1.set_xlabel("X (Longitude)")
ax1.set_ylabel("Y (Latitude)")
ax1.grid(True, linestyle=':', alpha=0.6)

# Distances
ax2.plot(sa_hist['iteration'], sa_hist['current_dist'], label='Atual', color='#95a5a6', alpha=0.6)
ax2.plot(sa_hist['iteration'], sa_hist['best_dist'], label='Melhor', color='#27ae60', linewidth=2)
ax2.set_title("Evolução da Distância", fontweight='bold')
ax2.set_xlabel("Iterações")
ax2.set_ylabel("Custo")
ax2.legend()
ax2.grid(True, linestyle=':', alpha=0.6)

# Acceptance prob
# Subsample for clear scatter
sub_indices = list(range(0, len(sa_hist['iteration']), 3))
sub_it = [sa_hist['iteration'][i] for i in sub_indices]
sub_p = [sa_hist['accept_prob'][i] for i in sub_indices]
colors = ['#3498db' if p >= 0.999 else '#e74c3c' for p in sub_p]
ax3.scatter(sub_it, sub_p, c=colors, s=8, alpha=0.6)
ax3.set_ylim([-0.05, 1.05])
ax3.set_title("Probabilidade de Aceitação (Azul=Melhoria, Vermelho=Piora)", fontweight='bold')
ax3.set_xlabel("Iterações")
ax3.set_ylabel("Probabilidade")
ax3.grid(True, linestyle=':', alpha=0.6)

# Temperature
ax4.plot(sa_hist['iteration'], sa_hist['temp'], color='#8e44ad', linewidth=2)
ax4.set_title("Decaimento da Temperatura", fontweight='bold')
ax4.set_xlabel("Iterações")
ax4.set_ylabel("Temperatura")
ax4.grid(True, linestyle=':', alpha=0.6)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "painel_sa_instrumentado.png"), dpi=200)
plt.close()

print("All plots generated successfully in ./plots/ directory!")
