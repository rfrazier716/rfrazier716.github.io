def build_tree(segments: np.ndarray, starting_segment: np.ndarray = None) -> nx.DiGraph:
    def bsp_helper(segments: np.ndarray, division_line: np.ndarray):
        ahead, behind, colinear = bisect(segments, division_line)  # get the bisected segments
        node_id = id(division_line)  # make your line hashable so it's usable as a node
        graph.add_node(node_id, line=division_line, colinear_segments=colinear)  # add the node to the graph
        if behind.size != 0:  # if there's any elements behind
            node_behind = bsp_helper(behind, behind[0])  # recursively call for all segments behind
            graph.add_edge(node_id, node_behind, position=-1)  # add an edge from this node to the behind node
        if ahead.size != 0:
            node_ahead = bsp_helper(ahead, ahead[0])  # recursively call for all segments in front
            graph.add_edge(node_id, node_ahead, position=1)  # add an edge from this node to the front node
        return node_id  # return the hashed id

    graph = nx.DiGraph()  # make a new directed graph
    if starting_segment is None:
        starting_segment = segments[0]

    # run the recursive helper function, which should add all nodes and edges
    bsp_helper(segments, starting_segment)
    return nx.relabel.convert_node_labels_to_integers(graph)