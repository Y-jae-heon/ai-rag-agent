# Typescript(NestJS) 레이어드 아키텍처 - 레포지토리 코드 패턴

생성일: 2026년 3월 12일 오후 3:44
역할: BE
작성자: 제라드(김재현)
작성 시간: 2026년 3월 12일 오후 3:44
수정자: 제라드(김재현)
수정 시간: 2026년 3월 12일 오후 7:23
버전: r0
ID: BE-7
활성여부: Active

## Title

NestJS 코드 아키텍처 - 레포지토리 패턴

## Rule

### Repository (레포지토리)

- **역할**: 복잡한 DB 쿼리(QueryBuilder) 및 데이터 접근 로직 캡슐화.
- **베이스 클래스**: `Repository<Entity>`를 상속받습니다.
- **커스텀 메서드**: 도메인 특화 쿼리를 구현합니다 (예: `findUserDetailList`).

**생성 Create 메서드**

- 레포지토리 레이어에서는 비즈니스 로직을 처리하지 않습니다.
- 엔티티를 파라미터로 넘기며 레포지토리 계층에서는 이에대한 저장만 수행합니다.

```tsx
async createJobPosting(jobPosting: JobPosting): Promise<JobPosting> {
  return await this.save(jobPosting);
}
```

**조회 Read 메서드 (단일)**

- 엔티티를 상속한 Get{Domain}Dto 를 사용합니다.
    - GetDto 에는 조회에 필요한 필터 값들이 `PickType` 으로 정의되어 있습니다.
    - GetDto 에는 연관관계에 대한 조인 정보가 `relations` 라는 필드로 제공됩니다.
    
    ```tsx
    export class GetUserDto extends PartialType(UserDto) {
      relations: {
        withPii?: boolean;
      }
    }
    ```
    
- 조회 메서드는 `buildQuery` 를 호출해 기본적인 조인, 조건 정보를 설정합니다.
- 조인 정보는 레포지토리 계층에서 설정합니다.
    
    ```tsx
    async findJobPosting(dto: GetJobPostingDto) {
      const query = this.buildQuery({
        ...dto,
        relations: {withBoard: true, withRegion: true, withStore: true, withSupportField: true}
      });
    
      return await query.getOne();
    }
    ```
    
- 찾는 값이 없다면 `NULL` 을 리턴합니다.

**조회 Read 메서드 (리스트)**

- 대게 리스트 조회에 필요한 DTO를 사용합니다.
- 페이지네이션이 필요하다면 페이지네이션 정보를 같이 전달합니다.
    
    ```tsx
    export interface Pagination {
      page: number;
      pageSize: number;
    }
    ```
    
- `getManyAndCount` 를 사용해 리스트와 카운트를 같이 조회합니다.
    
    ```tsx
    async findResumeListAndCount(
      dto: GetResumeListDto,
      pagination?: Pagination,
    ) {
      const {regionIds, supportFieldIds, column, order} = dto;
    
      const query = this.buildQuery({
          ...dto,
          relations: {
            withSupportField: true,
            withRegionResumes: true,
            withRegion: true
          }
        },
        pagination);
    
      query.andWhere('(resume.expiredAt IS NULL OR resume.expiredAt > NOW())');
    
      if (regionIds) {
        query.andWhere('rr.regionId IN (:...regionIds)', {regionIds});
      }
    
      if (supportFieldIds) {
        query.andWhere('resume.supportId IN (:...supportFieldIds)', {
          supportFieldIds,
        });
      }
    
      switch (column) {
        case 'publishedAt':
          query.orderBy('resume.publishedAt', order)
          break;
        default:
          query.orderBy('resume.createdAt', 'DESC');
          break;
      }
    
      const [list, count] = await query.getManyAndCount();
    
      return {list, count};
    }
    ```
    

**수정 Update 메서드**

- Create 메서드와 동일합니다.

**삭제(복구) Delete 메서드**

- Repository 에 기본으로 정의된 `softDelete`, `restore` 를 사용합니다.

**buildQuery** 

- 트랜잭션 처리와 엔티티 조회시 필요한 조건들을 정의한 기본 쿼리 생성 메서드 입니다. where, join 등이 포함됩니다.

```tsx
private buildQuery(dto: GetUserDto, transactionManager?: EntityManager) {
  let query: SelectQueryBuilder<User>;
  const { id, status, username, email, phone, withPii } = dto;
  if (transactionManager) {
    query = transactionManager.createQueryBuilder(User, 'u');
  } else {
    query = this.createQueryBuilder('u');
  }

  if (withPii) {
    query.innerJoinAndMapOne('u.userPii', UserPii, 'up', 'u.id = up.user_id');
  }

  if (id) {
    query.andWhere('u.id = :id', { id });
  }
  if (status) {
    query.andWhere('u.status = :status', { status });
  }
  if (username) {
    query.andWhere('u.username = :username', { username });
  }
  if (email) {
    query.andWhere('u.email = :email', { email });
  }
  if (phone) {
    query.andWhere('u.phone = :phone', { phone });
  }

  return query;
}
```

## Rationale

## Exception

## Override