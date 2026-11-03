"""Cyclomatic complexity V(G) from code (counting convention stated) and from control-flow graphs."""
from __future__ import annotations

import re

from families._t07kit import q

TOPIC = "순환 복잡도"

SNIPPETS = {
    "grade": """int grade(int s, int a) {
    int r = 0;
    if (s >= 90) r = 4;
    else if (s >= 80) r = 3;
    else if (s >= 70) r = 2;
    else r = 1;
    if (a < 3 && r > 1) r++;
    return r;
}""",
    "count": """int count(int a[], int n) {
    int c = 0;
    for (int i = 0; i < n; i++) {
        if (a[i] < 0) continue;
        if (a[i] % 2 == 0 || a[i] > 100) c++;
    }
    while (c > 10) c -= 10;
    return c;
}""",
    "fee": """int fee(int t, int w) {
    int f;
    switch (t) {
        case 1: f = 10; break;
        case 2: f = 20; break;
        case 3: f = 30; break;
        default: f = 0;
    }
    if (w > 5) f += 5;
    return f;
}""",
    "pairs": """int pairs(int a[], int n, int k) {
    int c = 0;
    for (int i = 0; i < n; i++)
        for (int j = i + 1; j < n; j++)
            if (a[i] + a[j] == k) c++;
    return c;
}""",
    "collatz": """int steps(int x) {
    int s = 0;
    while (x != 1) {
        x = (x % 2 == 0) ? x / 2 : 3 * x + 1;
        s++;
        if (s > 1000) break;
    }
    return s;
}""",
    "valid": """int valid(int a, int b, int c) {
    if (a > 0 && b > 0 && c > 0) {
        if (a + b > c || b + c > a || a + c > b)
            return 1;
    }
    return 0;
}""",
    "classify": """int classify(int t, int h) {
    int r = 0;
    while (t > 0) {
        if (t > 30 && h > 70) r += 2;
        else if (t > 30 || h > 70) r += 1;
        t -= 10;
    }
    return r;
}""",
}


def counts(src):
    body = re.sub(r"\bdefault:", "", src)
    simple = (len(re.findall(r"\bif\b", body)) + len(re.findall(r"\bfor\b", body)) +
              len(re.findall(r"\bwhile\b", body)) + len(re.findall(r"\bcase\b", body)) +
              len(re.findall(r"\?", body)))
    ops = len(re.findall(r"&&|\|\|", body))
    return simple, ops


def code_q(n, key, convention, diff):
    src = SNIPPETS[key]
    simple, ops = counts(src)
    if convention == "A":
        right = simple + 1
        conv = ("판단점은 if(else if 포함), for, while, case, ?: 하나당 1개로 세고 default는 세지 않는다. "
                "&&, ||로 이어진 복합 조건도 하나의 판단점으로 본다.")
    else:
        right = simple + ops + 1
        conv = ("판단점은 if(else if 포함), for, while, case, ?: 하나당 1개로 세고 default는 세지 않는다. "
                "추가로 조건식 안의 &&, || 연산자마다 판단점 1개를 더 센다(조건 단위 계산).")
    wrong = [
        (str(simple if convention == "A" else simple + ops), "마지막에 더하는 1(시작 경로)을 빠뜨렸다. V(G)=판단점 수+1이다."),
        (str(simple + ops + 1 if convention == "A" else simple + 1), "다른 계산 규칙을 적용했다. 이 문제에서 명시한 복합 조건 처리 방식과 다르다."),
        (str(simple + ops + 2), "판단점에 1을 두 번 더했다. 종료 경로 하나와 시작 경로를 이중으로 센 오류다."),
        (str(simple + 2 if convention == "A" else simple + ops + 2), "else나 default를 판단점으로 한 번 더 세었다. else와 default는 분기를 만들지 않는다."),
        (str(len(re.findall(r"\bif\b", src)) + 1), "if만 판단점으로 세고 반복문·switch·삼항 연산자를 빼먹었다."),
        (str(len(src.splitlines())), "코드의 줄 수를 답했다. 순환 복잡도는 줄 수가 아니라 독립 경로 수다."),
        (str(simple + ops + 3), "판단점 수에 3을 더했다. 시작과 종료를 각각 경로로 센 값이다."),
        (str(max(simple - 1, 1)), "시작 경로를 더하지 않고 판단점에서 하나를 뺐다."),
        (str(simple + ops), "복합 조건을 모두 판단점으로 센 값에서 시작 경로 1을 더하지 않았다."),
    ]
    return q(f"t07-cyclo-{n:02d}", TOPIC,
             f"다음 C 함수에서 순환 복잡도(McCabe V(G))를 구하라. {conv}", (str(right), f"규칙대로 판단점을 세면 {right - 1}개이고, V(G)는 판단점 수 + 1 = {right}이다."),
             wrong, "코드에서 판단점을 세어 순환 복잡도를 계산한다. 복합 조건 처리 규칙이 핵심 조건이다.",
             [f"이 문제의 판단점 규칙: {conv}",
              f"코드에서 세면 단순 판단점(if·for·while·case·?:)은 {simple}개, &&·||는 {ops}개다. "
              + (f"복합 조건을 한 판단점으로 보므로 판단점 {simple}개." if convention == "A" else f"연산자까지 포함하면 판단점 {simple}+{ops}={simple + ops}개."),
              f"V(G) = 판단점 수 + 1 = {right}. 이 값은 기본 경로 테스트에서 필요한 독립 경로의 수이자, 모든 분기를 덮기 위한 시험 케이스 수의 상한 지표가 된다."],
             "먼저 문제가 정한 세기 규칙(복합 조건을 하나로 보는지)을 확인하고, 판단점을 모두 센 뒤 마지막에 +1을 한다.",
             diff, tags=["순환 복잡도", "McCabe"], code={"lang": "c", "text": src}, pad=right)


GRAPHS = [
    ("if-else 합류", [(1, 2), (2, 3), (2, 4), (3, 5), (4, 5), (5, 6)], 2),
    ("반복문과 if-else", [(1, 2), (2, 3), (3, 4), (4, 2), (2, 5), (5, 6), (5, 7), (6, 8), (7, 8)], 2),
    ("중첩 판단과 되돌아가기", [(1, 2), (2, 3), (2, 8), (3, 4), (3, 5), (4, 6), (5, 6), (6, 7), (7, 2), (7, 8)], 3),
    ("4방향 분기", [(1, 2), (2, 3), (2, 4), (2, 5), (2, 6), (3, 7), (4, 7), (5, 7), (6, 7), (7, 8)], 2),
    ("복합 제어 흐름", [(1, 2), (2, 3), (2, 4), (3, 5), (4, 5), (5, 6), (6, 7), (6, 8), (7, 9), (8, 9), (9, 5), (9, 10)], 3),
]


def graph_q(n, idx, ask_kind):
    name, edges, diff = GRAPHS[idx]
    nodes = sorted({x for e in edges for x in e})
    N, E = len(nodes), len(edges)
    v = E - N + 2
    outdeg = {x: sum(1 for a, _ in edges if a == x) for x in nodes}
    pred = sum(1 for x in nodes if outdeg[x] >= 2)
    text = "\n".join(f"{a} -> {b}" for a, b in edges)
    wrong = [
        (str(E - N), "공식 E-N+2에서 +2를 빠뜨렸다. 연결 요소가 1개인 단일 흐름 그래프이므로 +2를 더한다."),
        (str(E - N + 1), "E-N+1은 연결 요소를 다르게 적용한 값이다. 그래프를 닫지 않은 흐름 그래프는 E-N+2다."),
        (str(E - N + 3), "연결 요소를 2개로 보고 +3을 적용했다."),
        (str(N - E + 2), "E와 N의 순서를 바꿔 계산했다."),
        (str(E), "간선의 수를 답했다."),
        (str(N), "노드의 수를 답했다."),
        (str(pred), "분기(출력 간선 2개 이상) 노드 수를 답했다. V(G)는 이 값에 1을 더해야 한다." if pred + 1 == v else "분기(출력 간선 2개 이상) 노드 수를 답했다. 합류와 되돌아가기 간선이 늘리는 독립 경로를 놓친다."),
        (str(E + N - 2), "N-E 대신 합을 이용했다."),
        (str(E - N - 1), "부호를 바꿔 계산했다."),
    ]
    asks = {
        "v": "다음 제어 흐름 그래프의 순환 복잡도 V(G)는? (노드 N, 간선 E, 연결 요소 1개)",
        "paths": "다음 제어 흐름 그래프에서 기본 경로 테스트(basis path testing)로 찾아야 하는 선형 독립 경로의 수는?",
    }
    return q(f"t07-cyclo-{n:02d}", TOPIC, asks[ask_kind] + f"\n{name}를 나타낸 그래프이며 1이 시작, {nodes[-1]}이 종료 노드다.",
             (str(v), f"N={N}, E={E}에서 V(G)=E-N+2={v}이다."), wrong,
             "제어 흐름 그래프의 노드와 간선을 세어 순환 복잡도(선형 독립 경로 수)를 구한다.",
             [f"그래프의 노드는 {N}개, 간선은 {E}개이고 연결 요소는 하나다.",
              f"V(G) = E - N + 2 = {E} - {N} + 2 = {v}. 출력 간선이 둘 이상인 분기 노드가 {pred}개 있는 점은 판단점+1 공식과도 연결된다.",
              "기본 경로 테스트는 이 V(G)개의 선형 독립 경로를 각각 실행하는 시험이다. 경로 수가 곧 필요한 최소 시험 케이스 수의 기준이 된다."],
             "공식은 E−N+2. 판단점이 분명한 구조라면 '분기 노드 수 + 1'로 교차 확인한다(단, 한 노드의 출력이 3개 이상이면 출력 수−1씩 더한다).",
             diff, tags=["순환 복잡도", "제어 흐름 그래프"], code={"lang": "text", "text": text}, pad=v)


def generate():
    out = [
        code_q(1, "grade", "A", 1), code_q(2, "count", "B", 2), code_q(3, "fee", "A", 2),
        code_q(4, "pairs", "A", 1), code_q(5, "collatz", "B", 3), code_q(6, "valid", "B", 3),
        code_q(7, "classify", "A", 2),
        graph_q(8, 0, "v"), graph_q(9, 1, "v"), graph_q(10, 2, "paths"), graph_q(11, 3, "v"),
        graph_q(12, 4, "paths"),
    ]
    return out
