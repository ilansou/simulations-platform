package ch.ethz.systems.floodns.ext.utils;

import java.util.List;

public class RegularGraph {

    private int K;  // Regularity
    private int p;
    private List<Integer> C;
    private List<Integer> D;

    public RegularGraph(int k, int p, List<Integer> c, List<Integer> d) {
        K = k;
        this.p = p;
        C = c;
        D = d;
    }

    public int getK() {
        return K;
    }

    public int getP() {
        return p;
    }

    public List<Integer> getC() {
        return C;
    }

    public List<Integer> getD() {
        return D;
    }
}
