---
name: multi-review
description: "Dynamic multi-perspective review: spawn parallel critics with role separation for high-stakes decisions. Use when a decision needs validation from multiple independent viewpoints."
---

# Multi-Review Protocol

중요한 결정에 대해 독립적인 관점의 Critic들을 병렬로 실행하여 다각도 검증을 수행한다.
프로토콜은 고정, Critic 구성은 문제에 따라 매번 동적으로 결정.

## When to Activate

### User trigger
`/multi-review` 또는 "다각도로 검증해줘", "여러 관점에서 봐줘" 등

### Claude auto-suggest (제안만, 강제 아님)
다음 시그널이 감지되면 사용자에게 multi-review를 제안:
- 되돌리기 어려운 결정 (전략 파라미터 확정, 라이브 배포, 지원서 제출)
- 불확실성이 높은 판단 (데이터 부족, 트레이드오프가 명확하지 않음)
- 이전에 단일 관점 평가로 놓친 사례가 있었던 도메인

## Protocol

### Phase 1: Problem Framing

결정 대상을 구조화한다:

```
Decision: [무엇을 결정하는가]
Stakes: [잘못되면 어떤 비용이 발생하는가]
Constraints: [이미 확정된 제약 조건]
Input: [Critic들에게 전달할 자료]
```

### Phase 2: Critic Design (Dynamic)

문제에 맞는 2~4개의 Critic을 즉석 설계한다.

**설계 원칙**:
- 각 Critic의 평가 범위는 **명시적으로 분리** (겹치면 합의가 아니라 중복)
- Critic은 **자연스러운 페르소나**로 부여 (역할이 아닌 관점)
- 하나의 Critic은 **Veto 권한** 보유 가능 (해당 관점에서 치명적 결함 시 강제 기각)

**Critic 설계 템플릿**:
```
Critic N: [이름]
  Persona: [누구의 관점인가]
  Scope: [평가 범위 — 이것만 본다]
  Anti-scope: [평가하지 않는 것 — 명시적 제외]
  Veto: [있다면, 어떤 조건에서 발동하는가]
```

**모델 배정 기준**:
- 깊은 분석/판단 → opus 또는 sonnet
- 체크리스트/형식 검증 → haiku
- 기본: sonnet (비용-품질 균형)

### Phase 3: Parallel Execution

각 Critic을 **독립 서브에이전트**로 실행한다 (Agent tool).

**각 Critic에게 전달하는 프롬프트 구조**:
```
## Your Role
당신은 [Persona]입니다.

## Your Scope
당신은 오직 [Scope]만 평가합니다.
[Anti-scope]는 평가하지 마세요.

## Input
[Problem framing + 관련 자료]

## Output Format (JSON)
{
  "score": 1-10,
  "verdict": "pass" | "concern" | "veto",
  "key_findings": ["최대 3개의 핵심 발견"],
  "evidence": ["각 발견의 근거"],
  "veto_reason": null | "veto 사유 (해당 시)"
}
```

**실행 규칙**:
- 모든 Critic은 **동시에** 실행 (Agent tool 병렬 호출)
- 각 Critic은 다른 Critic의 결과를 볼 수 없음 (독립성 보장)
- Critic은 자기 scope 밖의 의견을 내지 않도록 프롬프트에서 제약

### Phase 4: Convergence Check

| 조건 | 판정 |
|------|------|
| 모든 Critic ≥ 7 AND veto 없음 | **PASS** — 요약 1줄로 보고 |
| 임의 Critic이 veto | **VETO** — veto 사유 + 해당 Critic 전문 제시 |
| 평균 ≥ 7 BUT 일부 < 7 | **MIXED** → Phase 5 Synthesis |
| 평균 < 7 | **FAIL** → Phase 5 Synthesis |

### Phase 5: Synthesis (MIXED/FAIL 시)

Critic 결과 간 충돌을 식별하고 통합 판단을 생성한다:

```
## Conflicts
- Critic A는 [X]라 판단, Critic B는 [Y]라 판단
- 충돌 원인: [왜 다른 결론에 도달했는가]

## Unified Assessment
- [통합된 판단 + 근거]
- 잔여 리스크: [해소되지 않은 우려]

## Recommendation
- [구체적 행동 제안]
- 조건부 진행 가능 여부: [있다면 조건 명시]
```

### Phase 6: Present to User

**결과 테이블**:
```
| Critic | Score | Verdict | Key Finding |
|--------|-------|---------|-------------|
| ...    | ...   | ...     | ...         |
```

**최종 판정**: PASS / VETO / MIXED + 통합 권고
**사용자 결정**: Human-in-the-loop — 최종 결정은 항상 사용자

## Harness Feedback Loop

리뷰 완료 후 학습:
- Critic이 놓친 관점이 있었다면 → 다음번 유사 문제에서 해당 관점 추가
- 사용자가 Critic 판단을 번복했다면 → 해당 Critic의 프롬프트/scope 재검토
- 반복되는 도메인이면 → 해당 Critic을 `.claude/skills/`에 전용 스킬로 승격 (Level 3)

학습 피드백 기록 경로:
- **프로젝트 특화 학습** → 해당 프로젝트의 memory/ (예: `feedback_review_*.md`)
- **multi-review 프로토콜 자체 개선** → 이 SKILL.md의 Anti-Patterns에 추가
- 스코프 판별: "이 학습이 다른 프로젝트에서도 적용되나?" → Yes=SKILL.md, No=프로젝트 memory

## Anti-Patterns

- 사소한 결정에 multi-review 남용 (3줄 코드 변경에 4-Critic은 과잉)
- Critic 간 scope가 겹쳐서 같은 말을 반복
- 모든 Critic에게 동일한 모델 사용 (관점 다양성 저하)
- Synthesis 없이 점수만 평균 내서 판단
- 사용자 결정권 무시 (Critic 합의 ≠ 최종 결정)
- **Iteration drift**: 같은 문제에 3회 이상 이터레이션 시 복잡도(변경 개수/메커니즘 수)가 증가하고 있다면 수렴이 아니라 발산이다. 메커니즘-온-메커니즘을 멈추고 minimal-viable로 회귀하라. 근본 원인 진단 없이 global intervention 금지. 매 이터레이션마다 "이 변경이 기존 규칙의 부재를 해결하는가, 아니면 기존 규칙 위반을 보상하는가?"를 자문할 것 — 후자라면 규칙을 강화할 게 아니라 **위반 원인을 먼저 진단**해야 한다.
- **Convergence Critic 상시 포함**: 2회 이상 이터레이션되는 multi-review에는 반드시 Convergence vs Drift 메타 Critic을 포함시켜 iteration 건강도를 체크할 것.
