from collections import deque
from heapq import *


class HopCroftKarp:
    def __init__(self, n, m):
        self.n = n
        self.m = m
        self.G = [[] for _ in range(n)]
        self.RG = [[] for _ in range(m)]
        self.match_l = [-1] * n
        self.match_r = [-1] * m
        self.used = [0] * n
        self.time_stamp = 0

    def add_edges(self, u, v):
        self.G[u].append(v)

    def _build_argument_path(self):
        queue = deque()
        self.dist = [-1] * self.n
        for i in range(self.n):
            if self.match_l[i] == -1:
                queue.append(i)
                self.dist[i] = 0
        while queue:
            a = queue.popleft()
            for b in self.G[a]:
                c = self.match_r[b]
                if c >= 0 and self.dist[c] == -1:
                    self.dist[c] = self.dist[a] + 1
                    queue.append(c)

    def _find_min_dist_argument_path(self, a):
        self.used[a] = self.time_stamp
        for b in self.G[a]:
            c = self.match_r[b]
            if c < 0 or (
                self.used[c] != self.time_stamp
                and self.dist[c] == self.dist[a] + 1
                and self._find_min_dist_argument_path(c)
            ):
                self.match_r[b] = a
                self.match_l[a] = b
                return True
        return False

    def max_matching(self):
        while 1:
            self._build_argument_path()
            self.time_stamp += 1
            flow = 0
            for i in range(self.n):
                if self.match_l[i] == -1:
                    flow += self._find_min_dist_argument_path(i)
            if flow == 0:
                break
        ret = []
        for i in range(self.n):
            if self.match_l[i] >= 0:
                ret.append((i, self.match_l[i]))
        return ret


class UnionFind:
    def __init__(self, n):
        self.n = n
        self.parents = [-1] * n
        self.group = n

    def find(self, x):
        if self.parents[x] < 0:
            return x
        else:
            self.parents[x] = self.find(self.parents[x])
            return self.parents[x]

    def union(self, x, y):
        x = self.find(x)
        y = self.find(y)

        if x == y:
            return
        self.group -= 1
        if self.parents[x] > self.parents[y]:
            x, y = y, x

        self.parents[x] += self.parents[y]
        self.parents[y] = x

    def size(self, x):
        return -self.parents[self.find(x)]

    def same(self, x, y):
        return self.find(x) == self.find(y)

    def members(self, x):
        root = self.find(x)
        return [i for i in range(self.n) if self.find(i) == root]

    def roots(self):
        return [i for i, x in enumerate(self.parents) if x < 0]

    def group_count(self):
        return self.group

    def all_group_members(self):
        dic = {r: [] for r in self.roots()}
        for i in range(self.n):
            dic[self.find(i)].append(i)
        return dic

    def __str__(self):
        return "\n".join("{}: {}".format(r, self.members(r)) for r in self.roots())


def contract(deg, k):
    hq = []
    for i, d in enumerate(deg):
        hq.append([d, i])
    heapify(hq)
    UF = UnionFind(len(deg))
    while len(hq) >= 2:
        p = heappop(hq)
        q = heappop(hq)
        if p[0] + q[0] > k:
            continue
        p[0] += q[0]
        UF.union(p[1], q[1])
        heappush(hq, p)
    return UF


def build_k_regular_graph(n, m, A, B):
    dega = [0] * n
    degb = [0] * m
    for a in A:
        dega[a] += 1
    for b in B:
        degb[b] += 1
    K = max(*dega, *degb)

    UFa = contract(dega, K)
    ida = [-1] * n
    pa = 0
    for i in range(n):
        if UFa.find(i) == i:
            ida[i] = pa
            pa += 1

    UFb = contract(degb, K)
    idb = [-1] * m
    pb = 0
    for i in range(m):
        if UFb.find(i) == i:
            idb[i] = pb
            pb += 1

    p = max(pa, pb)
    dega = [0] * p
    degb = [0] * p

    C = []
    D = []
    for i in range(len(A)):
        u = ida[UFa.find(A[i])]
        v = idb[UFb.find(B[i])]
        C.append(u)
        D.append(v)
        dega[u] += 1
        degb[v] += 1
    j = 0
    for i in range(p):
        while dega[i] < K:
            while degb[j] == K:
                j += 1
            C.append(i)
            D.append(j)
            dega[i] += 1
            degb[j] += 1

    return K, p, C, D


def EdgeColoring(a, b, A, B):
    K, n, A, B = build_k_regular_graph(a, b, A, B)

    ord = [i for i in range(len(A))]
    ans = []

    def euler_trail(ord):
        V = 2 * n
        G = [[] for _ in range(V)]
        m = 0
        for i in ord:
            G[A[i]].append((B[i] + n, m))
            G[B[i] + n].append((A[i], m))
            m += 1
        used_v = [0] * V
        used_e = [0] * m
        ans = []
        for i in range(V):
            if used_v[i]:
                continue
            st = []
            ord2 = []
            st.append((i, -1))
            while st:
                id_ = st[-1][0]
                used_v[id_] = True
                if len(G[id_]) == 0:
                    ord2.append(st[-1][1])
                    st.pop()
                else:
                    e = G[id_][-1]
                    G[id_].pop()
                    if used_e[e[1]]:
                        continue
                    used_e[e[1]] = True
                    st.append(e)
            ord2.pop()
            ord2 = ord2[::-1]
            ans += ord2
        for i, a in enumerate(ans):
            ans[i] = ord[a]
        return ans

    def rec(ord, K):
        if K == 0:
            return
        elif K == 1:
            ans.append(ord)
            return
        elif K & 1:
            G = HopCroftKarp(n, n)
            for i in ord:
                G.add_edges(A[i], B[i])
            G.max_matching()
            lst = []
            ans.append([])
            for i in ord:
                if G.match_l[A[i]] == B[i]:
                    G.match_l[A[i]] = -1
                    ans[-1].append(i)
                else:
                    lst.append(i)
            rec(lst, K - 1)
        else:
            path = euler_trail(ord)
            L = []
            R = []
            for i, p in enumerate(path):
                if i & 1:
                    L.append(p)
                else:
                    R.append(p)
            rec(L, K // 2)
            rec(R, K // 2)

    rec(ord, K)
    return K, ans


def color_edges(commodities: dict):
    nodes = set()
    for src, dst in commodities.values():
        nodes.add(f"{src}-")
        nodes.add(f"{dst}+")
    nodes_mapping = {node: i for i, node in enumerate(nodes)}
    edges = [
        (nodes_mapping[f"{src}-"], nodes_mapping[f"{dst}+"]) for src, dst in commodities.values()
    ]

    l = r = len(nodes)
    m = len(edges)

    A = []
    B = []
    for src, dst in edges:
        A.append(src)
        B.append(dst)

    K, ans = EdgeColoring(l, r, A, B)
    colors = [-1] * m
    for i in range(len(ans)):
        for j in ans[i]:
            if j < m:
                colors[j] = i
    assignments = {}
    for conn_id, color in zip(commodities.keys(), colors):
        assignments[conn_id] = color

    return assignments
