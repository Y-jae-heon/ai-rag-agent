# Java(Spring) 데이터 소스 관리

생성일: 2026년 3월 12일 오후 7:46
역할: BE
작성자: 제라드(김재현)
작성 시간: 2026년 3월 12일 오후 7:46
수정자: 제라드(김재현)
수정 시간: 2026년 3월 12일 오후 7:56
버전: r0
ID: BE-25
활성여부: Active

## Title

Java(Spring) 데이터 소스 관리

## Rule

### 데이터소스 관리

- 데이터 소스가 **1개**인 경우 Spring의 Auto Config 를 사용합니다.
- 데이터소스가 **2개 이상**인경우 데이터소스와 트랜잭션 매니저를 직접 선언합니다.
    - 트랜잭션에서는 트랜잭션 매니저의 이름으로 관리합니다.
    
    ```java
    @Configuration
    public class BatchConfig {
    
        @Primary
        @Bean
        @ConfigurationProperties(prefix = "spring.datasource.batch")
        public DataSource batchDataSource() {
            return DataSourceBuilder.create().build();
        }
    
        @Primary
        @Bean
        public PlatformTransactionManager batchDataSourceTransactionManager() {
            return new DataSourceTransactionManager(batchDataSource());
        }
    }
    ```
    

```java
@Configuration
public class JpaConfig {

    @Bean
    @ConfigurationProperties(prefix = "spring.datasource.business")
    public DataSource businessDataSource() {
        return DataSourceBuilder.create().build();
    }

    @Bean
    public LocalContainerEntityManagerFactoryBean dataEntityManagerFactory() {
        LocalContainerEntityManagerFactoryBean em = new LocalContainerEntityManagerFactoryBean();
        em.setDataSource(businessDataSource());
        em.setPackagesToScan("batch.adapter.out.persistence", "core.entity");
        em.setJpaVendorAdapter(new HibernateJpaVendorAdapter());

        Map<String, Object> properties = new HashMap<>();
        properties.put("hibernate.hbm2ddl.auto", "none");
        properties.put("hibernate.show_sql", "true");
        em.setJpaPropertyMap(properties);

        return em;
    }

    @Bean
    public PlatformTransactionManager dataTransactionManager() {
        JpaTransactionManager transactionManager = new JpaTransactionManager();
        transactionManager.setEntityManagerFactory(dataEntityManagerFactory().getObject());
        return transactionManager;
    }
}
```

## Rationale

## Exception

## Override