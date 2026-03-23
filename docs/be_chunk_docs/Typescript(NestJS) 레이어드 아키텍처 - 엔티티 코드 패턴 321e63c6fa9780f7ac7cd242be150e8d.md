# Typescript(NestJS) 레이어드 아키텍처 - 엔티티 코드 패턴

생성일: 2026년 3월 12일 오후 4:12
역할: BE
작성자: 제라드(김재현)
작성 시간: 2026년 3월 12일 오후 4:12
수정자: 제라드(김재현)
수정 시간: 2026년 3월 12일 오후 7:23
버전: r0
ID: BE-9
활성여부: Active

## Title

NestJS 코드 아키텍처 - 엔티티 패턴

## Rule

### Entity (엔티티)

- 도메인의 핵심 데이터를 표현하며, 도메인 로직을 구현합니다.
- 모든 비즈니스 엔티티는 `CoreSoftEntity` 를 상속받습니다.

- **TypeORM**: 표준 데코레이터(`@Entity`, `@Column`, `@ManyToOne` 등)를 사용합니다.
    - DB 제약 조건 없이 객체 탐색이 가능하도록 `ManyToOne`에 `{ createForeignKeyConstraints: false }`를 설정합니다.
- **Swagger**: 외부에 노출되는 필드일 경우 자동 API명세 모델 생성을 위해 속성에 `@ApiProperty`를 붙입니다.
- **네이밍**: `name` 옵션을 사용하여 DB의 `snake_case` 컬럼을 TS의 `camelCase` 속성과 매핑합니다.
- **Soft Delete**: `deletedAt` 컬럼(`datetime`)을 사용하며, 레포지토리 로직이나 수동으로 처리합니다.
- **연관관계** : 연관관계 필드는 항상 맨 마지막에 작성합니다. 연관관계에서 외래키를 가지고 있는 자식은 필드로 항상 외래키를 가지고 있습니다.
    
    ```tsx
    @Enity('user') {
      ...
      @ApiProperty({
        description: '팀 ID',
        example: '1'
      })
      @Column({type: 'bigint', name: 'team_id', nullable: false})
      teamId: number;
      
      @ApiProperty({description: '팀 (1 : N) 유저', type: () => Team})
      @ManyToOne(() => Team)
      @JoinColumn({name: 'team_id'})
      team: Team;
    }
    ```
    
- **어노테이션** `@ApiProperty` , `@Column` 를 사용해 일반 필드를 표현합니다.
- **도메인 로직** : 도메인 로직은 엔티티에 작성합니다.
    
    ```tsx
    @Entity('product') {
    	...
    	decreaseStock(quantity: number): void {
    		if (quantity <= 0) { 
    			throw new BadRequestException('수량은 0보다 커야 합니다');
    		}
    		if (this.stick < quantity) {
    			throw new BadRequestException('재고가 부족합니다');
    		}
    		this.stock -= quantity;
    	}
    }
    ```
    
- **필드 Swagger, Validator 규칙** (DTO에서 필드를 재사용하기 때문에 규칙을 엔티티에 적용)
    - `공통`
        - `@ApiProperty` 를 사용해 Swagger 문서를 정의합니다.
        - `@IsOptional` 을 사용해 옵셔널한 필드를 정의합니다.
    - `string` : `@IsString`  을 사용합니다.
    - `string[]` : `@IsString({each: true})` `@ToArray(String)` 을 사용합니다.
    - `number` : `@IsNumber` 를 사용합니다.
    - `number[]` : `@IsNumber({}, {each: true})` 와 `@ToArray(Number)` 를 사용합니다.
    - `boolean` : `@IsBoolean` 을 사용합니다.
    - `boolean[]` : `@IsBoolean({each: true})` 와 `@ToArray(Boolean)` 을 사용합니다.
    - `date` :  `@IsDate` 를 사용합니다.
    - `ENUM` : `@IsEnum(EnumName)` 을 사용합니다.
    - `ENUM[]` : `@IsEnum(EnumName)` 와 `ToArray(EnumName)` 을 사용합니다.
    - `object` : `@Type(() => Object)` , `@ValidateNested` 를 사용합니다.
    - `object[]` : `@Type(() => Object)`, `@ValidateNested` 를 사용합니다.
    - to-array.ts (`@ToArray(Number)`)
        
        ```tsx
        import { applyDecorators } from '@nestjs/common';
        import { Transform, plainToInstance } from 'class-transformer';
        
        type PrimitiveConstructor =
          | StringConstructor
          | NumberConstructor
          | BooleanConstructor;
        
        type ClassConstructor<T = any> = new (...args: any[]) => T;
        
        export function ToArray(
          type?: PrimitiveConstructor | ClassConstructor | object,
        ) {
          return applyDecorators(
            Transform(({ value }) => {
              if (value === undefined || value === null) return undefined;
        
              const arr = Array.isArray(value) ? value : [value];
        
              if (!type) return arr;
        
              // 🔥 Primitive
              if (type === String || type === Number || type === Boolean) {
                if (type === Boolean) {
                  return arr.map((v) => v === 'true' || v === true);
                }
        
                return arr.map((v) => (type as PrimitiveConstructor)(v));
              }
        
              // 🔥 Class (DTO 객체)
              if (typeof type === 'function') {
                return arr.map((v) =>
                  plainToInstance(type as ClassConstructor, v),
                );
              }
        
              // 🔥 Enum
              const enumValues = Object.values(type);
              return arr.map((v) => {
                if (enumValues.includes(v)) return v;
        
                const numeric = Number(v);
                if (!isNaN(numeric) && enumValues.includes(numeric)) {
                  return numeric;
                }
        
                return v;
              });
            }),
          );
        }
        ```
        

## Rationale

## Exception

## Override