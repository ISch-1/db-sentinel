package com.dbsentinel.config;

import java.net.URI;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.DefaultCredentialsProvider;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.dynamodb.DynamoDbClient;

/**
 * Builds the DynamoDB client. When {@code AWS_ENDPOINT_URL} is set (LocalStack)
 * we use static test credentials and the custom endpoint; otherwise we fall back
 * to the default AWS credential chain and real endpoints — same code, both
 * environments.
 */
@Configuration
public class AwsConfig {

    @Bean
    public DynamoDbClient dynamoDbClient(
            @Value("${AWS_ENDPOINT_URL:}") String endpoint,
            @Value("${AWS_REGION:us-east-1}") String region) {

        var builder = DynamoDbClient.builder().region(Region.of(region));

        if (endpoint != null && !endpoint.isBlank()) {
            builder = builder
                    .endpointOverride(URI.create(endpoint))
                    .credentialsProvider(StaticCredentialsProvider.create(
                            AwsBasicCredentials.create("test", "test")));
        } else {
            builder = builder.credentialsProvider(DefaultCredentialsProvider.create());
        }
        return builder.build();
    }
}
