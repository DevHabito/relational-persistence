"""Independent RP-S001-P01 exact recomputation using a disjoint-set union.

Deliberately does NOT import the original BFS/DFS experiment. The graph set,
mincut and failure subsets are independently reconstructed. Read-only replay.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
import hashlib
import json


ORIGINAL_REPORT_SHA256 = "6d825f055fcdc4955513218b56ec477900911f72c7e2ac7ada8f0c0cba36de19"
ORIGINAL_PATH = Path("docs/results/RP-S001-P01-first-run/audit.json")


def all_possible_edges():
    return tuple((i,j) for i in range(6) for j in range(i+1,6) if (i,j)!=(0,5))


def union_reachable(edges, blocked=(), all_nodes=False):
    parent = list(range(6))
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    forbidden = set(blocked)
    for index,(i,j) in enumerate(edges):
        if index in forbidden:
            continue
        a,b = root(i),root(j)
        if a != b:
            parent[a]=b
    return all(root(i)==root(0) for i in range(6)) if all_nodes else root(0)==root(5)


def terminal_cut_by_partitions(edges):
    result=9
    for mask in range(16):
        side={0}|{v for v in (1,2,3,4) if mask & (1<<(v-1))}
        crossing=sum((u in side)!=(v in side) for u,v in edges)
        result=min(result,crossing)
    return result


def degrees(edges):
    d=[0]*6
    for i,j in edges:
        d[i]+=1
        d[j]+=1
    return tuple(d)


def recompute():
    by_degree=defaultdict(list)
    histogram=Counter()
    source_graphs=0
    for graph in combinations(all_possible_edges(),8):
        d=degrees(graph)
        if d[0]!=2 or d[5]!=2 or not union_reachable(graph,all_nodes=True):
            continue
        if terminal_cut_by_partitions(graph)!=2:
            continue
        source_graphs+=1
        surviving=sum(union_reachable(graph,(i,j))
                      for i in range(8) for j in range(i+1,8))
        histogram[surviving]+=1
        by_degree[d].append((graph,surviving))
    possible=[]
    for degree, group in by_degree.items():
        for index,(graph,n) in enumerate(group):
            found=False
            for nextgraph,nextn in group[index+1:]:
                if nextn!=n:
                    possible.append((graph,nextgraph,degree,n,nextn))
                    found=True
                    break
            if found:break
    first=min(possible,key=lambda p:(p[0],p[1])) if possible else None
    return {
        "admissible_source_graphs":source_graphs,
        "full_labeled_degree_classes":len(by_degree),
        "degree_classes_with_at_least_two_members":sum(len(v)>=2 for v in by_degree.values()),
        "degree_classes_with_nonconstant_survival":sum(len({n for _,n in v})>1 for v in by_degree.values()),
        "survival_numerator_histogram":{str(k):histogram[k] for k in sorted(histogram)},
        "first_lexicographic_primary_witness": None if first is None else {
            "graph_A_edges":[list(edge) for edge in first[0]],
            "graph_B_edges":[list(edge) for edge in first[1]],
            "full_labeled_degree_vector":list(first[2]),
            "graph_A_surviving_two_edge_subsets":first[3],
            "graph_B_surviving_two_edge_subsets":first[4],
        },
    }


def verify_report(source=ORIGINAL_PATH):
    blob=source.read_bytes()
    if hashlib.sha256(blob).hexdigest()!=ORIGINAL_REPORT_SHA256:
        raise ValueError("First RP-S001 original JSON digest differs")
    record=json.loads(blob)
    result=recompute()
    for field in result:
        if field=="first_lexicographic_primary_witness":
            expected=record[field]
            if expected is None or result[field] is None:
                if expected != result[field]:
                    raise ValueError("First lex witness presence differs")
            elif any(expected[key]!=value for key,value in result[field].items()):
                raise ValueError("Independent DSU first lex witness differs")
        elif record[field]!=result[field]:
            raise ValueError("Independent DSU summary differs: "+field)
    if record["protocol_commit"]!="5f61ae5a3dc239bb0017fa09ced81a52d49df493":
        raise ValueError("Original protocol identity differs")
    if record["primary_decision"]!="SUMMARY_SUFFICIENCY_COUNTEREXAMPLE":
        raise ValueError("Original declared primary decision differs")
    if record["temporal_decision"]!="TEMPORAL_CORRELATION_CONTRAST":
        raise ValueError("Original declared temporal decision differs")
    return result


if __name__=="__main__":
    print(json.dumps(verify_report(),sort_keys=True,indent=2))
