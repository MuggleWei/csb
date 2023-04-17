import typing


class KahnAlgo:
    """
    Kahn's algorithm
    """

    class Node:
        def __init__(self, idx):
            self.idx = idx
            self.to_list: typing.List[KahnAlgo.Node] = []
            self.in_degree = 0

    def sort(self, node_cnt, edges) -> typing.Optional[typing.List]:
        """
        Kahn's algorithm sort nodes
        :param node_cnt: total node count
        :param edges: edge list
        """
        nodes: typing.List[KahnAlgo.Node] = []
        for i in range(node_cnt):
            nodes.append(KahnAlgo.Node(i))

        for i in range(len(edges)):
            edge = edges[i]
            from_idx = edge[0]
            to_idx = edge[1]
            from_node = nodes[from_idx]
            to_node = nodes[to_idx]

            from_node.to_list.append(to_node)
            to_node.in_degree += 1

        s: typing.List[KahnAlgo.Node] = []
        for node in nodes:
            if node.in_degree == 0:
                s.append(node)

        l: typing.List[KahnAlgo.Node] = []
        while len(s) > 0:
            n = s.pop(0)
            l.append(n)

            for m in n.to_list:
                m.in_degree -= 1
                if m.in_degree == 0:
                    s.append(m)

        if len(l) == node_cnt:
            result = []
            for node in l:
                result.append(node.idx)
            return result
        else:
            return None
