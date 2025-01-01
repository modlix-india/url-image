package com.modlix.urlscreenshot;

import java.net.MalformedURLException;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.URL;
import java.util.Set;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.modlix.urlscreenshot.exception.URL2ImageException;

import jakarta.servlet.http.HttpServletRequest;

public class URL2ImageValidator {

    public static final Logger logger = LoggerFactory.getLogger(URL2ImageValidator.class);

    public static void validateReferrer(Set<String> allowedDomainsList, HttpServletRequest request) {
        if (!allowedDomainsList.isEmpty()) {
            String referer = request.getHeader("Referer");
            if (referer == null) {
                throw new URL2ImageException("Referer header is missing");
            }

            URL refererURL;
            try {
                refererURL = new URI(referer).toURL();
            } catch (MalformedURLException | URISyntaxException e) {
                logger.error("Unable to parse referer URL: {}", referer);
                throw new URL2ImageException("Invalid referer URL: " + referer, e);
            }

            if (!allowedDomainsList.contains(refererURL.getHost())) {
                throw new URL2ImageException("Referer domain is not allowed: " + refererURL.getHost());
            }
        }
    }

    public static String validateAndGetURL(HttpServletRequest request, String key) {
        String url = request.getRequestURI().trim();

        if (url == null || url.isBlank()) {
            logger.error("URL is missing");
            throw new URL2ImageException("URL is missing");
        }

        if (key != null && !key.isBlank()) {
            int index = url.indexOf(key);
            if (index == -1) {
                logger.error("Key is missing in URL: {}", key);
                throw new URL2ImageException("Key is missing in URL: " + key);
            }
            url = url.substring(index + key.length()).trim();
        }

        url = url.replace("//", "/");

        if (url.startsWith("/"))
            url = url.substring(1);

        if (url.startsWith("https/"))
            url = "https://" + url.substring(6);
        else if (url.startsWith("http/"))
            url = "http://" + url.substring(5);
        else
            url = "https://" + url;

        try {
            new URI(url).toURL();
        } catch (MalformedURLException | URISyntaxException e) {
            logger.error("Invalid URL: {}", url);
            throw new URL2ImageException("Invalid URL: " + url, e);
        }

        return url;
    }

    private URL2ImageValidator() {
    }
}
