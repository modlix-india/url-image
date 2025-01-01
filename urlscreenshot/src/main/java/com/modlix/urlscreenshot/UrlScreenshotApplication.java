package com.modlix.urlscreenshot;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.AutoConfiguration;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.context.annotation.EnableAspectJAutoProxy;

@AutoConfiguration
@EnableCaching
@SpringBootApplication
@EnableAspectJAutoProxy(proxyTargetClass = true, exposeProxy = true)
public class UrlScreenshotApplication {

	public static void main(String[] args) {
		SpringApplication.run(UrlScreenshotApplication.class, args);
	}

}
