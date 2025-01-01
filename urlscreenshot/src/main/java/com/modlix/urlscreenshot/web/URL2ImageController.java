package com.modlix.urlscreenshot.web;

import java.io.IOException;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.modlix.urlscreenshot.service.URL2ImageService;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

@RestController
@RequestMapping("/url2image")
public class URL2ImageController {

    public static final Logger logger = LoggerFactory.getLogger(URL2ImageController.class);

    private final URL2ImageService url2ImageService;

    public URL2ImageController(URL2ImageService url2ImageService) {
        this.url2ImageService = url2ImageService;
    }

    @GetMapping("/**")
    public void get(HttpServletRequest request, HttpServletResponse response) {

        try {
            this.url2ImageService.get("url2image", request, response);
        } catch (Exception e) {
            logger.error("Error while processing request", e);
            response.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
            try {
                e.printStackTrace(response.getWriter());
            } catch (IOException e1) {
                e1.printStackTrace();
            }
        }
    }

}
