package ch.ethz.systems.floodns.ext.utils;

import org.apache.commons.lang3.tuple.ImmutablePair;

import java.util.*;

public class EdgeColoring {

    public static Map<Integer, Integer> colorEdges(Map<Integer, ImmutablePair<Integer, Integer>> commodities) {
        HashSet<String> nodes = new HashSet<>();
        for (ImmutablePair<Integer, Integer> conn : commodities.values()) {
            nodes.add(conn.getKey() + "-");
            nodes.add(conn.getValue() + "+");
        }
        HashMap<String, Integer> nodes_mapping = new HashMap<>();
        int idx = 0;
        for (String node : nodes) {
            nodes_mapping.put(node, idx);
            idx++;
        }

        List<ImmutablePair<Integer, Integer>> edges = new ArrayList<>();

        for (ImmutablePair<Integer, Integer> conn : commodities.values()) {
            String src = conn.getKey() + "-";
            String dst = conn.getValue() + "+";
            edges.add(new ImmutablePair<>(nodes_mapping.get(src), nodes_mapping.get(dst)));
        }

        int l = nodes.size();
        int r = nodes.size();
        int m = edges.size();
        int[] A = new int[m];
        int[] B = new int[m];

        for (int i = 0; i < m; i++) {
            A[i] = edges.get(i).getKey();
            B[i] = edges.get(i).getValue();
        }

        RegularGraph ret = buildKRegularGraph(l, r, A, B);
        int K = ret.getK();
        List<List<Integer>> ans = new ArrayList<>();
        List<Integer> ord = new ArrayList<>();
        for (int i = 0; i < A.length; i++) {
            ord.add(i);
        }

        rec(ret.getC(), ret.getD(), ord, K, ans, ret.getP());
        int[] colors = new int[m];

        for (int i = 0; i < ans.size(); i++) {
            for (int j : ans.get(i)) {
                if (j < m) {
                    colors[j] = i;
                }
            }
        }

        Map<Integer, Integer> assignments = new HashMap<>();

        for (Map.Entry<Integer, ImmutablePair<Integer, Integer>> entry : commodities.entrySet()) {
            assignments.put(entry.getKey(), colors[entry.getValue().getKey()]);
        }

        return assignments;
    }

    private static RegularGraph buildKRegularGraph(int n, int m, int[] A, int[] B) {
        int[] dega = new int[n];
        int[] degb = new int[m];

        for (int a : A) {
            dega[a]++;
        }

        for (int b : B) {
            degb[b]++;
        }

        int K = Math.max(Arrays.stream(dega).max().getAsInt(), Arrays.stream(degb).max().getAsInt());
        UnionFind UFa = contract(dega, K);
        int[] ida = new int[n];
        int pa = 0;

        for (int i = 0; i < n; i++) {
            if (UFa.find(i) == i) {
                ida[i] = pa;
                pa++;
            }
        }

        UnionFind UFb = contract(degb, K);
        int[] idb = new int[m];
        int pb = 0;

        for (int i = 0; i < m; i++) {
            if (UFb.find(i) == i) {
                idb[i] = pb;
                pb++;
            }
        }

        int p = Math.max(pa, pb);
        dega = new int[p];
        degb = new int[p];
        List<Integer> C = new ArrayList<>();
        List<Integer> D = new ArrayList<>();

        for (int i = 0; i < A.length; i++) {
            int u = ida[UFa.find(A[i])];
            int v = idb[UFb.find(B[i])];
            C.add(u);
            D.add(v);
            dega[u]++;
            degb[v]++;
        }

        int j = 0;

        for (int i = 0; i < p; i++) {
            while (dega[i] < K) {
                while (degb[j] == K) {
                    j++;
                }

                C.add(i);
                D.add(j);
                dega[i]++;
                degb[j]++;
            }
        }

        return new RegularGraph(K, p, C, D);
    }

    private static UnionFind contract(int[] deg, int k) {
        PriorityQueue<int[]> hq = new PriorityQueue<>((a, b) -> a[0] - b[0]);

        for (int i = 0; i < deg.length; i++) {
            hq.add(new int[]{deg[i], i});
        }

        UnionFind UF = new UnionFind(deg.length);

        while (hq.size() >= 2) {
            int[] p = hq.poll();
            int[] q = hq.poll();

            if (p[0] + q[0] > k) {
                continue;
            }

            p[0] += q[0];
            UF.union(p[1], q[1]);
            hq.add(p);
        }

        return UF;
    }

    private static List<Integer> eulerTrail(List<Integer> A, List<Integer> B, List<Integer> ord, int n) {
        int V = 2 * n;
        List<List<ImmutablePair<Integer, Integer>>> G = new ArrayList<>();
        for (int i = 0; i < V; i++) {
            G.add(new ArrayList<>());
        }

        int m = 0;
        for (int i : ord) {
            G.get(A.get(i)).add(new ImmutablePair<>(B.get(i) + n, m));
            G.get(B.get(i) + n).add(new ImmutablePair<>(A.get(i), m));
            m++;
        }

        boolean[] used_v = new boolean[V];
        boolean[] used_e = new boolean[m];
        List<Integer> ans = new ArrayList<>();

        for (int i = 0; i < V; i++) {
            if (used_v[i]) {
                continue;
            }

            Stack<ImmutablePair<Integer, Integer>> st = new Stack<>();
            List<Integer> ord2 = new ArrayList<>();
            st.push(new ImmutablePair<>(i, -1));

            while (!st.isEmpty()) {
                ImmutablePair<Integer, Integer> p = st.peek();
                int id_ = p.getKey();
                used_v[id_] = true;

                if (G.get(id_).isEmpty()) {
                    ord2.add(p.getValue());
                    st.pop();
                } else {
                    ImmutablePair<Integer, Integer> e = G.get(id_).get(G.get(id_).size() - 1);
                    G.get(id_).remove(G.get(id_).size() - 1);

                    if (used_e[e.getValue()]) {
                        continue;
                    }

                    used_e[e.getValue()] = true;
                    st.push(e);
                }
            }

            ord2.remove(ord2.size() - 1);
            Collections.reverse(ord2);
            ans.addAll(ord2);
        }

        for (int i = 0; i < ans.size(); i++) {
            ans.set(i, ord.get(ans.get(i)));
        }

        return ans;
    }

    private static void rec(List<Integer> A, List<Integer> B, List<Integer> ord, int K, List<List<Integer>> ans, int n) {
        if (K == 0) {
            return;
        } else if (K == 1) {
            ans.add(ord);
            return;
        } else if ((K & 1) == 1) {
            HopcroftKarp G = new HopcroftKarp(n, n);

            for (int i : ord) {
                G.addEdges(A.get(i), B.get(i));
            }

            G.maxMatching();
            List<Integer> lst = new ArrayList<>();
            ans.add(new ArrayList<>());

            for (int i : ord) {
                if (G.getMatchLeft()[A.get(i)] == B.get(i)) {
                    G.getMatchLeft()[A.get(i)] = -1;
                    ans.get(ans.size() - 1).add(i);
                } else {
                    lst.add(i);
                }
            }

            rec(A, B, lst, K - 1, ans, n);
        } else {
            List<Integer> path = eulerTrail(A, B, ord, n);
            List<Integer> L = new ArrayList<>();
            List<Integer> R = new ArrayList<>();

            for (int i = 0; i < path.size(); i++) {
                if ((i & 1) == 1) {
                    L.add(path.get(i));
                } else {
                    R.add(path.get(i));
                }
            }

            rec(A, B, L, K / 2, ans, n);
            rec(A, B, R, K / 2, ans, n);
        }
    }
}
