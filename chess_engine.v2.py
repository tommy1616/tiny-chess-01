# tiny-chess-01 engine: alpha-beta with quiescence, MVV-LVA, killers.
# One file, Python 3.13 standard library, fixed node budget per move.
import os, sys, json, urllib.request

E = os.environ.get("MAKEFUN_ENV_URL") or sys.exit(1)
C = "abcdefgh"
W = [0, 100, 320, 330, 500, 900, 0]
SQ = [i for i in range(128) if not i & 0x88]
PC = {}
for _i, _c in enumerate("PNBRQK"):
    PC[_c] = _i + 1
    PC[_c.lower()] = -_i - 1
DIR = {2: (33, 31, 18, 14, -33, -31, -18, -14),
       3: (17, 15, -17, -15),
       4: (16, 1, -16, -1),
       5: (17, 15, -17, -15, 16, 1, -16, -1),
       6: (17, 15, -17, -15, 16, 1, -16, -1)}
# piece-square tables, written rank 8 first, white's side of the board
PAWN = [
    0, 0, 0, 0, 0, 0, 0, 0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5, 5, 10, 25, 25, 10, 5, 5,
    0, 0, 0, 20, 20, 0, 0, 0,
    5, -5, -10, 0, 0, -10, -5, 5,
    5, 10, 10, -20, -20, 10, 10, 5,
    0, 0, 0, 0, 0, 0, 0, 0]
KNIGHT = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20, 0, 0, 0, 0, -20, -40,
    -30, 0, 10, 15, 15, 10, 0, -30,
    -30, 5, 15, 20, 20, 15, 5, -30,
    -30, 0, 15, 20, 20, 15, 0, -30,
    -30, 5, 10, 15, 15, 10, 5, -30,
    -40, -20, 0, 5, 5, 0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50]
BISHOP = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 0, 5, 10, 10, 5, 0, -10,
    -10, 5, 5, 10, 10, 5, 5, -10,
    -10, 0, 10, 10, 10, 10, 0, -10,
    -10, 10, 10, 10, 10, 10, 10, -10,
    -10, 5, 0, 0, 0, 0, 5, -10,
    -20, -10, -10, -10, -10, -10, -10, -20]
ROOK = [
    0, 0, 0, 0, 0, 0, 0, 0,
    5, 10, 10, 10, 10, 10, 10, 5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    0, 0, 0, 5, 5, 0, 0, 0]
QUEEN = [
    -20, -10, -10, -5, -5, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 0, 5, 5, 5, 5, 0, -10,
    -5, 0, 5, 5, 5, 5, 0, -5,
    0, 0, 5, 5, 5, 5, 0, -5,
    -10, 5, 5, 5, 5, 5, 0, -10,
    -10, 0, 5, 0, 0, 0, 0, -10,
    -20, -10, -10, -5, -5, -10, -10, -20]
KMG = [
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
    20, 20, 0, 0, 0, 0, 20, 20,
    20, 30, 10, 0, 0, 10, 30, 20]
KEG = [
    -50, -40, -30, -20, -20, -30, -40, -50,
    -30, -20, -10, 0, 0, -10, -20, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -30, 0, 0, 0, 0, -30, -30,
    -50, -30, -30, -30, -30, -30, -30, -50]


def _tbl(a):
    w = [0] * 128
    b = [0] * 128
    for i in SQ:
        r = i >> 4
        f = i & 7
        w[i] = a[(7 - r) * 8 + f]
        b[i] = a[r * 8 + f]
    return w, b


PT = {1: _tbl(PAWN), 2: _tbl(KNIGHT), 3: _tbl(BISHOP), 4: _tbl(ROOK), 5: _tbl(QUEEN)}
KMW, KMB = _tbl(KMG)
KEW, KEB = _tbl(KEG)
INF = 10 ** 6
LIM = 0
NODES = 0
EP = -1
CR = ""
KG = [0, 0]
K1 = [0] * 64
K2 = [0] * 64


class X(Exception):
    pass


def post(p, b):
    r = urllib.request.Request(E + p, data=json.dumps(b).encode(),
                               headers={"content-type": "application/json"})
    with urllib.request.urlopen(r, timeout=8) as f:
        return json.load(f)


def load(fen):
    b = [0] * 128
    p = fen.split()
    r = 7
    f = 0
    for c in p[0]:
        if c == "/":
            r -= 1
            f = 0
        elif c.isdigit():
            f += int(c)
        else:
            b[r * 16 + f] = PC[c]
            f += 1
    ep = -1
    if len(p) > 3 and p[3] != "-":
        ep = (int(p[3][1]) - 1) * 16 + C.index(p[3][0])
    return b, 1 if p[1] == "w" else -1, ep, (p[2] if len(p) > 2 else "-")


def atk(b, s, st):
    d = 16 * st
    for c in (d - 1, d + 1):
        j = s - c
        if not j & 0x88 and b[j] == st:
            return 1
    for o in DIR[2]:
        j = s + o
        if not j & 0x88 and b[j] == 2 * st:
            return 1
    for o in DIR[6]:
        j = s + o
        if not j & 0x88 and b[j] == 6 * st:
            return 1
    for o in DIR[3]:
        j = s + o
        while not j & 0x88:
            q = b[j]
            if q:
                if q * st > 0 and abs(q) in (3, 5):
                    return 1
                break
            j += o
    for o in DIR[4]:
        j = s + o
        while not j & 0x88:
            q = b[j]
            if q:
                if q * st > 0 and abs(q) in (4, 5):
                    return 1
                break
            j += o
    return 0


def ap(b, m, st):
    global EP, CR
    f = (m >> 7 & 127)
    t = m & 127
    pc = b[f]
    cap = b[t]
    oe = EP
    oc = CR
    b[t] = pc
    b[f] = 0
    if abs(pc) == 1:
        if not cap and t == oe and (t & 7) != (f & 7):
            j = t - 16 * st
            cap = b[j]
            b[j] = 0
        elif t >> 4 in (0, 7):
            b[t] = (m >> 14 & 7) * (1 if pc > 0 else -1)
        EP = f + 16 * st if t - f == 32 * st else -1
    else:
        EP = -1
        if abs(pc) == 6:
            KG[0 if pc > 0 else 1] = t
            if abs(t - f) == 2:
                rf, rt = (f + 3, f + 1) if t > f else (f - 4, f - 1)
                b[rt] = b[rf]
                b[rf] = 0
    if CR:
        if f in (4, 7) or t in (4, 7):
            CR = CR.replace("K", "")
        if f in (0, 4) or t in (0, 4):
            CR = CR.replace("Q", "")
        if f in (116, 119) or t in (116, 119):
            CR = CR.replace("k", "")
        if f in (112, 116) or t in (112, 116):
            CR = CR.replace("q", "")
    return cap, oe, oc


def un(b, m, u):
    global EP, CR
    f = (m >> 7 & 127)
    t = m & 127
    p = m >> 14 & 7
    pc = (1 if b[t] > 0 else -1) if p else b[t]
    b[f] = pc
    b[t] = u[0] if u[0] else 0
    if abs(pc) == 1 and not u[0] and t == EP and (t & 7) != (f & 7):
        b[t - 16 * (1 if pc > 0 else -1)] = -pc
        b[t] = 0
    if abs(pc) == 6:
        KG[0 if pc > 0 else 1] = f
    EP = u[1]
    CR = u[2]


def gen(b, st, caps=0):
    ms = []
    for i in SQ:
        v = b[i]
        if v * st <= 0:
            continue
        t = abs(v)
        if t == 1:
            d = 16 * st
            j = i + d
            if not j & 0x88 and not b[j]:
                if not caps:
                    if j >> 4 in (0, 7):
                        for p in (5, 4, 3, 2):
                            ms.append(i * 128 + j | p << 14)
                    else:
                        ms.append(i * 128 + j)
                        k = i + 2 * d
                        if i >> 4 in (1, 6) and not b[k]:
                            ms.append(i * 128 + k)
            for c in (d - 1, d + 1):
                j = i + c
                if j & 0x88:
                    continue
                q = b[j]
                if q * st < 0:
                    if j >> 4 in (0, 7):
                        for p in (5, 4, 3, 2):
                            ms.append(i * 128 + j | p << 14)
                    else:
                        ms.append(i * 128 + j)
                elif j == EP:
                    ms.append(i * 128 + j)
        else:
            for o in DIR[t]:
                j = i + o
                while not j & 0x88:
                    q = b[j]
                    if not q:
                        if not caps:
                            ms.append(i * 128 + j)
                        if t < 3 or t > 5:
                            break
                    else:
                        if q * st < 0:
                            ms.append(i * 128 + j)
                        break
                    j += o
    if not caps:
        if st > 0:
            if "K" in CR and not b[5] and not b[6] and b[7] == 4 and not atk(b, 4, -1) and not atk(b, 5, -1) and not atk(b, 6, -1):
                ms.append(4 * 128 + 6)
            if "Q" in CR and not b[1] and not b[2] and not b[3] and b[0] == 4 and not atk(b, 4, -1) and not atk(b, 2, -1) and not atk(b, 3, -1):
                ms.append(4 * 128 + 2)
        else:
            if "k" in CR and not b[117] and not b[118] and b[119] == -4 and not atk(b, 116, 1) and not atk(b, 117, 1) and not atk(b, 118, 1):
                ms.append(116 * 128 + 118)
            if "q" in CR and not b[113] and not b[114] and not b[115] and b[112] == -4 and not atk(b, 116, 1) and not atk(b, 114, 1) and not atk(b, 115, 1):
                ms.append(116 * 128 + 114)
    return ms


def ev(b):
    s = 0
    ph = 0
    kw = 0
    kb = 0
    for i in SQ:
        v = b[i]
        if not v:
            continue
        t = abs(v)
        if t == 6:
            if v > 0:
                kw = i
            else:
                kb = i
            continue
        if t > 1:
            ph += W[t]
        if v > 0:
            s += W[t] + PT[t][0][i]
        else:
            s -= W[t] + PT[t][1][i]
    if ph > 2000:
        s += KMW[kw] - KMW[kb]
    else:
        s += KEW[kw] - KEW[kb]
    return s


def qs(b, st, a, bt):
    global NODES
    NODES += 1
    if NODES > LIM:
        raise X
    s = ev(b) * st
    if s >= bt:
        return s
    if s > a:
        a = s
    ms = gen(b, st, 1)
    ms.sort(key=lambda m: -(W[abs(b[m & 127]) or 0] * 8 - W[abs(b[(m >> 7 & 127)])]))
    for m in ms:
        u = ap(b, m, st)
        if atk(b, KG[0 if st > 0 else 1], -st):
            un(b, m, u)
            continue
        v = -qs(b, -st, -bt, -a)
        un(b, m, u)
        if v > a:
            a = v
            if a >= bt:
                break
    return a


def ab(b, st, d, a, bt, ply):
    global NODES
    if d <= 0:
        return qs(b, st, a, bt)
    NODES += 1
    if NODES > LIM:
        raise X
    ms = gen(b, st)
    k = K1[ply]
    sc = []
    for m in ms:
        t = m & 127
        v = b[t]
        if v:
            sc.append((-(1000 + W[abs(v)] * 8 - W[abs(b[(m >> 7 & 127)])]), m))
        else:
            sc.append((-900 if m == k else 0, m))
    sc.sort()
    best = -INF
    any = 0
    for _, m in sc:
        u = ap(b, m, st)
        if atk(b, KG[0 if st > 0 else 1], -st):
            un(b, m, u)
            continue
        any = 1
        v = -ab(b, -st, d - 1, -bt, -a, ply + 1)
        un(b, m, u)
        if v > best:
            best = v
        if v > a:
            a = v
            if a >= bt:
                if not b[m & 127] and m != k:
                    K2[ply] = k
                    K1[ply] = m
                break
    if not any:
        return -INF + ply if atk(b, KG[0 if st > 0 else 1], -st) else 0
    return a


def uci(m):
    f = (m >> 7 & 127)
    t = m & 127
    s = C[f & 7] + str((f >> 4) + 1) + C[t & 7] + str((t >> 4) + 1)
    p = m >> 14 & 7
    return s + "pnbrq"[p - 1] if p else s


def pick(fen, legal):
    global LIM, NODES, EP, CR, KG
    b, st, ep, cr = load(fen)
    EP = ep
    CR = cr
    KG = [0, 0]
    for i in SQ:
        if b[i] == 6:
            KG[0] = i
        elif b[i] == -6:
            KG[1] = i
    mv = []
    for x in legal:
        m = (C.index(x[0]) + 16 * (int(x[1]) - 1)) * 128 + C.index(x[2]) + 16 * (int(x[3]) - 1)
        if len(x) > 4:
            m |= (1 + "pnbrq".index(x[4])) << 14
        mv.append(m)
    LIM = int(os.environ.get("ENGINE_NODES") or 90000)
    bestm = mv[0]
    for d in range(1, 9):
        NODES = 0
        try:
            a = -INF
            cur = None
            for m in mv:
                u = ap(b, m, st)
                v = -ab(b, -st, d - 1, -INF, -a, 1)
                un(b, m, u)
                if v > a:
                    a = v
                    cur = m
            if cur is not None:
                bestm = cur
                mv.remove(cur)
                mv.insert(0, cur)
        except X:
            break
    return uci(bestm)


while True:
    g = post("/game", {})
    if g["status"] == "done":
        break
    while g["status"] == "your_move":
        g = post("/move", {"game": g["game"], "move": pick(g["fen"], g["legal_moves"])})
    print("game %s: %s" % (g["game"], g["outcome"]), file=sys.stderr)
