package ch.ethz.systems.floodns.ext.utils;

import java.util.*;


public class UnionFind {
    private final int n;
    private final int[] parents;
    private int group;

    public UnionFind(int n) {
        this.n = n;
        parents = new int[n];
        group = n;

        Arrays.fill(parents, -1);
    }

    public int find(int x) {
        if (parents[x] < 0) {
            return x;
        } else {
            parents[x] = find(parents[x]);
            return parents[x];
        }
    }

    public void union(int x, int y) {
        x = find(x);
        y = find(y);

        if (x == y) {
            return;
        }

        group--;

        if (parents[x] > parents[y]) {
            int temp = x;
            x = y;
            y = temp;
        }

        parents[x] += parents[y];
        parents[y] = x;
    }

    public int size(int x) {
        return -parents[find(x)];
    }

    public boolean same(int x, int y) {
        return find(x) == find(y);
    }

    public List<Integer> members(int x) {
        int root = find(x);
        List<Integer> members = new ArrayList<>();

        for (int i = 0; i < n; i++) {
            if (find(i) == root) {
                members.add(i);
            }
        }

        return members;
    }

    public List<Integer> roots() {
        List<Integer> roots = new ArrayList<>();

        for (int i = 0; i < n; i++) {
            if (parents[i] < 0) {
                roots.add(i);
            }
        }

        return roots;
    }

    public int group_count() {
        return group;
    }

    public Map<Integer, List<Integer>> all_group_members() {
        Map<Integer, List<Integer>> dic = new HashMap<>();

        for (int r : roots()) {
            dic.put(r, new ArrayList<>());
        }

        for (int i = 0; i < n; i++) {
            dic.get(find(i)).add(i);
        }

        return dic;
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();

        for (int r : roots()) {
            sb.append(r).append(": ").append(members(r)).append("\n");
        }

        return sb.toString();
    }

}