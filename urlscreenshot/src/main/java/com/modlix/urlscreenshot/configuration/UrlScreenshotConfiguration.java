package com.modlix.urlscreenshot.configuration;

import javax.cache.CacheManager;
import javax.cache.Caching;
import javax.cache.spi.CachingProvider;

import org.ehcache.config.builders.CacheConfigurationBuilder;
import org.ehcache.config.builders.ExpiryPolicyBuilder;
import org.ehcache.config.builders.ResourcePoolsBuilder;
import org.ehcache.config.units.MemoryUnit;
import org.ehcache.jsr107.Eh107Configuration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import com.modlix.urlscreenshot.dto.URLImage;

@Configuration
public class UrlScreenshotConfiguration {
    @Bean
    public CacheManager ehCacheManager() {
        CachingProvider provider = Caching.getCachingProvider();
        CacheManager cacheManager = provider.getCacheManager();

        CacheConfigurationBuilder<String, URLImage> configuration = CacheConfigurationBuilder
                .newCacheConfigurationBuilder(
                        String.class,
                        URLImage.class,
                        ResourcePoolsBuilder
                                .newResourcePoolsBuilder()
                                .heap(40, MemoryUnit.MB)
                                .offheap(1, MemoryUnit.GB))
                .withDefaultDiskStoreThreadPool()
                .withExpiry(ExpiryPolicyBuilder.noExpiration());

        javax.cache.configuration.Configuration<String, URLImage> urlImageCacheConfiguration = Eh107Configuration
                .fromEhcacheCacheConfiguration(configuration);

        cacheManager.createCache("url2image", urlImageCacheConfiguration);
        return cacheManager;

    }
}