# Typescript(NestJS) 레이어드 아키텍처 - 컨트롤러 코드 패턴

생성일: 2026년 3월 12일 오후 3:05
역할: BE
작성자: 제라드(김재현)
작성 시간: 2026년 3월 12일 오후 3:05
수정자: 제라드(김재현)
수정 시간: 2026년 3월 12일 오후 7:23
버전: r0
ID: BE-5
활성여부: Active

## Title

NestJS 코드 아키텍처 - 컨트롤러 패턴

## Rule

**Controller**

- **역할** : HTTP 요청 처리, 입력값 검증, 서비스 호출.
- **Swagger** : 문서화를 위해 `@ApiTags` (`swaggerConstants` 사용)와 `@ApiDoc` (커스텀 데코레이터)를 사용합니다.
    - `@ApiDoc` : summary, responseModel (응답 DTO), isArrayResponse (배열 여부) 등 정보를 기입합니다.
    
    ```tsx
    export interface ApiDocOptions {
      summary: string; // 설명
      description?: string; // 설명 상세
      responseModel?: Type<any>; // 응답 객체 Class
      isArrayResponse?: boolean; // 응답 객체가 배열 형식일 경우 'true' 로 설정
      /**
       * 인증된 유저만 호출가능할 경우 'true' 로 설정
       * 설정시 Api Header JWT 입력 스펙을 자동으로 추가
       */
      authUserOnly?: boolean;
    
      /**
       * 인증된 관리자 유저만 호출가능할 경우 'true' 로 설정
       * 설정시 Api Header JWT 입력 스펙을 자동으로 추가
       */
      adminUserOnly?: boolean;
      batchOnly?: boolean; // 배치 작업일 경우 'true'로 설정
      pagination?: boolean; // Pagination 문서 추가
      deprecated?: boolean; // 디플리케이티드 여부
    }
    ```
    
- **검증** : Pipe (ParseIntPipe 등)와 class-validator가 적용된 DTO를 사용합니다.
- **경로** : 경로는 기본적으로 케밥 케이스를 사용하고, 자원은 복수형으로 표기합니다. 리소스 이름은 카멜케이스를 사용합니다
    - ex) `user-temas/boards/:boardId/attachments`)
- **응답** : 서비스 레이어에서 엔티티로 응답하기 때문에, 엔티티 내부 구조를 가리기 위해 DTO로 변환시켜 리턴합니다.

```tsx
@Controller('/auth/users')
@ApiTags(swaggerConstants.COMMON_API_TAGS.USER)
@UseGuards(JwtAccessTokenGuard)
export class UserController {
  constructor(private readonly service: UserService) {}

  @ApiDoc({
    summary: '세션 조회',
    responseModel: GetUserByTokenResponseDto,
    authUserOnly: true,
  })
  @Get('/me')
  async getUserByToken(@CurrentUser() user: AuthUser) {
    const result = await this.service.getUserByToken(user);
		const responseDto = GetUserByTokenResponseDto.fromUser(result);
    return new ObjectResponse(responseDto);
  }
}
```

## Rationale

## Exception

## Override