package com.modlix.urlscreenshot;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

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

        this.url2ImageService.get("url2image", request, response);
    }

}
