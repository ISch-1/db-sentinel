FROM maven:3.9-eclipse-temurin-21 AS builder

WORKDIR /src
COPY pom.xml ./
RUN mvn -q -B dependency:go-offline
COPY src ./src
RUN mvn -q -B -DskipTests package

# ------------------------------------------------------------------

FROM eclipse-temurin:21-jre-alpine AS runtime

WORKDIR /app
COPY --from=builder /src/target/control-plane.jar /app/control-plane.jar

EXPOSE 8080 9100
RUN addgroup -S app && adduser -S app -G app
USER app

ENTRYPOINT ["java", "-jar", "/app/control-plane.jar"]
