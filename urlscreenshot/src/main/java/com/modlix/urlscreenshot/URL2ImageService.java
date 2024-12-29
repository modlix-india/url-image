package com.modlix.urlscreenshot;

import java.io.IOException;
import java.io.OutputStream;
import java.util.Set;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import org.openqa.selenium.OutputType;
import org.openqa.selenium.TakesScreenshot;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import com.modlix.urlscreenshot.dto.URLImage;
import com.modlix.urlscreenshot.dto.URLImageParameters;

import jakarta.annotation.PostConstruct;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

@Service
public class URL2ImageService {

    public static final Logger logger = LoggerFactory.getLogger(URL2ImageService.class);

    @Value("${allowed.domains:}")
    private String allowedDomains;

    @Value("${chromedriver:/usr/bin/chromedriver}")
    private String chromeDriver;

    private Set<String> allowedDomainsList;

    @PostConstruct
    public void initialize() {
        allowedDomainsList = Stream.of(allowedDomains.split(",")).collect(Collectors.toSet());
        System.setProperty("webdriver.chrome.driver", chromeDriver);
    }

    public void get(String urlKey, HttpServletRequest request, HttpServletResponse response) {

        URL2ImageValidator.validateReferrer(allowedDomainsList, request);

        String url = URL2ImageValidator.validateAndGetURL(request, urlKey);

        URLImageParameters params = URLImageParameters.of(request);

        String eTag = url.hashCode() + "-" + params.hashCode();

        String ifNoneMatch = request.getHeader("If-None-Match");

        URLImage urlImage = getURLImage(url, params, eTag);

        if (ifNoneMatch != null && ifNoneMatch.startsWith(eTag) && ifNoneMatch.endsWith(urlImage.getTimestamp() + "")) {
            response.setStatus(HttpServletResponse.SC_NOT_MODIFIED);
            return;
        }

        if (params.getCacheControl().contains("must-revalidate"))
            response.setHeader("ETag", eTag + "-" + urlImage.getTimestamp());

        response.setHeader("Cache-Control", params.getCacheControl());
        response.setHeader("Content-Type", params.getImageType().getContentType());
        response.setHeader("X-Cache", (System.currentTimeMillis() - urlImage.getTimestamp()) < 300 ? "MISS" : "HIT");

        try (OutputStream out = response.getOutputStream()) {
            out.write(urlImage.getData());
        } catch (IOException ex) {
            logger.error("Unable to write image to response : {} with parameters {}", url, params);
            throw new URL2ImageException("Unable to write image to response : ", ex);
        }
    }

    @Cacheable(value = "url2image", key = "#eTag")
    public URLImage getURLImage(String url, URLImageParameters params, String eTag) {

        ChromeOptions options = new ChromeOptions();
        options.addArguments("--headless");
        options.addArguments("window-size=" + params.getDeviceWidth() + "," + params.getDeviceHeight());

        WebDriver driver = new ChromeDriver(options);

        byte[] data = ((TakesScreenshot) driver).getScreenshotAs(OutputType.BYTES);

        return new URLImage(data, url, params, System.currentTimeMillis());
    }

}
