import functools
import gc

import numpy as np
import osmnx as ox
from networkx import write_gpickle, read_gpickle, relabel_nodes
import matplotlib.pyplot as plt

import bmm


# Load graph of Cambridge
def cambridge_graph():
    graph_dir = '/Users/samddd/Main/Data/bayesian-map-matching/graphs/Cambridge/'
    graph_name = 'cambridge_latest_utm_cleaned'
    graph_path = graph_dir + graph_name + '.graphml'

    graph = read_gpickle(graph_path)
    return graph


def remove_dead_ends(graph):
    pruned_graph = graph.copy()

    for u in graph.nodes:

        u_in_edges = graph.in_edges(u)
        u_out_edges = graph.out_edges(u)

        if len(u_out_edges) == 0 or (len(u_out_edges) == 1 and len(u_in_edges) == 1
                                     and list(u_in_edges)[0][::-1] in list(u_out_edges)):
            pruned_graph.remove_node(u)

    return pruned_graph


def download_simplify_cambridge_graph():
    graph_dir = '/Users/samddd/Main/Data/bayesian-map-matching/graphs/Cambridge/'
    graph_name = 'cambridge_latest_utm_cleaned'
    graph_path = graph_dir + graph_name + '.graphml'

    cambridge_ll_bbox = [52.245, 52.150, 0.220, 0.025]
    raw_graph = ox.graph_from_bbox(*cambridge_ll_bbox,
                                   truncate_by_edge=True,
                                   simplify=False,
                                   network_type='drive')

    projected_graph = ox.project_graph(raw_graph)

    # Removing dead-ends creates more dead-ends - so repeat a few times
    pruned_graph = projected_graph.copy()
    prune_iters = 25
    for i in range(prune_iters):
        pruned_graph = remove_dead_ends(pruned_graph)

    consolidated_graph = ox.consolidate_intersections(pruned_graph, tolerance=11)
    simplified_graph = ox.simplify_graph(consolidated_graph)

    # Relabel so that all node indices can be converted to float (otherwise buffered nodes contain -)
    node_map = {node: int(node.replace('-', '000')) if isinstance(node, str) else node for node in
                simplified_graph.nodes}
    rn_graph = relabel_nodes(simplified_graph, node_map)

    write_gpickle(rn_graph, graph_path)

    return simplified_graph


# Clear lru_cache
def clear_cache():
    gc.collect()
    wrappers = [
        a for a in gc.get_objects()
        if isinstance(a, functools._lru_cache_wrapper)]

    for wrapper in wrappers:
        wrapper.cache_clear()


# Function to sample a random point on the graph
def random_positions(graph, n=1):
    edges_arr = np.array(graph.edges)
    n_edges = len(edges_arr)

    edge_selection_indices = np.random.choice(n_edges, n)
    edge_selection = edges_arr[edge_selection_indices]

    random_alphas = np.random.uniform(size=(n, 1))

    positions = np.concatenate((edge_selection, random_alphas), axis=1)
    return positions


# Function to sample a route (given a start position, route length and time_interval (assumed constant))
def sample_route(graph, model, time_interval, length, start_position=None, cart_route=False, observations=False):
    route = np.zeros((1, 7))

    if start_position is None:
        start_position = random_positions(graph, 1)

    route[0, 1:5] = start_position

    for t in range(1, length):
        prev_pos = route[-1:].copy()
        prev_pos[0, 0] = 0

        # Sample a distance
        sampled_dist = model.distance_prior_sample(time_interval)

        # Evaluate all possible routes
        possible_routes = bmm.get_possible_routes(graph, prev_pos, sampled_dist)

        if possible_routes is None or all(p is None for p in possible_routes):
            break

        # Prior route probabilities given distance
        num_poss_routes = len(possible_routes)
        if num_poss_routes == 0:
            break
        possible_routes_probs = np.zeros(num_poss_routes)
        for i in range(num_poss_routes):
            if possible_routes[i] is None:
                continue

            intersection_col = possible_routes[i][:-1, 5]
            possible_routes_probs[i] = np.prod(1 / intersection_col[intersection_col > 1]) \
                                       * model.intersection_penalisation ** len(intersection_col)

        # Normalise
        possible_routes_probs /= np.sum(possible_routes_probs)

        # Choose one
        sampled_route_index = np.random.choice(num_poss_routes, 1, p=possible_routes_probs)[0]
        sampled_route = possible_routes[sampled_route_index]

        sampled_route[-1, 0] = route[-1, 0] + time_interval

        route = np.append(route, sampled_route, axis=0)

    if cart_route or observations:
        cartesianised_route_out = bmm.cartesianise_path(graph, route, t_column=True, observation_time_only=True)

        if observations:
            observations_out = cartesianised_route_out \
                               + model.gps_sd * np.random.normal(size=cartesianised_route_out.shape)
            if cart_route:
                return route, cartesianised_route_out, observations_out
            else:
                return route, observations_out
        else:
            return route, cartesianised_route_out
    else:
        return route


# RMSE given particle cloud
def rmse(graph, particles, truth, each_time=False):
    if isinstance(truth, np.ndarray) and truth.shape[1] > 4:
        truth = bmm.cartesianise_path(graph, truth, t_column=True, observation_time_only=True)

    # N x T x 2
    obs_time_particles = np.zeros((len(particles), len(truth), 2))
    for i, particle in enumerate(particles):
        obs_time_particles[i] = bmm.cartesianise_path(graph, particle, t_column=True, observation_time_only=True)

    squared_error = np.square(obs_time_particles - truth)

    if each_time:
        return np.sqrt(np.mean(squared_error, axis=(0, 2)))
    else:
        return np.sqrt(np.mean(squared_error))


# RMSE given repeated particle clouds
def rmse_multiple_routes(graph, particles_arr, truth, each_time=False, average_over_routes=True):
    rmse_arr = np.zeros((len(particles_arr), len(truth)) if each_time else len(particles_arr))

    for i, particle in enumerate(particles_arr):
        if particle is not None:
            rmse_arr[i] = rmse(graph, particle, truth, each_time)

    non_zero_rows = np.all(rmse_arr > 0, axis=1)

    return np.mean(rmse_arr[non_zero_rows], axis=0) if average_over_routes else rmse_arr[non_zero_rows]


# Proportion of particles on correct sub-route
def prop_edges_incorrect(particles: bmm.MMParticles,
                         true_route):
    out_arr = np.zeros(particles.m)

    for i in range(particles.m):
        if i == 0:
            true_first_edge = true_route[0, 1:4]
            particle_first_edges = [np.array_equal(p[0, 1:4], true_first_edge) for p in particles]
            out_arr[0] = 1 - sum(particle_first_edges) / particles.n
        else:
            prev_time = particles.observation_times[i - 1]
            current_time = particles.observation_times[i]

            correct_arr_n = np.zeros(particles.n, dtype=bool)

            true_prev_ind = np.where(true_route[:, 0] == prev_time)[0][0]
            true_curr_ind = np.where(true_route[:, 0] == current_time)[0][0]

            true_sub_route = true_route[true_prev_ind:(true_curr_ind + 1), 1:4]

            for j, p in enumerate(particles):
                prev_ind = np.where(p[:, 0] == prev_time)[0][0]
                curr_ind = np.where(p[:, 0] == current_time)[0][0]

                sub_route = p[prev_ind:(curr_ind + 1), 1:4]

                correct_arr_n[j] = np.array_equal(sub_route, true_sub_route)

            out_arr[i] = 1 - correct_arr_n.sum() / particles.n

    return out_arr


# Average correct sub-routes given repeated particle clouds
def prop_edges_incorrect_multiple_routes(particles_arr, true_route, average_over_routes=True):
    pec_arr = np.empty((len(particles_arr), particles_arr[0].m), dtype=object)

    for i, particle in enumerate(particles_arr):
        if particle is not None:
            pec_arr[i] = prop_edges_incorrect(particle, true_route)

    non_empty_rows = np.all(pec_arr != None, axis=1)

    return np.mean(pec_arr[non_empty_rows], axis=0) if average_over_routes else pec_arr[non_empty_rows]


# Plot RMSE
def plot_rmse(graph, setup_dict, true_polyline, fl_pf_routes, fl_bsi_routes, ffbsi_routes, save_dir):
    lags = setup_dict['lags']
    t_linspace = np.linspace(0, (setup_dict['route_length'] - 1) * setup_dict['time_interval'],
                             setup_dict['route_length'])

    fontsize = 8
    shift = 0.08

    l_start = 0.01
    u_start = 0.85

    lines = [None] * (len(lags) + 1)

    fig, axes = plt.subplots(3, 2, sharex='all', sharey='all', figsize=(8, 6))
    for j, n in enumerate(setup_dict['n_samps']):
        for k, lag in enumerate(lags):
            axes[j, 0].plot(t_linspace, rmse_multiple_routes(graph, fl_pf_routes[..., k, j], true_polyline,
                                                             each_time=True, average_over_routes=True),
                            label=f'Lag: {lag}')
            lines[k], = axes[j, 1].plot(t_linspace,
                                        rmse_multiple_routes(graph, fl_bsi_routes[..., k, j], true_polyline,
                                                             each_time=True),
                                        label=f'Lag: {lag}')

        ffbsi_j_rmse = rmse_multiple_routes(graph, ffbsi_routes[..., j], true_polyline, each_time=True)

        lines[len(lags)], = axes[j, 0].plot(t_linspace, ffbsi_j_rmse, label='FFBSi')
        axes[j, 1].plot(t_linspace, ffbsi_j_rmse, label='FFBSi')

    for j, n in enumerate(setup_dict['n_samps']):
        for k, lag in enumerate(lags):
            pf_avtime = np.mean([p.time for p in fl_pf_routes[..., k, j] if p is not None])
            axes[j, 0].text(l_start, u_start - k * shift, "{:.1f}".format(pf_avtime),
                            color=lines[k].get_color(),
                            fontsize=fontsize, transform=axes[j, 0].transAxes)
            bsi_avtime = np.mean([p.time for p in fl_bsi_routes[..., k, j] if p is not None])
            axes[j, 1].text(l_start, u_start - k * shift, "{:.1f}".format(bsi_avtime),
                            color=lines[k].get_color(),
                            fontsize=fontsize, transform=axes[j, 1].transAxes)
        ffbsi_avtime = np.mean([p.time for p in ffbsi_routes[..., j] if p is not None])
        axes[j, 0].text(l_start, u_start - len(lags) * shift, "{:.1f}".format(ffbsi_avtime),
                        color=lines[len(lags)].get_color(),
                        fontsize=fontsize, transform=axes[j, 0].transAxes)
        axes[j, 1].text(l_start, u_start - len(lags) * shift, "{:.1f}".format(ffbsi_avtime),
                        color=lines[len(lags)].get_color(),
                        fontsize=fontsize, transform=axes[j, 1].transAxes)

        axes[j, 0].text(l_start, u_start + shift, "Time (s)",
                        fontsize=fontsize, transform=axes[j, 0].transAxes)

        axes[j, 1].text(l_start, u_start + shift, "Time (s)",
                        fontsize=fontsize, transform=axes[j, 1].transAxes)

        axes[j, 0].set_ylabel(f'RMSE   N={n}')

    axes[-1, 0].set_xlabel('t')
    axes[-1, 1].set_xlabel('t')

    axes[0, 0].set_title('FL Particle Filter')
    axes[0, 1].set_title('FL (Partial) Backward Simulation')

    plt.legend(loc='upper right')

    plt.tight_layout()

    plt.savefig(save_dir + 'route_rmse_compare.png', dpi=350)

    return fig, axes


# Plot proportion routes correct
def plot_pei(setup_dict, true_route, fl_pf_routes, fl_bsi_routes, ffbsi_routes, save_dir):
    lags = setup_dict['lags']
    t_linspace = np.linspace(0, (setup_dict['route_length'] - 1) * setup_dict['time_interval'],
                             setup_dict['route_length'])

    fontsize = 8
    shift = 0.08

    l_start = 0.01
    u_start = 0.85

    lines = [None] * (len(lags) + 1)

    fig, axes = plt.subplots(3, 2, sharex='all', sharey='all', figsize=(8, 6))
    for j, n in enumerate(setup_dict['n_samps']):
        for k, lag in enumerate(lags):
            axes[j, 0].plot(t_linspace, prop_edges_incorrect_multiple_routes(fl_pf_routes[..., k, j], true_route),
                            label=f'Lag: {lag}')
            lines[k], = axes[j, 1].plot(t_linspace,
                                        prop_edges_incorrect_multiple_routes(fl_bsi_routes[..., k, j], true_route),
                                        label=f'Lag: {lag}')

        ffbsi_j_pec = prop_edges_incorrect_multiple_routes(ffbsi_routes[..., j], true_route)

        lines[len(lags)], = axes[j, 0].plot(t_linspace, ffbsi_j_pec, label='FFBSi')
        axes[j, 1].plot(t_linspace, ffbsi_j_pec, label='FFBSi')

    for j, n in enumerate(setup_dict['n_samps']):
        for k, lag in enumerate(lags):
            pf_avtime = np.mean([p.time for p in fl_pf_routes[..., k, j] if p is not None])
            axes[j, 0].text(l_start, u_start - k * shift, "{:.1f}".format(pf_avtime),
                            color=lines[k].get_color(),
                            fontsize=fontsize, transform=axes[j, 0].transAxes)
            bsi_avtime = np.mean([p.time for p in fl_bsi_routes[..., k, j] if p is not None])
            axes[j, 1].text(l_start, u_start - k * shift, "{:.1f}".format(bsi_avtime),
                            color=lines[k].get_color(),
                            fontsize=fontsize, transform=axes[j, 1].transAxes)
        ffbsi_avtime = np.mean([p.time for p in ffbsi_routes[..., j] if p is not None])
        axes[j, 0].text(l_start, u_start - len(lags) * shift, "{:.1f}".format(ffbsi_avtime),
                        color=lines[len(lags)].get_color(),
                        fontsize=fontsize, transform=axes[j, 0].transAxes)
        axes[j, 1].text(l_start, u_start - len(lags) * shift, "{:.1f}".format(ffbsi_avtime),
                        color=lines[len(lags)].get_color(),
                        fontsize=fontsize, transform=axes[j, 1].transAxes)

        axes[j, 0].text(l_start, u_start + shift, "Time (s)",
                        fontsize=fontsize, transform=axes[j, 0].transAxes)

        axes[j, 1].text(l_start, u_start + shift, "Time (s)",
                        fontsize=fontsize, transform=axes[j, 1].transAxes)

        axes[j, 0].set_ylabel(f'Incorrect Edges  N={n}')
        axes[j, 0].set_yticks([0, 0.5, 1])

    axes[-1, 0].set_xlabel('t')
    axes[-1, 1].set_xlabel('t')

    axes[0, 0].set_title('FL Particle Filter')
    axes[0, 1].set_title('FL (Partial) Backward Simulation')

    plt.legend(loc='upper right')

    plt.tight_layout()

    plt.savefig(save_dir + 'route_incorrect_edges_compare.png', dpi=350)

    return fig, axes

