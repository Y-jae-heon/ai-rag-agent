# FSD 레이어드 아키텍처 README 템플릿

ID: FE-3
버전: r0
생성일: 2026년 3월 13일 오후 3:46
수정 시간: 2026년 3월 16일 오후 9:32
수정자: 무무(염재헌)
역할: FE
작성 상태: 작성완료
작성 시간: 2026년 3월 13일 오후 3:46
작성자: 무무(염재헌)
활성여부: Active

## **Title**

프론트엔드 README 템플릿

## **Rule**

프론트엔드에서 사용되는 프로젝트 내 [README.md](http://README.md) 파일은 기본적으로 다음과 같이 구성합니다.

### **프로젝트 개요**

| 항목        | 내용                              |
| ----------- | --------------------------------- |
| 프레임워크  | React 19                          |
| 스타일      | Tailwind CSS + shadcn/ui          |
| 상태관리    | Zustand + React Query             |
| API 통신    | RESTful API 기반, Axios 래퍼 사용 |
| 타입 시스템 | TypeScript                        |
| 테스트      | Vitest (단위), Playwright (E2E)   |
| 배포 환경   | AWS S3, CloudFront                |

---

### **설치 및 실행**

```bash
# 의존성 설치
yarn install // or yarn

# 로컬 실행
yarn dev

# 프로덕션 실행
yarn dev:prod

# 개발 빌드
yarn build:dev

# 프로덕션 빌드
yarn build:prod

# 스토리북 실행
yarn storybook

# 스토리북 빌드
yarn build:storybook
```

### **폴더 구조 요약**

```bash
📁 src/
├─ 📁 app/                            # 전역스타일/프로바이더/라우팅설정
│  ├─ 📁 i18n/
│  ├─ 📁 providers/
│  ├─ 📁 routing/
│  │  ├─ 📄 routes.tsx
│  │  ├─ 📄 paths.tsx
│  │  └─ 📄 guards.tsx
│	└─	📁 styles/
├─ 📁 pages/                          # 라우트 단위 조립
│  ├─ 📁 dashboard
│  │  ├─ 📄 MainDashboardPage.tsx
│  │  └─ 📄 MonthlyAnalyticsDashboardPage.tsx
│  ├─ 📁 auth
│  │  ├─ 📄 SignInPage.tsx
│  │  └─ 📄 SignUpPage.tsx
│  └─ 📁 station
│     ├─ 📄 StationListPage.tsx
│     ├─ 📄 StationDetailPage.tsx
│     └─ 📄 StationDetailEdit.tsx
│
├─ 📁 widgets/                        # 여러 도메인이 합쳐진 UI
│  └─ 📁 station-overview
│     ├─ 📁 ui/
│     │  └─ 📄 StationOverviewPanel.tsx
│     ├─ 📁 model/
│     │  ├─ 📄 station-overview.dto.ts
│     │  ├─ 📄 station-overview.schema.ts
│     ├─ 📁 hooks/
│     │  ├─ 📄 use-station-overview.ts
│     ├─ 📁 store/
│     │  ├─ 📄 use-station-overview.store.ts
│     ├─ 📁 api/
│     │  └─ 📄 station-overview.ts
│     ├─ 📁 lib/
│     │  └─ 📄 mappers.ts
│     └─ 📄 index.ts
│
├─ 📁 features/                       # 동사(CUD) 중심의 비즈니스 로직
│  ├─ 📁 sign-in/
│  │  ├─ 📁 ui/
│  │  │  └─ 📄 SignInForm.tsx
│  │  ├─ 📁 model/
│  │  │  ├─ 📄 sign-in.dto.ts
│  │  │  ├─ 📄 sign-in.schema.ts
│  │  ├─ 📁 hooks/
│  │  │  ├─ 📄 use-sign-in-mutation.ts
│  │  ├─ 📁 store/
│  │  │  ├─ 📄 use-sign-in.store.ts
│  │  ├─ 📁 api/
│  │  │  └─ 📄 sign-in.ts
│  │  ├─ 📁 lib/
│  │  │  └─ 📄 mappers.ts
│  │  └─ 📄 index.ts
├─ 📁 entities/                       # 명사(Read) 중심
│  └─ 📁 auth/
│     ├─ 📁 ui/
│     │  └─ 📄 Avatar.tsx
│     ├─ 📁 model/
│     │  ├─ 📄 auth.entity.ts
│     │  ├─ 📄 auth.dto.ts
│     ├─ 📁 api/
│     │  └─ 📄 authQueries.ts
│     ├─ 📁 hooks/
│     │  ├─ 📄 use-session-query.ts
│     ├─ 📁 store/
│     │  ├─ 📄 use-session.store.ts
│     ├─ 📁 lib/
│     │  └─ 📄 mappers.ts
│     └─ 📄 index.ts
└─ 📁 shared/                         # 전역 공용
   ├─ 📁 api/
   │  ├─ 📄 http.ts
   │  └─ 📄 queryClient.ts
   ├─ 📁 lib/
   │  ├─ 📄 formatters.ts
   │  ├─ 📄 analytics.ts
   │  └─ 📄 logger.ts
   ├─ 📁 ui/
   │  ├─ 📁 core
   │  │  ├─ 📄 Button.tsx
   │  │  ├─ 📄 Input.tsx
   │  │  └─ 📄 ...etc.tsx
   │  └─ 📁 lib
   │  │  └─ 📄 ...shadcnComponent.tsx
   │  └─ 📄 index.ts
   └─ 📁 assets/
      ├─ 📁 fonts/
      ├─ 📁 icons/
      └─ 📁 images/
```

---

### **FSD 패턴 요약**

- app: 전역스타일/프로바이더/라우팅설정
- pages: 라우트 단위 조립
- widgets: 여러 도메인이 합쳐진 UI
- features: 동사(CUD) 중심의 비즈니스 로직
  - 기본적으로 동사로 작성되며, Create, Update, Delete와 관련된 비즈니스 로직과 해당 로직이 사용되는 UI 또는 사용자의 행위 및 시나리오가 포함된 기능 단위 및 UI는 여기에 해당함
- entities: 명사(Read) 중심 비즈니스 모델
  - 기본적으로 명사로 작성되며, Read와 관련된 비즈니스 로직과 해당 로직이 사용되는 UI가 여기에 해당함
  - 서버의 Entity와 비슷한 역할을 수행(작은 단위의 도메인, User, Product 등)
- shared: 전역에서 사용되는 함수 및 UI

---

### **도메인 분리 기준**

- ✅ 비즈니스 로직, API 종속성, 사용자의 행위 (동사)가 포함된 기능 단위 및 UI는 `/features/{domain}` 내부에 배치
- ✅ 비즈니스 로직, API Domain 종속적인 기능 단위 및 UI는 `/entities/{domain}` 내부에 배치
- ✅ `api/`, `services/`, `hooks/`는 명확하게 역할 구분하여 관심사 분리 유지

---

### **네이밍 컨벤션 요약**

| 구분                 | 예시               |
| -------------------- | ------------------ |
| 폴더 (도메인)        | `kebab-case`       |
| Model, api 파일명    | `kebab-case`       |
| 훅 파일명            | `kebab-case`       |
| Util 파일명          | `kebab-case`       |
| API 함수명           | `camelCase`        |
| 컴포넌트 파일/함수명 | `PascalCase`       |
| 타입/인터페이스      | `PascalCase`       |
| enum / 상수          | `UPPER_SNAKE_CASE` |

> 📌 전체 네이밍 규칙은 팀 컨벤션 문서에 상세 명시됨

---

### **참조**

> ✅ 누구든지 이 README 로 구조를 파악하고 일관된 규칙으로 개발할 수 있도록 작성되었습니다.
>
> **구조가 변경될 경우 반드시 README도 함께 갱신**해주세요

## **Rationale**

이 문서는 본 프로젝트의 **프론트엔드 FSD 구조와 컨벤션 적용 방식**을 설명합니다. 팀의 아키텍처 가이드라인(FSD)을 바탕으로, 이 프로젝트가 어떻게 구현되었는지를 명확히 전달하는 [README.md](http://README.md) 파일의 예시입니다.

---

## **Exception**

## **Override**

프로젝트 내 특이 사항의 경우 위와 같이 짜임새 있도록 추가하여 [README.md](http://README.md) 파일을 갱신할 수 있습니다.
