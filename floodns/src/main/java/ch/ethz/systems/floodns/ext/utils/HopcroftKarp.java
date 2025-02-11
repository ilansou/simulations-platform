package ch.ethz.systems.floodns.ext.utils;

import org.apache.commons.lang3.tuple.ImmutablePair;

import java.util.*;

public class HopcroftKarp {
    private int n;
    private int m;
    private List<List<Integer>> G;
    private List<List<Integer>> RG;
    private int[] matchLeft;
    private int[] matchRight;
    private int[] used;
    private int time_stamp;
    private int[] dist;

    public HopcroftKarp(int n, int m) {
        this.n = n;
        this.m = m;
        G = new ArrayList<>();
        RG = new ArrayList<>();
        matchLeft = new int[n];
        matchRight = new int[m];
        used = new int[n];
        dist = new int[n];
        time_stamp = 0;

        Arrays.fill(matchLeft, -1);
        Arrays.fill(matchRight, -1);
        Arrays.fill(used, 0);
        Arrays.fill(dist, -1);


        for (int i = 0; i < n; i++) {
            G.add(new ArrayList<>());
        }

        for (int i = 0; i < m; i++) {
            RG.add(new ArrayList<>());
        }
    }

    public void addEdges(int u, int v) {
        G.get(u).add(v);
    }

    private void buildArgumentPath() {
        Queue<Integer> queue = new LinkedList<>();
        int[] dist = new int[n];
        Arrays.fill(dist, -1);

        for (int i = 0; i < n; i++) {
            if (matchLeft[i] == -1) {
                queue.add(i);
                dist[i] = 0;
            }
        }

        while (!queue.isEmpty()) {
            int a = queue.poll();

            for (int b : G.get(a)) {
                int c = matchRight[b];

                if (c >= 0 && dist[c] == -1) {
                    dist[c] = dist[a] + 1;
                    queue.add(c);
                }
            }
        }
    }

    private boolean findMinDistArgumentPath(int a) {
        used[a] = time_stamp;

        for (int b : G.get(a)) {
            int c = matchRight[b];

            if (c < 0 || (used[c] != time_stamp && dist[c] == dist[a] + 1 && findMinDistArgumentPath(c))) {
                matchRight[b] = a;
                matchLeft[a] = b;
                return true;
            }
        }

        return false;
    }

    public List<ImmutablePair<Integer, Integer>> maxMatching() {
        while (true) {
            buildArgumentPath();
            time_stamp++;
            int flow = 0;

            for (int i = 0; i < n; i++) {
                if (matchLeft[i] == -1) {
                    flow += findMinDistArgumentPath(i) ? 1 : 0;
                }
            }

            if (flow == 0) {
                break;
            }
        }

        List<ImmutablePair<Integer, Integer>> ret = new ArrayList<>();

        for (int i = 0; i < n; i++) {
            if (matchLeft[i] >= 0) {
                ret.add(ImmutablePair.of(i, matchLeft[i]));
            }
        }

        return ret;
    }

    public int getN() {
        return n;
    }

    public int getM() {
        return m;
    }

    public List<List<Integer>> getG() {
        return G;
    }

    public List<List<Integer>> getRG() {
        return RG;
    }

    public int[] getMatchLeft() {
        return matchLeft;
    }

    public int[] getMatchRight() {
        return matchRight;
    }

    public int[] getUsed() {
        return used;
    }

    public int getTime_stamp() {
        return time_stamp;
    }
}