# Typescript(NestJS) 레이어드 아키텍처 - 서비스 코드 패턴

생성일: 2026년 3월 12일 오후 3:36
역할: BE
작성자: 제라드(김재현)
작성 시간: 2026년 3월 12일 오후 3:36
수정자: 제라드(김재현)
수정 시간: 2026년 3월 12일 오후 7:23
버전: r0
ID: BE-6
활성여부: Active

## Title

NestJS 코드 아키텍처 - 서비스 패턴

## Rule

### Service (서비스)

- **역할**: 비즈니스 로직 수행, 트랜잭션 관리.
- **주입**: Repository, `DataSource`, 다른 Service 등을 주입받습니다.
- **트랜잭션**: `@Transactional` 어노테이션을 사용해 트랜잭션을 관리합니다.
- **리턴타입** : 서비스 레이어에서 리턴타입은 재사용성을 위해 엔티티를 리턴합니다.
- 도메인 로직 : 도메인 로직은 서비스 레이어에서 로직으로 처리하지 않고 엔티티에서 메서드를 호출해 처리합니다.

```jsx
@Injectable()
export class JobPostingService {
  constructor(
    private readonly jobPostingRepository: JobPostingRepository,
    private readonly jobApplicationRepository: JobApplicationRepository,
    private readonly interviewOfferRepository: InterviewOfferRepository,
    private readonly boardRepository: BoardRepository,
    private readonly boardCounterRepository: BoardCounterRepository,
    private readonly resumeService: ResumeService,
    private readonly piiCrypto: PiiCryptoService,
    private readonly dataSource: DataSource
  ) { }
  /**
   * 구인글 생성
   * - Board(type=6) 생성 → JobPosting 생성 (트랜잭션)
   */
  @Transactional()
  async generateJobPosting(dto: CreateJobPostingServiceDto, authorId: number) {
    const board = await this.boardRepository.createBoard({
      authorId,
      type: BoardType.JOB,
      title: dto.title,
      content: '',
      model: null,
      storeId: dto.storeId,
    });

    const jobPosting = plainToInstance(JobPosting, {
      ...dto,
      boardId: board.id,
      status: JobPostingStatus.ACTIVE
    });

    jobPosting.managerNameAes = this.piiCrypto.encryptAES256(dto.managerName);
    jobPosting.managerPhoneAes = this.piiCrypto.encryptAES256(dto.managerPhone);

    return await this.jobPostingRepository.createJobPosting(jobPosting);
  }
}

```

## Rationale

## Exception

## Override