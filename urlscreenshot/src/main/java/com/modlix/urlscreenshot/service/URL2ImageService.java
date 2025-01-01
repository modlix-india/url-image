package com.modlix.urlscreenshot.service;

import java.io.File;
import java.io.IOException;
import java.io.OutputStream;
import java.time.Duration;
import java.util.Set;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import org.openqa.selenium.Dimension;
import org.openqa.selenium.JavascriptExecutor;
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

import com.modlix.urlscreenshot.URL2ImageValidator;
import com.modlix.urlscreenshot.dto.URLImage;
import com.modlix.urlscreenshot.dto.URLImageParameters;
import com.modlix.urlscreenshot.exception.URL2ImageException;

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

    private final ImageService imageService;

    public URL2ImageService(ImageService imageService) {
        this.imageService = imageService;
    }

    @PostConstruct
    public void initialize() {
        if (allowedDomains == null || allowedDomains.isBlank())
            allowedDomainsList = Set.of();
        else
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

    @Cacheable(value = "urlImage", key = "#eTag")
    public URLImage getURLImage(String url, URLImageParameters params, String eTag) {

        ChromeOptions options = new ChromeOptions();
        options.addArguments("--headless", "--disable-gpu");

        WebDriver driver = new ChromeDriver(options);
        File sc = null;

        try {
            // Set Device dimensions to get the screenshot of the size given device
            // dimension.
            options.addArguments("--window-size=" + params.getDeviceWidth() + "," + params.getDeviceHeight());

            JavascriptExecutor js = (JavascriptExecutor) driver;

            Long viewportWidth = (Long) js.executeScript("return window.innerWidth;");
            Long viewportHeight = (Long) js.executeScript("return window.innerHeight;");

            int outerWidth = driver.manage().window().getSize().getWidth();
            int outerHeight = driver.manage().window().getSize().getHeight();

            int chromeWidth = outerWidth - viewportWidth.intValue();
            int chromeHeight = outerHeight - viewportHeight.intValue();

            // Set the new outer dimensions to achieve exact viewport size
            int targetWidth = params.getDeviceWidth() + chromeWidth;
            int targetHeight = params.getDeviceHeight() + chromeHeight;
            driver.manage().window().setSize(new Dimension(targetWidth, targetHeight));

            driver.get(url);

            if (params.getWaitTime() > 0l)
                Thread.sleep(Duration.ofSeconds(params.getWaitTime()).toMillis());

            sc = ((TakesScreenshot) driver).getScreenshotAs(OutputType.FILE);

        } catch (InterruptedException ex) {
            Thread.currentThread().interrupt();
            logger.error("Thread was interrupted while taking screenshot of URL: {}", url);
            throw new URL2ImageException("Thread was interrupted while taking screenshot of URL: " + url, ex);
        } catch (Exception ex) {
            logger.error("Unable to take screenshot of URL: {}", url);
            throw new URL2ImageException("Unable to take screenshot of URL: " + url, ex);
        } finally {
            driver.quit();
        }

        return new URLImage(adjustImageSize(sc, params), url, params, System.currentTimeMillis());
    }

    private byte[] adjustImageSize(File sc, URLImageParameters params) {
        try {
            return imageService.resizeImage(sc, params.getImageType(), params.getImageWidth(), params.getImageHeight(),
                    params.getImageBandColor());
        } catch (Exception ex) {
            logger.error("Unable to resize image: {}", sc.getAbsolutePath());
            throw new URL2ImageException("Unable to resize image: " + sc.getAbsolutePath(), ex);
        }
    }
}