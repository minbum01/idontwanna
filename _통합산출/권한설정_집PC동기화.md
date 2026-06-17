# Claude Code 권한 설정 — 집 PC 동기화 가이드

집에서 yes(확인)를 매번 눌러야 하는 이유와, 회사 PC처럼 **묻지 않고 자동 통과**되게 맞추는 방법.

## 왜 집에서는 yes를 자주 물어볼까?
회사 PC의 **전역 설정**(`C:\Users\<사용자>\.claude\settings.json`)에 "모든 작업 허용" 규칙이 들어 있어서, 파일 수정·명령 실행·검색이 **확인 없이 바로 통과**된다.
집 PC에는 이 규칙이 없어서 기본 모드(작업마다 물어봄)로 동작 → Edit/Write/Bash 할 때마다 yes를 눌러야 함.

## 회사 PC에 들어있는 설정 (참고)

### ① 전역 설정 — `C:\Users\<사용자>\.claude\settings.json`
```json
{
  "permissions": {
    "allow": [
      "Bash(*)",
      "Edit(*)",
      "Write(*)",
      "Read(*)",
      "Glob(*)",
      "Grep(*)",
      "WebFetch(*)",
      "WebSearch(*)"
    ]
  }
}
```
- `*` = 전부 허용. 이 8개가 핵심(Bash·Edit·Write가 yes 대부분의 원인).
- 기존 settings.json에 다른 키(theme, effortLevel 등)가 있으면 **`permissions` 블록만 추가/병합**하면 된다.

### ② 프로젝트 설정 — `<프로젝트>\.claude\settings.json` (선택)
프로젝트별로 자주 쓰는 명령을 추가로 허용. 예) 결과 HTML 열기 명령 등. 없어도 ①만으로 충분.

## 집 PC 적용 방법 (3가지 중 택1)

### 방법 A — 전역 설정에 붙여넣기 (추천, 모든 프로젝트 적용)
1. 파일 열기: `C:\Users\<사용자>\.claude\settings.json`
   - 없으면 새로 만들고 위 ① 내용을 그대로 저장.
   - 있으면 `permissions` 블록만 병합(아래 "병합 예시" 참고).
2. Claude Code 재시작.

**병합 예시** (기존에 theme 등이 있을 때):
```json
{
  "theme": "dark-daltonized",
  "effortLevel": "high",
  "permissions": {
    "allow": ["Bash(*)", "Edit(*)", "Write(*)", "Read(*)", "Glob(*)", "Grep(*)", "WebFetch(*)", "WebSearch(*)"]
  }
}
```

### 방법 B — 세션에서 토글 (그 세션만)
- 실행 중 `Shift + Tab` 을 눌러 권한 모드를 전환(auto-accept edits 등).
- 임시로 한 번만 자동 통과시키고 싶을 때.

### 방법 C — 승인할 때 "앞으로 허용" 선택
- yes 물어볼 때 "이 명령은 앞으로 허용" 류 항목을 고르면 그 규칙이 settings에 자동 누적됨.
- 안전하게 필요한 것만 하나씩 쌓는 방식.

## ⚠️ 주의
- `Bash(*)` / `Write(*)` 처럼 전부 허용하면 편하지만, **확인 없이 실행**되므로 신뢰하는 환경(본인 PC)에서만 사용.
- 더 안전하게 하려면 `*` 대신 좁게 지정 가능. 예: `Bash(git*)`, `Bash(python*)`, 특정 폴더만 등.
- `permissions`에는 `allow` 외에 `deny`(차단), `ask`(항상 물어봄)도 쓸 수 있다.

## 요약
집 `~/.claude/settings.json`에 위 `permissions.allow` 8줄을 넣고 재시작 → 회사 PC와 동일하게 묻지 않고 진행됨.
