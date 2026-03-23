# Typescript(NestJS) 코드 아키텍처 - 도메인 모듈

생성일: 2026년 3월 12일 오후 2:40
역할: BE
작성자: 제라드(김재현)
작성 시간: 2026년 3월 12일 오후 2:40
수정자: 제라드(김재현)
수정 시간: 2026년 3월 12일 오후 7:22
버전: r0
ID: BE-4
활성여부: Active

## Title

NestJS 코드 아키텍처 - 모듈 패턴

## Rule

- 각 도메인은 독립된 모듈을 가집니다 (예: `AttachmentModule`).

**imports**

- TypeORM 엔티티, 의존이 필요한 외부 모듈을 import 합니다.
- 순환 의존은 절대 금지합니다.
- 순환 의존이 필요하다면 외부 모듈을 따로 만들어 의존관계를 정리합니다.
    - ex) `게시글` → `회원`, `회원` → `게시글` 참조가 필요한 상황이라면
    - `게시글` → `회원` 방향으로 참조하고, `게시글_회원` 이라는 모듈을 만들어 `게시글_회원` → `회원`, `게시글_회원` → `게시글` 로 의존을 정리합니다.

**controllers**

- 해당 도메인의 Controller 계층을 선언합니다.

**providers**

- 해당 도메인의 Service, Repository 계층을 선언합니다.

**exports**

- 노출이 필요한 경우 Service 계층만 노출시킵니다.

```tsx
@Module({
  imports: [
    TypeOrmModule.forFeature([JobPosting, JobApplication, InterviewOffer]),
    BoardModule,
    ResumeModule,
    CryptoModule
  ],
  controllers: [JobPostingController],
  providers: [
    JobPostingService,
    JobPostingRepository,
  ],
  exports: [JobPostingService]
})
export class JobPostingModule {}
```

## Rationale

## Exception

## Override