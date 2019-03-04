import networkx as nx
import json
import pprint
import sys
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

def find_student_groups(pairs, min_group_size=2):
    """
    Find all maximal cliques in the graph (groups of students who all have some code in common)

    Returns
    dictionary listing the groups of students
    """
    graph = create_graph(pairs)
    cliques = nx.algorithms.clique.find_cliques(graph)
    clique_list = []

    for c in cliques:
        if len(c)>=min_group_size:
            clique_list.append({'students':c})
    out_dict = {'groups':clique_list}
    return out_dict

def output_groups_json(out_dict, filename):
    with open(filename, 'w') as outfile:
        json.dump(out_dict, outfile,indent=4)

def formatted_print(to_print, verbose = False):
    pp = pprint.PrettyPrinter(indent=4)
    if verbose:
        pp.pprint(to_print)

def check_interval_overlap(interval1,interval2):
    """
    Check if two line intervals have any lines in common
    Parameters
    ----------
    interval1 : tuple
        (from,to ,...,...)
    interval2 : tuple
        (from,to ,...,...)
    Returns
    -------
    True if they overlap, else false

    """
    latest_start = max(interval1[0],interval2[0])
    first_end = min(interval1[1],interval2[1])
    return first_end>latest_start


def find_cliques(graph,min_clique_size=3):
    """
    Find maximal cliques in the graph
    Parameters
    ----------
    graph : networkx graph
        Description of parameter `graph`.
    min_clique_size : int
    Returns
    -------
    list(clique)
    """
    cliques = nx.algorithms.clique.find_cliques(graph)
    clique_list = []
    for c in cliques:
        if len(c)>=min_clique_size:
            clique_list.append(c)
    return clique_list

def create_interval_graph(student,collaborations):
    """
    Given a student's file, we want to find out all other students that overlap with a particular line of code.
    The different matches can be thought of as a set of (from,to) line intervals in the student's code.
    The problem then reduces to finding maximal overlapping intervals.
    A maximum overlapping interval corresponds to a clique in an interval graph.
    https://en.wikipedia.org/wiki/Interval_graph

    Parameters
    ----------
    student : uuid
    collaborations : dictionary
        The data relating to codde matching with some code in 'student''s file
    Returns
    -------
    Networkx graph
    """
    intervals = []
    collaborators = collaborations.keys()
    interval_graph = nx.Graph()
    for c in collaborators:
        first_match = collaborations[c][0] #TODO replace with code to find the i_th match
        if first_match [0]['student'] == student:
            current_student_match_data = first_match [0]
        else:
            current_student_match_data = first_match [1]

        lines = current_student_match_data['lines']
        for l in lines.keys():
            intervals.append((lines[l]['from'],lines[l]['to'],c,l))
    intervals.sort()

    interval_graph.add_nodes_from(intervals)

    for i in range(len(intervals)):
        for j in range(i+1,len(intervals)):
            if check_interval_overlap(intervals[i],intervals[j]):
                interval_graph.add_edge(intervals[i],intervals[j])
    return interval_graph

def find_student_common_code(student,collaborations):
    """
    Find all multi-student collaborations that 'student' participates in

    ----------
    student : uuid
    collaborations : dictionary
        The data relating to codde matching with some code in 'student''s file
    Returns
    -------
    Dictionary
    """
    interval_graph = create_interval_graph(student,collaborations)
    cliques = find_cliques(interval_graph)
    formatted_clique_list = []
    for clique in cliques:
        range_start = sys.maxsize
        range_end = 0
        matches = {}
        formatted_clique = []
        for node in clique:

            if node[0]<range_start:
                range_start = node[0]

            if node[1]>range_end:
                range_end = node[1]

            collaborator_data = collaborations[node[2]][0]

            if collaborator_data[0]['student'] == node[2]:
                collaborator = collaborator_data[0]
            else:
                collaborator = collaborator_data[1]

            collaborator_lines = collaborator['lines'][node[3]]

            matches[collaborator['student']] = {'from':collaborator_lines['from'],'to':collaborator_lines['to']}

        clique_description_simplified = {}
        clique_description_simplified['matches'] = matches
        clique_description_simplified['from'] = range_start
        clique_description_simplified['to'] = range_end
        formatted_clique_list.append(clique_description_simplified)
    return formatted_clique_list

def find_multistudent_collaborations(data,verbose=False):
    """
    Find all collaborations with the same lines of code being used amongst multiple (3 or more) students

    Parameters
    ----------
    data : dictionary
        Description of parameter `data`.

    Returns
    -------
    dictionary
        List of all multi-student collaborations, indexed by student uuid
    """
    students = data.keys()
    out_dict = {}
    i=0
    for student in students:
        collaborating_students_data = data[student]
        common_code = find_student_common_code(student,collaborating_students_data)
        if len(common_code)==0:
            #TODO do we display students with no matches?
            formatted_print(common_code)
        out_dict[student] = common_code
    return out_dict

if __name__ == '__main__':
    with open('anon-line-refs.json') as data_file:
        data = json.load(data_file)
    out_dict= find_multistudent_collaborations(data)
    with open('test2.json', 'w') as outfile:
        json.dump(out_dict, outfile,indent=4)
