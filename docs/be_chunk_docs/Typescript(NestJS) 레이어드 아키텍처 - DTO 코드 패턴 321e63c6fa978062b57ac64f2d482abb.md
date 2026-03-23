# Typescript(NestJS) 레이어드 아키텍처 - DTO 코드 패턴

생성일: 2026년 3월 12일 오후 4:16
역할: BE
작성자: 제라드(김재현)
작성 시간: 2026년 3월 12일 오후 4:16
수정자: 제라드(김재현)
수정 시간: 2026년 3월 12일 오후 7:23
버전: r0
ID: BE-10
활성여부: Active

## Title

NestJS 코드 아키텍처 - DTO 패턴

## Rule

### DTO (Data Transfer Object)

- 기본 엔티티로부터 DTO를 뽑아내고, 목적에 따라 이 DTO를 상속해 DTO를 만들어 사용합니다.
    - {SOME}Entity → {SOME}Dto → {METHOD}{SOME}Dto → …
    
    ```tsx
    class User {
      @ApiProperty({ description: '로그인 아이디', example: 'hong_01' })
      @Column({ type: 'varchar', length: 50 })
      username!: string;
    
      @ApiProperty({
        description: '이메일',
        example: 'john@example.com',
        nullable: true,
      })
      @Column({ type: 'varchar', length: 254, nullable: true })
      email!: string;
    
      @ApiProperty({
        description: '비밀번호 해시(bcrypt 60자)',
        example: '$2b$10$...',
      })
      @Column({ name: 'password_hash', type: 'char', length: 60, nullable: true })
      passwordHash!: string;
    
      @ApiProperty({
        description: '휴대폰 번호(숫자만)',
        example: '01012345678',
        nullable: true,
      })
      @Column({ type: 'varchar', length: 30, nullable: true })
      phone!: string;
    }
    
    class UserDto extends OmitType(User, ['passwordHash']) {}
    
    class GetUserDto extends PickType(UserDto, ['username', 'email']) {}
    ```
    
- **상속**: 중복을 줄이기 위해 `@nestjs/swagger`의 `IntersectionType`, `PickType`, `OmitType`을 사용하여 Entity 필드를 상속받습니다.
- **검증**: Entity를 상속받지 않거나 추가 규칙이 필요한 경우 `class-validator` 데코레이터를 사용합니다.
- **추가 필드** : 엔티티로부터 상속할 수 없는 필드의 경우 DTO에서 직접 생성합니다.
- **변환 메서드** : 엔티티를 가지고 변환하는 to, from 메서드는 DTO에 정의합니다.
    
    ```tsx
    export class JobPostingListItemDto {
    	...
    
      static fromJobPosting(jp: JobPosting): JobPostingListItemDto {
        const region = jp.region;
        return plainToInstance(JobPostingListItemDto, {
          id: jp.id,
          title: jp.board?.title,
          storeName: jp.board?.store?.storeName,
          regionName: region
            ? `${region.sido} ${region.sigungu ?? ''}`.trim()
            : undefined,
          applyEndAt: jp.applyEndAt,
          experience: jp.experience,
        });
      }
    }
    ```
    

## Rationale

## Exception

## Override