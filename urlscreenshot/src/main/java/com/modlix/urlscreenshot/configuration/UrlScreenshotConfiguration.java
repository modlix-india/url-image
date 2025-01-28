package com.modlix.urlscreenshot.configuration;

import org.springframework.cache.CacheManager;
import org.springframework.cache.caffeine.CaffeineCacheManager;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import com.github.benmanes.caffeine.cache.Caffeine;

@Configuration
public class UrlScreenshotConfiguration implements WebMvcConfigurer {

    @SuppressWarnings("rawtypes")
    @Bean
    public Caffeine caffeineConfig() {
        return Caffeine.newBuilder().maximumSize(100);
    }

    @SuppressWarnings({ "rawtypes", "unchecked" })
    @Bean
    public CacheManager cacheManager(Caffeine caffeine) {
        CaffeineCacheManager caffeineCacheManager = new CaffeineCacheManager();
        caffeineCacheManager.setCaffeine(caffeine);
        return caffeineCacheManager;
    }

    @SuppressWarnings("null")
    @Override
    public void addCorsMappings(CorsRegistry registry) {

        registry.addMapping("/**").allowedOrigins("*").allowedMethods("GET", "POST", "PUT", "DELETE")
                .allowCredentials(false);
    }
}