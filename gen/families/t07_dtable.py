"""Decision table testing: rule counts, rules per action, collapsed-table completeness and overlap."""
from __future__ import annotations

from itertools import product

from families._t07kit import q

TOPIC = "결정 테이블 테스트"


def full_count(n, conds, shape, why, diff):
    total = 1
    for c in shape:
        total *= c
    rows = [[c, "참/거짓" if k == 2 else f"{k}가지 값"] for c, k in zip(conds, shape)]
    wrong = [
        (str(sum(shape)), "조건별 값의 수를 더했다. 규칙은 각 조건 값의 모든 조합이므로 곱이다."),
        (str(2 ** len(shape)), "모든 조건이 참/거짓 두 값뿐이라고 가정했다. 값이 3가지인 조건은 3배로 센다."),
        (str(total // 2), "불가능한 조합이 있다고 가정해 절반으로 줄였다. 명세에 제약이 없으면 완전 결정 테이블은 모든 조합을 가진다."),
        (str(total * 2), "결과(액션)별로 규칙을 두 배로 세었다. 규칙 수는 조건 조합 수와 같다."),
        (str(len(shape) * max(shape)), "조건 수와 최대 값의 수를 곱했다. 조건 값의 조합이 아니라 단순 곱이다."),
        (str(total - 1), "모든 조건이 기본값인 조합 하나를 뺐다. 기본값 조합도 하나의 규칙이다."),
        (str(total + len(shape)), "조건마다 '해당 없음' 항목을 하나씩 더 둔 값이다. 해당 없음은 축약된 규칙에서만 쓴다."),
        (str(max(shape) ** len(shape)), "모든 조건이 가장 큰 값의 수를 가진다고 가정했다."),
    ]
    return q(f"t07-dtable-{n:02d}", TOPIC,
             f"{why}에서 다음 표의 조건들을 결정 테이블의 조건부에 모두 쓰고 빠짐없는 완전 결정 테이블을 만들려 한다. 조건 사이에 서로 불가능한 조합은 없다고 할 때 규칙(열)의 수는?",
             (str(total), f"각 조건의 값 수를 곱한 {' × '.join(map(str, shape))} = {total}개다."),
             wrong, "조건 값의 모든 조합이 만드는 완전 결정 테이블의 규칙 수를 센다.",
             [f"결정 테이블의 한 규칙은 모든 조건에 값을 하나씩 지정한 조합이다. 조건이 {len(shape)}개이고 값의 수가 {list(shape)}이므로 서로 곱한다.",
              f"{' × '.join(map(str, shape))} = {total}. 이 {total}개가 테스트 설계 때 빠뜨리면 안 되는 모든 조합이다.",
              "참/거짓만 있는 조건은 2배, 값이 3가지인 조건은 3배로 곱해진다. 조건을 하나 늘릴 때마다 규칙 수는 지수적으로 증가한다."],
             "완전 결정 테이블의 규칙 수는 각 조건의 값 수를 모두 곱한 값이다. 불가능한 조합은 명세로 확인 후 제거한다.",
             diff, tables=[{"caption": "조건과 값", "columns": ["조건", "값"], "rows": rows}], pad=total)


def action_count(n, text, names, f, mistakes, diff):
    k = len(names)
    combos = list(product([True, False], repeat=k))
    right = sum(1 for c in combos if f(*c))
    wrong = []
    for desc, g, why in mistakes:
        wrong.append((str(sum(1 for c in combos if g(*c))), why))
    wrong += [
        (str(2 ** k - right), "액션이 실행되지 않는 조합 수를 센 값이다. 질문은 실행되는 조합이다."),
        (str(2 ** k), "모든 조합 수를 답했다."),
        (str(2 ** (k - 1)), "조건이 반반이라고 가정한 값이다. 실제 논리식으로 직접 세어야 한다."),
        (str(right + 1), "논리식을 평가하다 한 조합을 더 참으로 센 계산 실수다."),
        (str(max(right - 1, 0)), "논리식을 평가하다 한 조합을 빠뜨린 계산 실수다."),
    ]
    rows = []
    for c in combos:
        rows.append(["".join("Y" if x else "N" for x in c) and " ".join("Y" if x else "N" for x in c), "실행" if f(*c) else "-"])
    return q(f"t07-dtable-{n:02d}", TOPIC, text,
             (str(right), f"{2 ** k}개 조합을 모두 대입해 논리식이 참인 조합이 {right}개임을 확인했다."),
             wrong, "논리식으로 정의된 액션이 실행되는 규칙(조건 조합)의 수를 센다.",
             [f"조건은 {', '.join(names)}으로 {k}개이므로 완전 결정 테이블의 규칙은 2^{k} = {2 ** k}개다.",
              "실행되는 입력 조합은 " + ", ".join("(" + ", ".join(f"{name}={'참' if value else '거짓'}" for name, value in zip(names, c)) + ")" for c in combos if f(*c)) + "이다. 각 조합을 독립적으로 한 번씩 세고, 한 규칙 안의 조건 개수와 규칙 수를 혼동하지 않는다.",
              {"table": {"caption": "규칙별 액션 실행 여부(" + " ".join(names) + ")", "columns": ["조건 값", "액션"], "rows": rows}},
              f"표에서 '실행'이 표시된 규칙이 {right}개다. 괄호와 and/or 우선순위를 먼저 확정한 뒤 대입해야 한다."],
             "and/or가 섞인 논리식은 괄호를 먼저 확정하고 모든 조합을 표로 평가한다. 평가 순서를 바꾸면 개수가 달라진다.",
             diff, pad=right)


def collapsed(n, kind, conds, rules, diff):
    k = len(conds)
    allc = list(product("YN", repeat=k))

    def match(rule, c):
        return all(r == "-" or r == x for r, x in zip(rule, c))

    cover = {c: [i for i, r in enumerate(rules) if match(r[0], c)] for c in allc}
    uncovered = sum(1 for c in allc if not cover[c])
    overlap = sum(1 for c in allc if len(cover[c]) > 1)
    expand = sum(2 ** r[0].count("-") for r in rules)
    rows = [[f"R{i + 1}"] + list(r[0]) + [r[1]] for i, r in enumerate(rules)]
    cols = ["규칙"] + conds + ["액션"]
    base = f"다음 표는 조건 {k}개({', '.join(conds)})에 대한 축약 결정 테이블이다. '-'는 해당 조건의 값과 무관함(Y·N 모두 해당)을 뜻한다."
    if kind == "uncovered":
        right = uncovered
        stem = base + " 이 표가 어떤 규칙에도 해당하지 않는 조건 조합, 즉 명세에서 누락된 조합은 몇 개인가?"
        ask = "축약 규칙이 덮지 못하는 조건 조합 수를 센다."
        wrong = [(str(expand), "각 규칙이 펼쳐지는 조합을 단순히 합했다. 겹치는 조합이 있으면 합은 실제 서로 다른 조합 수보다 크다."),
                 (str(2 ** k - expand if expand <= 2 ** k else 0), "규칙 확장 합계를 전체에서 뺐다. 중복 확장을 고려하지 않으면 누락 수가 어긋난다."),
                 (str(overlap), "둘 이상의 규칙에 해당하는 중복 조합 수를 센 값이다."),
                 (str(2 ** k), "전체 조합 수를 답했다."),
                 (str(len(rules)), "규칙의 개수를 답했다."),
                 (str(uncovered + 1), "한 조합을 더 누락으로 센 계산 실수다."),
                 (str(max(uncovered - 1, 0)), "한 조합을 덮이는 것으로 잘못 판단한 계산 실수다.")]
        sol = f"각 규칙의 '-'는 해당 칸을 Y/N 둘 다로 펼친다. 2^{k}={2 ** k}개 조합을 모두 규칙과 대조하면 어느 규칙에도 해당하지 않는 조합이 {uncovered}개 남는다."
    elif kind == "overlap":
        right = overlap
        stem = base + " 둘 이상의 규칙에 동시에 해당하는(모호한) 조건 조합은 몇 개인가?"
        ask = "규칙 사이에서 겹치는 조건 조합 수를 센다."
        wrong = [(str(expand - len({c for c in allc if cover[c]})), "중복 확장 횟수를 합한 값이다. 겹치는 조합 수가 아니라 초과 확장 횟수를 센 것으로 3개 이상 겹칠 때 다르다."),
                 (str(uncovered), "어떤 규칙에도 해당하지 않는 조합 수를 센 값이다."),
                 (str(expand), "규칙을 펼친 조합 수의 합이다. 겹침과 누락을 구분하지 않았다."),
                 (str(2 ** k), "전체 조합 수를 답했다."),
                 (str(len(rules)), "규칙의 개수를 답했다."),
                 (str(overlap + 1), "한 조합을 더 겹치는 것으로 센 계산 실수다."),
                 (str(overlap + 2), "겹치는 조합을 두 개 더 센 계산 실수다."),
                 (str(max(overlap - 1, 0)), "한 조합의 겹침을 놓친 계산 실수다.")]
        sol = f"2^{k}={2 ** k}개 조합 각각이 몇 개의 규칙과 맞는지 센다. 맞는 규칙이 2개 이상인 조합이 {overlap}개이며, 이 조합에서 액션이 서로 다르면 명세 모순이다."
    else:
        right = expand
        stem = base + " 모든 규칙의 '-'를 Y와 N으로 펼쳤을 때 만들어지는 조건 조합의 총수(겹침 포함, 규칙별 합계)는?"
        ask = "축약 규칙을 완전 규칙으로 펼쳤을 때의 합계를 구한다."
        wrong = [(str(len(rules)), "규칙 열의 개수를 답했다. '-' 하나는 두 규칙으로 펼쳐진다."),
                 (str(2 ** k), "완전 결정 테이블의 이론적 규칙 수를 답했다. 이 표의 규칙들이 펼쳐진 합계와는 다를 수 있다."),
                 (str(sum(r[0].count('-') for r in rules)), "'-' 개수의 합을 답했다. 각 '-'는 2배씩 곱해진다."),
                 (str(sum(2 * r[0].count('-') for r in rules)), "'-' 개수에 2를 곱해 더했다. 두 값으로 분기하므로 2^(-의 수)다."),
                 (str(expand + len(rules)), "펼친 규칙에 원래 규칙 수를 한 번 더 더했다."),
                 (str(max(expand - 1, 1)), "하나를 빠뜨린 계산 실수다."),
                 (str(expand + 1), "하나를 더한 계산 실수다."),
                 (str(sum(r[0].count('-') + 1 for r in rules)), "규칙마다 '-' 수 + 1로 센 값이다. 지수가 아닌 선형으로 계산했다.")]
        sol = "'-' 하나는 Y·N 두 규칙으로 펼쳐지고, '-'가 m개인 규칙은 2^m개의 완전 규칙이 된다. 규칙별 값을 모두 더한다: " + " + ".join(str(2 ** r[0].count("-")) for r in rules) + f" = {expand}."
    return q(f"t07-dtable-{n:02d}", TOPIC, stem,
             (str(right), sol.split(".")[0] + "."),
             wrong, ask,
             [sol, "표에서 '-'가 있는 규칙은 여러 조합을 한 열에 합친 것이다. 결정 테이블의 완전성(빠진 조합 없음)과 일관성(겹쳐도 같은 액션)은 이렇게 펼쳐서 확인한다."],
             "축약 규칙은 '-'를 Y·N으로 펼쳐 전체 2^n 조합과 대조한다. 누락은 어떤 규칙에도 없는 조합, 모호함은 둘 이상 규칙에 걸리는 조합이다.",
             diff, tables=[{"caption": "축약 결정 테이블", "columns": cols, "rows": rows}], pad=right)


def generate():
    out = []
    out.append(full_count(1, ["회원 여부", "쿠폰 보유", "주문 금액 10만원 이상"], (2, 2, 2), "쇼핑몰 할인 정책", 1))
    out.append(full_count(2, ["회원 등급(일반·우수·VIP)", "결제 수단(카드·계좌·포인트)", "배송 방식(일반·빠른)"], (3, 3, 2), "주문 결제 정책", 2))
    out.append(full_count(3, ["로그인 여부", "권한(읽기·쓰기·관리)", "승인 상태(대기·승인·반려)", "업무 시간 여부"], (2, 3, 3, 2), "문서 수정 권한 정책", 2))
    out.append(action_count(4, "배송비 면제 정책을 `회원이다 그리고 (쿠폰이 있거나 주문 금액이 10만원 이상이다)`로 정의했다. 조건은 회원 여부(A), 쿠폰 보유(B), 금액 10만원 이상(C) 세 가지이며 참/거짓만 있다. 완전 결정 테이블의 규칙 중 배송비가 면제되는 규칙은 몇 개인가?",
                            ["A", "B", "C"], lambda a, b, c: a and (b or c),
                            [("(A and B) or C", lambda a, b, c: (a and b) or c, "우선순위를 `(회원 그리고 쿠폰) 또는 금액`으로 잘못 묶었다. 비회원도 큰 금액이면 면제되어 개수가 달라진다."),
                             ("A or B or C", lambda a, b, c: a or b or c, "그리고를 또는으로 바꿨다. 비회원도 쿠폰만 있으면 면제되는 것으로 센 값이다.")], 1))
    out.append(action_count(5, "대출 심사 정책: 소득 증빙이 있고(A) 연체 이력이 없으며(B) 담보가 있거나(C) 보증인이 있으면(D) 승인한다. 즉 `A and B and (C or D)`이다. 4개 조건이 모두 참/거짓일 때 완전 결정 테이블에서 승인 규칙은 몇 개인가?",
                            ["A", "B", "C", "D"], lambda a, b, c, d: a and b and (c or d),
                            [("A and B and C and D", lambda a, b, c, d: a and b and c and d, "담보와 보증인을 모두 요구한다고 읽었다. 둘 중 하나면 충분하다."),
                             ("(A and B and C) or D", lambda a, b, c, d: (a and b and c) or d, "괄호 없이 읽어 보증인만 있으면 승인되는 것으로 센 값이다."),
                             ("(A and B) or (C and D)", lambda a, b, c, d: (a and b) or (c and d), "묶음을 잘못 나눴다. 소득·연체 조건은 담보/보증인 조건과 함께 만족해야 한다.")], 2))
    out.append(action_count(6, "알림 발송 규칙: `(긴급 표시(A)가 있거나 관리자 지정(B)이거나) 그리고 수신 거부(C)가 아닐 때` 알림을 보낸다. 세 조건 모두 참/거짓이고, 수신 거부 조건 C는 '수신 거부 상태'가 참이다. 알림이 발송되는 규칙은 몇 개인가?",
                            ["A", "B", "C"], lambda a, b, c: (a or b) and not c,
                            [("(A or B) and C", lambda a, b, c: (a or b) and c, "수신 거부가 참인 경우를 발송으로 읽었다. 조건 C는 부정(아닐 때)으로 걸려 있다."),
                             ("A or (B and not C)", lambda a, b, c: a or (b and not c), "긴급이면 수신 거부와 무관하게 발송되는 것으로 읽었다. 수신 거부 부정은 전체에 걸린다.")], 2))
    out.append(collapsed(7, "uncovered", ["회원", "쿠폰", "야간"],
                         [("YY-", "10% 할인"), ("N-Y", "야간 가산"), ("YNN", "할인 없음")], 2))
    out.append(collapsed(8, "overlap", ["승인", "한도 초과", "재고 있음", "이벤트"],
                         [("Y-Y-", "배송"), ("-NY-", "배송"), ("Y--Y", "사은품"), ("N---", "반려")], 3))
    out.append(collapsed(9, "expand", ["가입", "미납", "연령 확인", "동의"],
                         [("Y--N", "가입 보류"), ("YN-Y", "정상"), ("N---", "거절"), ("Y-NY", "추가 확인")], 3))
    return out
