import networkx as nx
import json

def parse_json(filename='student-anon-pair.json' ):
    """
    Test function - retreive pairs from student-anon-pair.json
    Returns
    list(string)
        Returns a list of pairs of students
    """

    with open(filename) as data_file:
        data = json.load(data_file)
    return data['pairs']

def create_graph(pair_list):
     G = nx.Graph()
     G.add_edges_from(pair_list)
     return G

def find_student_groups(pairs):
    """
    Find all maximal cliques in the graph (groups of students who all have some code in common)

    Returns
    dictionary listing the groups of students
    """
    graph = create_graph(pairs)
    cliques = nx.algorithms.clique.find_cliques(graph)
    clique_list = []

    for c in cliques:
        if len(c)>1:
            clique_list.append({'students':c})
    out_dict = {'groups':clique_list}
    return out_dict

def output_groups_json(out_dict, filename):
    with open(filename, 'w') as outfile:
        json.dump(out_dict, outfile,indent=4)


if __name__ == '__main__':
    pairs = parse_json('student-anon-pairs.json')
    outdict = find_student_groups(pairs)
    output_groups_json(outdict,'student-anon-groups.json')
